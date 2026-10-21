"""Extract contract details with Gemini or a regex fallback."""
from pathlib import Path
from datetime import date
import json,logging,os,re
import pdfplumber
from jsonschema import validate as validate_schema
logging.basicConfig(level=logging.INFO); log=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[1]
SCHEMA={"type":"object","required":["supplier","contract_value","currency","start_date","end_date","renewal_notice_days","SLAs","service_credit_terms"],"properties":{"supplier":{"type":"string"},"contract_value":{"type":"number","minimum":0},"currency":{"type":"string"},"start_date":{"type":"string"},"end_date":{"type":"string"},"renewal_notice_days":{"type":"integer","minimum":0},"SLAs":{"type":"array","items":{"type":"object","required":["metric","target","unit"],"properties":{"metric":{"type":"string"},"target":{"type":"number"},"unit":{"type":"string"}}}},"service_credit_terms":{"type":"string"}},"additionalProperties":False}
def read_pdf(path):
    with pdfplumber.open(path) as pdf: return "\n".join(p.extract_text() or "" for p in pdf.pages)
def regex_extract(text):
    def grab(pattern,default=""):
        m=re.search(pattern,text,re.I|re.M); return m.group(1).strip() if m else default
    name=grab(r"Supplier:\s*(.+)","Unknown Supplier"); value=grab(r"Contract Value:\s*[A-Z]{3}\s*([\d,.]+)","0").replace(",","")
    start=grab(r"Start Date:\s*(\d{4}-\d{2}-\d{2})",date.today().isoformat()); end=grab(r"End Date:\s*(\d{4}-\d{2}-\d{2})",date.today().isoformat())
    notice=int(grab(r"Renewal Notice:\s*(\d+)\s*days","60")); slas=[]
    for metric,pattern,unit in [("Uptime",r"Uptime:\s*minimum\s*([\d.]+)%","%"),("Response Time",r"Response Time:\s*maximum\s*([\d.]+)\s*hours","hours"),("Ticket Resolution",r"Ticket Resolution:\s*minimum\s*([\d.]+)%","%")]:
        m=re.search(pattern,text,re.I)
        if m: slas.append({"metric":metric,"target":float(m.group(1)),"unit":unit})
    return {"supplier":name,"contract_value":float(value),"currency":grab(r"Contract Value:\s*([A-Z]{3})","USD"),"start_date":start,"end_date":end,"renewal_notice_days":notice,"SLAs":slas,"service_credit_terms":grab(r"Service credits:\s*(.+)","No service credit terms found.")}
def gemini_extract(text):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    prompt="Extract supplier contract fields. Return ONLY strict JSON matching this schema exactly: "+json.dumps(SCHEMA)+"\nDo not infer missing values. Contract text:\n"+text
    response=genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    raw=re.sub(r"^```(?:json)?\s*|\s*```$","",response.text.strip(),flags=re.I)
    result=json.loads(raw); validate_schema(result,SCHEMA); return result
def extract_file(path):
    text=read_pdf(path)
    if os.getenv("GEMINI_API_KEY"):
        try:
            result=gemini_extract(text); result["source_pdf"]=str(path); result["extraction_method"]="gemini"; return result
        except Exception as exc: log.warning("Gemini extraction failed for %s; using regex: %s",path,exc)
    result=regex_extract(text); validate_schema(result,SCHEMA); result["source_pdf"]=str(path); result["extraction_method"]="regex"; return result
def extract_all():
    results=[]
    for path in sorted((ROOT/"data/contracts").glob("*.pdf")):
        try: results.append(extract_file(path))
        except Exception: log.exception("Could not extract %s",path)
    out=ROOT/"data/extracted_contracts.json"; out.write_text(json.dumps(results,indent=2)); log.info("Wrote %d contracts",len(results)); return results
if __name__=="__main__": extract_all()
