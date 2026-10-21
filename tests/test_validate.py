from src.generate_data import generate
from src.extract import extract_all
from src.db import load_all
from src.validate import validate_data
def test_generated_data_validates_cleanly():
    generate(); extract_all(); load_all(); issues=validate_data()
    assert list(issues.columns)==["severity","table_name","record_key","issue"]
    assert not (not issues.empty and (issues.severity=="error").any())
