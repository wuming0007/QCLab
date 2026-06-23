"""Minimal tests for L6 / CO Rabi analyzer."""

from qxtrl.co import analyze_rabi


def test_analyze_rabi_recovers_pi_amp():
    # Simulated data around hidden ~0.175
    fake_result = {
        "result": [
            {"amp": 0.0, "i": 0.98, "q": 0.01},
            {"amp": 0.05, "i": 0.65, "q": 0.02},
            {"amp": 0.10, "i": 0.05, "q": 0.01},
            {"amp": 0.15, "i": -0.55, "q": -0.01},
            {"amp": 0.20, "i": -0.92, "q": 0.0},
        ],
        "backend": "test",
    }
    out = analyze_rabi(fake_result)
    m = out["metrics"]
    assert "pi_amp" in m
    # Should be near 0.17x for this curve shape
    assert 0.14 < m["pi_amp"] < 0.22
    assert m["fit_quality"] > 0.7
    assert "proposal" in out
    assert out["proposal"]["value"] == m["pi_amp"]
