"""Validate source data and persist issues to SQLite."""
import pandas as pd
from src.db import connect,init_db,ROOT
def validate_data():
    init_db(); issues=[]; seed=pd.read_csv(ROOT/"data/suppliers_seed.csv"); perf=pd.read_csv(ROOT/"data/performance.csv")
    def add(table,key,msg,severity="warning"): issues.append((severity,table,str(key),msg))
    for r in seed.to_dict("records"):
        for f in ("supplier","contract_value","start_date","end_date"):
            if pd.isna(r.get(f)) or str(r.get(f)).strip()=="": add("suppliers",r.get("supplier","?"),f"Missing required field: {f}","error")
        try:
            if pd.to_datetime(r["end_date"])<pd.to_datetime(r["start_date"]): add("contracts",r["supplier"],"End date precedes start date","error")
        except Exception: add("contracts",r.get("supplier","?"),"Invalid contract date","error")
        if float(r.get("contract_value",0))<0: add("contracts",r["supplier"],"Negative contract value","error")
    if seed.supplier.duplicated().any():
        for name in seed.loc[seed.supplier.duplicated(False),"supplier"]: add("suppliers",name,"Duplicate supplier")
    if perf.duplicated(["supplier","month"]).any(): add("performance","multiple","Duplicate supplier/month records","error")
    for r in perf.to_dict("records"):
        if not 0<=float(r["uptime_pct"])<=100: add("performance",f'{r["supplier"]}:{r["month"]}',"Uptime outside 0–100","error")
        for f in ("response_time_hours","tickets_total"):
            if float(r[f])<0: add("performance",f'{r["supplier"]}:{r["month"]}',f"Negative {f}","error")
    with connect() as c:
        c.execute("DELETE FROM validation_report"); c.executemany("INSERT INTO validation_report(severity,table_name,record_key,issue) VALUES (?,?,?,?)",issues)
    return pd.DataFrame(issues,columns=["severity","table_name","record_key","issue"])
if __name__=="__main__":
    result=validate_data(); print(result.to_string(index=False) if len(result) else "No validation issues found.")
