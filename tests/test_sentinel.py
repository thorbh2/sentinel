"""
Tests for SENTINEL (direct runner). Web + LLM verdict mocked.

Run with:  python -m pytest -v
"""

import json
from pathlib import Path

CONTRACT = str(Path(__file__).resolve().parents[1] / "contracts" / "sentinel.py")

GEN = 10 ** 18
ASSERTED, DISPUTED, RULED = 0, 1, 2
V_NONE, V_TRUE, V_FALSE, V_UNCLEAR = 0, 1, 2, 3

URL = "https://example.com/evidence"
CLAIM = "The Eiffel Tower is in Paris."


def _assert(c, vm, who, bond=2 * GEN, statement=CLAIM, url=URL):
    vm.sender = who
    vm.value = bond
    cid = c.assert_claim(statement, url)
    vm.value = 0
    return cid


def _challenge(c, vm, who, cid, bond=2 * GEN):
    vm.sender = who
    vm.value = bond
    c.challenge(cid)
    vm.value = 0


# ----------------------------------------------------------------- assert
def test_assert_posts_bond(deploy, direct_vm, direct_alice):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice, bond=2 * GEN)
    assert cid == 0
    cl = c.get_claim(0)
    assert cl["status"] == ASSERTED
    assert cl["bond"] == str(2 * GEN)


def test_assert_requires_bond(deploy, direct_vm, direct_alice):
    c = deploy(CONTRACT)
    direct_vm.sender = direct_alice
    direct_vm.value = 0
    with direct_vm.expect_revert("bond"):
        c.assert_claim(CLAIM, URL)


def test_assert_requires_url(deploy, direct_vm, direct_alice):
    c = deploy(CONTRACT)
    direct_vm.sender = direct_alice
    direct_vm.value = GEN
    with direct_vm.expect_revert("evidence URL"):
        c.assert_claim(CLAIM, "  ")
    direct_vm.value = 0


# ----------------------------------------------------------------- challenge
def test_challenge_disputes(deploy, direct_vm, direct_alice, direct_bob):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice)
    _challenge(c, direct_vm, direct_bob, cid)
    assert c.get_claim(0)["status"] == DISPUTED


def test_cannot_challenge_own(deploy, direct_vm, direct_alice):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice, bond=2 * GEN)
    direct_vm.sender = direct_alice
    direct_vm.value = 2 * GEN
    with direct_vm.expect_revert("your own claim"):
        c.challenge(cid)
    direct_vm.value = 0


def test_challenge_must_match_bond(deploy, direct_vm, direct_alice, direct_bob):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice, bond=2 * GEN)
    direct_vm.sender = direct_bob
    direct_vm.value = GEN
    with direct_vm.expect_revert("counter-bond must equal"):
        c.challenge(cid)
    direct_vm.value = 0


# ----------------------------------------------------------------- adjudicate (mocked)
def test_adjudicate_true_undisputed_returns_bond(deploy, direct_vm, direct_alice):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice)
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "The Eiffel Tower stands in Paris, France."})
    direct_vm.mock_llm(r"SUPPORT the claim", json.dumps({"verdict": "TRUE", "reason": "page confirms"}))
    direct_vm.sender = direct_alice
    c.adjudicate(cid)
    cl = c.get_claim(0)
    assert cl["status"] == RULED
    assert cl["verdict"] == V_TRUE
    assert cl["paid"] is True


def test_adjudicate_true_disputed_pays_asserter(deploy, direct_vm, direct_alice, direct_bob):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice)
    _challenge(c, direct_vm, direct_bob, cid)
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Eiffel Tower, Paris."})
    direct_vm.mock_llm(r"SUPPORT the claim", json.dumps({"verdict": "TRUE", "reason": "supported"}))
    c.adjudicate(cid)
    cl = c.get_claim(0)
    assert cl["verdict"] == V_TRUE
    assert cl["paid"] is True


def test_adjudicate_false_disputed_pays_challenger(deploy, direct_vm, direct_alice, direct_bob):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice, statement="The moon is made of cheese.")
    _challenge(c, direct_vm, direct_bob, cid)
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "The moon is composed of rock and dust."})
    direct_vm.mock_llm(r"SUPPORT the claim", json.dumps({"verdict": "FALSE", "reason": "contradicted"}))
    c.adjudicate(cid)
    cl = c.get_claim(0)
    assert cl["verdict"] == V_FALSE
    assert cl["paid"] is True


def test_adjudicate_unclear_splits(deploy, direct_vm, direct_alice, direct_bob):
    c = deploy(CONTRACT)
    cid = _assert(c, direct_vm, direct_alice)
    _challenge(c, direct_vm, direct_bob, cid)
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Unrelated content."})
    direct_vm.mock_llm(r"SUPPORT the claim", json.dumps({"verdict": "UNCLEAR", "reason": "page silent"}))
    c.adjudicate(cid)
    assert c.get_claim(0)["verdict"] == V_UNCLEAR


def test_unknown_claim_reverts(deploy, direct_vm):
    c = deploy(CONTRACT)
    with direct_vm.expect_revert("no such claim"):
        c.get_claim(0)
