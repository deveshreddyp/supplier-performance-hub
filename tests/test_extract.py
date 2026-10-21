from src.extract import SCHEMA,regex_extract
from jsonschema import validate
def test_regex_extraction_schema():
    text="Supplier: Example Supplier\nContract Value: USD 120,000.00\nStart Date: 2025-01-01\nEnd Date: 2026-01-01\nRenewal Notice: 30 days\nUptime: minimum 99.9%\nResponse Time: maximum 4 hours\nTicket Resolution: minimum 95%\nService credits: 5% monthly fees."
    result=regex_extract(text); validate(result,SCHEMA)
    assert result["supplier"]=="Example Supplier" and len(result["SLAs"])==3
