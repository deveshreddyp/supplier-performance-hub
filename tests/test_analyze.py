import src.db as db
from src.analyze import analyze


def test_breach_logic_detects_breaches(tmp_path, monkeypatch):
    # Give this test its own database so it does not depend on test order
    # or on a previously initialized local SQLite database.
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "supplier_hub_test.db")
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
