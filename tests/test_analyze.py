import src.db as db
import src.extract as extractor
import src.generate_data as generator
from src.analyze import analyze


def test_breach_logic_detects_breaches(tmp_path, monkeypatch):
    # Build all required inputs in an isolated temporary directory so the
    # test passes on a clean clone without pre-generated data or a local DB.
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    monkeypatch.setattr(extractor, "ROOT", tmp_path)
    monkeypatch.setattr(db, "ROOT", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "data" / "supplier_hub_test.db")

    generator.generate()
    extractor.extract_all()
    db.load_all()

    data = analyze()
    breaches = data["breaches"]

    assert not breaches.empty
    assert {"supplier", "month", "metric", "target", "actual", "estimated_credit"}.issubset(
        breaches.columns
    )
    uptime = breaches[breaches.metric == "Uptime"]
    assert not uptime.empty
    assert (uptime.actual < uptime.target).all()
