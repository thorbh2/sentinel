from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "contracts" / "sentinel_v2.py").read_text(encoding="utf-8")


def test_standard_and_case_evidence_are_permissioned():
    assert "def _require_admin(" in SOURCE
    assert "def _require_case_editor(" in SOURCE
    assert "only_case_owner_or_admin" in SOURCE


def test_counter_bonds_close_before_review():
    assert "def close_staking(" in SOURCE
    assert "staking_must_close_before_review" in SOURCE
    assert "case_not_mature" in SOURCE


def test_open_reviews_block_settlement_and_payout():
    assert "open_dispute_blocks_settlement" in SOURCE
    assert 'a["payoutState"] = "claimable"' in SOURCE
    assert 'a.get("payoutState") == "paid"' in SOURCE


def test_unclear_verdict_is_a_neutral_refund():
    assert "Neutral refund: unclear verdict" in SOURCE
    assert "owed += amt if refund_mode" in SOURCE


def test_accepted_reviews_change_the_final_verdict():
    assert 'self._revise_outcome(a, res["ruling"] == "accepted")' in SOURCE
    assert 'self._revise_outcome(a, res["ruling"] == "granted")' in SOURCE
