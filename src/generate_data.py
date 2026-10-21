"""Generate fully synthetic supplier contracts and monthly performance records."""
from pathlib import Path
from datetime import date
import random
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT=Path(__file__).resolve().parents[1]
NAMES=["Northstar Cloud","BluePeak Logistics","Vertex Support","Cedar Analytics","Orbit Telecom","Summit Security","Brightline Hosting","Pioneer Facilities"]

def generate():
    random.seed(42)
    (ROOT/"data/contracts").mkdir(parents=True,exist_ok=True)
    today=date.today(); rows=[]
    for i,name in enumerate(NAMES):
        start=date(today.year-1,(i*2)%12+1,min(25,1+i*3))
        month=today.month+(i%5)+1
        end=date(today.year,month,min(25,2+i*2)) if month<=12 else date(today.year+1,(month-1)%12+1,min(25,2+i*2))
        value=[120000,85000,240000,67500,180000,95000,310000,74000][i]
        uptime=[99.9,99.5,99.7,99.8,99.5,99.9,99.95,99.5][i]; response=[2,4,3,2,5,1,2,4][i]
        clauses=f"""SYNTHETIC SUPPLIER AGREEMENT
Supplier: {name}
Contract Value: USD {value:,.2f}
Start Date: {start.isoformat()}
End Date: {end.isoformat()}
Renewal Notice: 60 days
Service Level Agreements (SLAs):
- Uptime: minimum {uptime}%
- Response Time: maximum {response} hours
- Ticket Resolution: minimum 95%
Service credits: For each monthly uptime shortfall below target, credit 5% of monthly fees; maximum service credit 15% of monthly fees. All terms are synthetic and illustrative only.
"""
        pdf=ROOT/"data/contracts"/f"supplier_{i+1:02d}.pdf"; c=canvas.Canvas(str(pdf),pagesize=letter); t=c.beginText(55,740); t.setFont("Helvetica",11)
        for line in clauses.splitlines(): t.textLine(line)
        c.drawText(t); c.save()
        rows.append({"supplier":name,"supplier_id":f"SUP-{i+1:03d}","contract_value":value,"currency":"USD","start_date":start.isoformat(),"end_date":end.isoformat(),"renewal_notice_days":60,"contract_pdf":str(pdf.relative_to(ROOT))})
    pd.DataFrame(rows).to_csv(ROOT/"data/suppliers_seed.csv",index=False)
    perf=[]; periods=pd.date_range(end=pd.Timestamp.today().normalize().replace(day=1),periods=12,freq="MS")
    ut=[99.9,99.5,99.7,99.8,99.5,99.9,99.95,99.5]; rt=[2,4,3,2,5,1,2,4]
    for i,s in enumerate(rows):
        for j,p in enumerate(periods):
            u=ut[i]+random.uniform(-.18,.08); r=max(.5,rt[i]+random.uniform(-1,1.8)); resolution=random.uniform(92,99.8)
            if (i+j)%7==0: u-=.35
            if (i*2+j)%9==0: r+=2.5
            perf.append({"supplier":s["supplier"],"month":p.strftime("%Y-%m-%d"),"uptime_pct":round(max(95,min(100,u)),3),"response_time_hours":round(r,2),"ticket_resolution_pct":round(resolution,2),"tickets_total":random.randint(80,500)})
    pd.DataFrame(perf).to_csv(ROOT/"data/performance.csv",index=False)
    print(f"Generated {len(rows)} synthetic contracts and {len(perf)} performance records.")
if __name__=="__main__": generate()
