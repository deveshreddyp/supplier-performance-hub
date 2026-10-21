"""SLA breach analysis, supplier health scores, and renewal alerts."""
import pandas as pd
from src.db import connect,frame
def analyze():
    perf=frame("SELECT * FROM performance ORDER BY month"); slas=frame("SELECT * FROM slas"); contracts=frame("SELECT * FROM contracts")
    if perf.empty or slas.empty: return {"scorecards":pd.DataFrame(),"breaches":pd.DataFrame(),"renewals":pd.DataFrame(),"trends":pd.DataFrame()}
    actual_map={"Uptime":"uptime_pct","Response Time":"response_time_hours","Ticket Resolution":"ticket_resolution_pct"}; unit_map={"Uptime":"%","Response Time":"hours","Ticket Resolution":"%"}
    values=contracts.set_index("supplier").contract_value.to_dict(); rows=[]
    for s in slas.to_dict("records"):
        col=actual_map.get(s["metric"])
        if not col: continue
        sub=perf[perf.supplier==s["supplier"]]; target=float(s["target"])
        bad=sub[col]<target if s["metric"] in ("Uptime","Ticket Resolution") else sub[col]>target
        for _,r in sub[bad].iterrows():
            credit=values.get(s["supplier"],0)/12*.05 if s["metric"]=="Uptime" else 0
            rows.append({"supplier":s["supplier"],"month":r["month"],"metric":s["metric"],"target":target,"actual":r[col],"unit":unit_map[s["metric"]],"estimated_credit":round(credit,2),"severity":"High" if abs(float(r[col])-target)>max(.5,target*.01) else "Medium"})
    cols=["supplier","month","metric","target","actual","unit","estimated_credit","severity"]; breaches=pd.DataFrame(rows,columns=cols)
    with connect() as c:
        c.execute("DELETE FROM breaches")
        if not breaches.empty: c.executemany("INSERT INTO breaches VALUES (?,?,?,?,?,?,?,?)",list(breaches.itertuples(index=False,name=None)))
    summaries=[]
    for name,g in perf.groupby("supplier"):
        b=breaches[breaches.supplier==name] if not breaches.empty else pd.DataFrame(); total=len(slas[slas.supplier==name])*len(g)
        score=round(max(0,min(100,100-len(b)/max(1,total)*100)),1); status="Green" if score>=95 else "Amber" if score>=85 else "Red"
        summaries.append({"supplier":name,"health_score":score,"status":status,"breach_count":len(b),"contract_value":values.get(name,0)})
    scorecards=pd.DataFrame(summaries).sort_values(["health_score","supplier"])
    today=pd.Timestamp.today().normalize(); renewals=contracts.copy(); renewals["end_date"]=pd.to_datetime(renewals.end_date,errors="coerce"); renewals["days_remaining"]=(renewals.end_date-today).dt.days
    renewals=renewals[(renewals.days_remaining>=0)&(renewals.days_remaining<=90)].sort_values("days_remaining")
    return {"scorecards":scorecards,"breaches":breaches,"renewals":renewals,"trends":perf}
