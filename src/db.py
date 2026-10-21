"""SQLite schema and loading helpers."""
from pathlib import Path
import json,sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DB_PATH=ROOT/"data/supplier_hub.db"
def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init_db():
    with connect() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS suppliers(supplier_id TEXT PRIMARY KEY,name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS contracts(supplier TEXT PRIMARY KEY,contract_value REAL,currency TEXT,start_date TEXT,end_date TEXT,renewal_notice_days INTEGER,service_credit_terms TEXT,source_pdf TEXT,extraction_method TEXT);
        CREATE TABLE IF NOT EXISTS slas(supplier TEXT,metric TEXT,target REAL,unit TEXT,UNIQUE(supplier,metric));
        CREATE TABLE IF NOT EXISTS performance(supplier TEXT,month TEXT,uptime_pct REAL,response_time_hours REAL,ticket_resolution_pct REAL,tickets_total INTEGER,UNIQUE(supplier,month));
        CREATE TABLE IF NOT EXISTS breaches(supplier TEXT,month TEXT,metric TEXT,target REAL,actual REAL,unit TEXT,estimated_credit REAL,severity TEXT,UNIQUE(supplier,month,metric));
        CREATE TABLE IF NOT EXISTS validation_report(id INTEGER PRIMARY KEY AUTOINCREMENT,severity TEXT,table_name TEXT,record_key TEXT,issue TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);""")
def load_all():
    init_db(); seed=pd.read_csv(ROOT/"data/suppliers_seed.csv"); perf=pd.read_csv(ROOT/"data/performance.csv"); contracts=json.loads((ROOT/"data/extracted_contracts.json").read_text())
    with connect() as c:
        for table in ("slas","contracts","suppliers","performance","breaches"): c.execute(f"DELETE FROM {table}")
        for _,s in seed.iterrows(): c.execute("INSERT INTO suppliers VALUES (?,?)",(s.supplier_id,s.supplier))
        for x in contracts:
            c.execute("INSERT INTO contracts VALUES (?,?,?,?,?,?,?,?,?)",(x["supplier"],x["contract_value"],x["currency"],x["start_date"],x["end_date"],x["renewal_notice_days"],x["service_credit_terms"],x.get("source_pdf",""),x.get("extraction_method","regex")))
            c.executemany("INSERT INTO slas VALUES (?,?,?,?)",[(x["supplier"],v["metric"],v["target"],v["unit"]) for v in x["SLAs"]])
        c.executemany("INSERT INTO performance VALUES (?,?,?,?,?,?)",[(r.supplier,r.month,r.uptime_pct,r.response_time_hours,r.ticket_resolution_pct,r.tickets_total) for r in perf.itertuples()])
def frame(query,params=()):
    with connect() as c: return pd.read_sql_query(query,c,params=params)
