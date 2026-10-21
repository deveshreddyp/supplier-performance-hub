"""Supplier Performance Hub synthetic-data Streamlit dashboard."""
import sys,logging
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
ROOT=Path(__file__).resolve().parent; sys.path.insert(0,str(ROOT))
from src.db import init_db,load_all,frame
from src.extract import extract_all
from src.validate import validate_data
from src.analyze import analyze
from src.report import generate_report
logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="Supplier Performance Hub",page_icon="📊",layout="wide")
st.markdown("<style>.block-container{padding-top:1.5rem}[data-testid='stMetric']{background:#f4f7fb;padding:14px;border-radius:12px}</style>",unsafe_allow_html=True)
st.title("📊 Supplier Performance Hub"); st.caption("AI-enabled contract intelligence · SLA monitoring · Renewal readiness")
st.warning("DEMO NOTICE: ALL DATA IS SYNTHETIC. Suppliers, contracts, performance records, values, and service-credit estimates are fictional.")
def ensure_data():
    if not (ROOT/"data/extracted_contracts.json").exists():
        from src.generate_data import generate
        generate(); extract_all(); load_all(); validate_data()
    elif not (ROOT/"data/supplier_hub.db").exists(): load_all(); validate_data()
ensure_data(); init_db(); data=analyze(); suppliers=frame("SELECT name FROM suppliers ORDER BY name")["name"].tolist()
with st.sidebar:
    st.header("Filters"); selected=st.multiselect("Suppliers",suppliers,default=suppliers)
    allperf=frame("SELECT * FROM performance ORDER BY month")
    min_date=pd.to_datetime(allperf.month).min().date(); max_date=pd.to_datetime(allperf.month).max().date()
    date_range=st.date_input("Performance date range",value=(min_date,max_date),min_value=min_date,max_value=max_date)
    st.caption("Gemini extraction is optional. Set GEMINI_API_KEY to enable it; regex fallback works without a key.")
if st.button("↻ Re-run contract extraction and refresh data"):
    with st.spinner("Extracting contracts and rebuilding analytics…"):
        extract_all(); load_all(); validate_data(); st.success("Data refreshed."); st.rerun()
perf=frame("SELECT * FROM performance ORDER BY month")
if len(date_range)==2: perf=perf[(pd.to_datetime(perf.month).dt.date>=date_range[0])&(pd.to_datetime(perf.month).dt.date<=date_range[1])]
perf=perf[perf.supplier.isin(selected)]
contracts=frame("SELECT * FROM contracts"); contracts=contracts[contracts.supplier.isin(selected)]
breaches=data["breaches"]
if not breaches.empty:
    breaches=breaches[breaches.supplier.isin(selected)]
    if len(date_range)==2: breaches=breaches[(pd.to_datetime(breaches.month).dt.date>=date_range[0])&(pd.to_datetime(breaches.month).dt.date<=date_range[1])]
quarter_start=pd.Timestamp.today().to_period("Q").start_time
quarter_breaches=breaches[pd.to_datetime(breaches.month)>=quarter_start] if not breaches.empty else breaches
renewals=data["renewals"]; renewals=renewals[renewals.supplier.isin(selected)]
credits=float(breaches.estimated_credit.sum()) if not breaches.empty else 0
cols=st.columns(5); cols[0].metric("Suppliers",len(selected)); cols[1].metric("Contract value",f"${contracts.contract_value.sum():,.0f}"); cols[2].metric("SLA breaches this quarter",len(quarter_breaches)); cols[3].metric("Estimated credits",f"${credits:,.0f}"); cols[4].metric("Renewing ≤90 days",len(renewals))
st.subheader("Supplier scorecards"); score=data["scorecards"]; score=score[score.supplier.isin(selected)]
def color_status(v):
    return "background-color: #fee2e2;color:#991b1b" if v=="Red" else "background-color: #fef3c7;color:#92400e" if v=="Amber" else "background-color: #dcfce7;color:#166534"
st.dataframe(score.style.map(color_status,subset=["status"]) if not score.empty else score,use_container_width=True,hide_index=True)
t1,t2,t3,t4=st.tabs(["SLA trends","Breaches & credits","Renewals","Validation issues"])
with t1:
    metric=st.selectbox("Metric",["Uptime","Response Time","Ticket Resolution"]); colmap={"Uptime":"uptime_pct","Response Time":"response_time_hours","Ticket Resolution":"ticket_resolution_pct"}
    slas=frame("SELECT * FROM slas WHERE metric=?",(metric,)); plot=perf[perf.supplier.isin(slas.supplier)]
    if not plot.empty:
        plot=plot.copy(); plot["month"]=pd.to_datetime(plot.month); plot["actual"]=plot[colmap[metric]]; targets=slas.set_index("supplier").target.to_dict(); plot["target"]=plot.supplier.map(targets)
        long=pd.concat([plot[["month","supplier","actual"]].rename(columns={"actual":"value"}).assign(series="Actual"),plot[["month","supplier","target"]].rename(columns={"target":"value"}).assign(series="SLA target")])
        st.plotly_chart(px.line(long,x="month",y="value",color="supplier",line_dash="series",markers=True,title=f"{metric}: actual vs target"),use_container_width=True)
    else: st.info("No performance data for these filters.")
with t2:
    st.metric("Estimated credits (filtered)",f"${credits:,.2f}"); st.dataframe(breaches,use_container_width=True,hide_index=True)
with t3: st.dataframe(renewals,use_container_width=True,hide_index=True)
with t4: st.dataframe(frame("SELECT severity,table_name,record_key,issue,created_at FROM validation_report ORDER BY id DESC"),use_container_width=True,hide_index=True)
report_path=generate_report()
with open(report_path,"rb") as f: st.download_button("⬇ Download Excel report",data=f,file_name="supplier_report.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("Supplier Performance Hub · ALL DATA IS SYNTHETIC · For demonstration only; not for real procurement or legal decisions.")
