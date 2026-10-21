from src.analyze import analyze
def test_breach_logic_detects_breaches():
    data=analyze(); assert not data["breaches"].empty
    assert {"supplier","month","metric","target","actual","estimated_credit"}.issubset(data["breaches"].columns)
    uptime=data["breaches"][data["breaches"].metric=="Uptime"]
    assert all(uptime.actual<uptime.target)
