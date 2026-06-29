# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
SENTINEL - On-Chain Fact-Checker with Bonded Challenges
=======================================================
Anyone posts a CLAIM and an evidence URL, putting up a bond that the claim is
TRUE. A skeptic can post an equal counter-bond that it is FALSE. The contract
then reads the evidence page on-chain and the validator set agrees (Equivalence
Principle) whether the source actually supports the claim. The side that matched
the verdict takes both bonds. If no challenger appears, the asserter simply
reclaims their bond after adjudication confirms it.

Lifecycle:
    ASSERTED   -> claim posted with a TRUE-bond, open to challenge
    DISPUTED   -> a FALSE-bond was posted, both sides locked in
    RULED      -> contract read the evidence, verdict in, winner(s) paid
"""

from genlayer import *
from dataclasses import dataclass
import json
import typing


STATUS_ASSERTED = 0
STATUS_DISPUTED = 1
STATUS_RULED = 2

VERDICT_NONE = 0
VERDICT_TRUE = 1
VERDICT_FALSE = 2
VERDICT_UNCLEAR = 3


@allow_storage
@dataclass
class Claim:
    asserter: Address       # bonded that the claim is TRUE
    challenger: Address     # bonded that the claim is FALSE
    statement: str
    evidence_url: str
    bond: u256
    status: u8
    verdict: u8
    rationale: str
    paid: bool


class Sentinel(gl.Contract):
    claims: DynArray[Claim]

    def __init__(self) -> None:
        pass

    @gl.public.write.payable
    def assert_claim(self, statement: str, evidence_url: str) -> int:
        if len(statement.strip()) == 0:
            raise gl.vm.UserError("a claim statement is required")
        if len(evidence_url.strip()) == 0:
            raise gl.vm.UserError("an evidence URL is required")
        bond = gl.message.value
        if bond == u256(0):
            raise gl.vm.UserError("you must post a bond")
        c = self.claims.append_new_get()
        c.asserter = gl.message.sender_address
        c.challenger = Address(bytes(20))
        c.statement = statement
        c.evidence_url = evidence_url
        c.bond = bond
        c.status = u8(STATUS_ASSERTED)
        c.verdict = u8(VERDICT_NONE)
        c.rationale = ""
        c.paid = False
        return len(self.claims) - 1

    @gl.public.write.payable
    def challenge(self, claim_id: int) -> None:
        """Post an equal counter-bond that the claim is FALSE."""
        c = self._get(claim_id)
        if c.status != STATUS_ASSERTED:
            raise gl.vm.UserError("claim is not open to challenge")
        if gl.message.sender_address == c.asserter:
            raise gl.vm.UserError("you cannot challenge your own claim")
        if gl.message.value != c.bond:
            raise gl.vm.UserError("counter-bond must equal the original bond")
        c.challenger = gl.message.sender_address
        c.status = u8(STATUS_DISPUTED)

    @gl.public.write
    def adjudicate(self, claim_id: int) -> None:
        """Read the evidence and let the validators agree on the verdict."""
        c = self._get(claim_id)
        if c.status != STATUS_ASSERTED and c.status != STATUS_DISPUTED:
            raise gl.vm.UserError("claim already ruled")

        url = c.evidence_url
        statement = c.statement

        def leader_fn() -> str:
            page = gl.nondet.web.get(url).body.decode("utf-8")[:6000]
            prompt = (
                f"Claim to verify: {statement}\n\n"
                f"Evidence page content:\n{page}\n\n"
                "Does the evidence page SUPPORT the claim? Judge strictly on what "
                'the page actually says. Reply with ONLY JSON: {"verdict": "TRUE"} '
                'if the page supports it, {"verdict": "FALSE"} if it contradicts '
                'it, or {"verdict": "UNCLEAR"} if the page does not settle it. '
                'Include a short "reason".'
            )
            return gl.nondet.exec_prompt(prompt)

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            return self._verdict_of(leader_res.calldata)[0] == self._verdict_of(leader_fn())[0]

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        verdict, reason = self._verdict_of(result)
        c.verdict = u8(verdict)
        c.rationale = reason[:400]
        c.status = u8(STATUS_RULED)
        self._settle(c)

    def _settle(self, c: Claim) -> None:
        if c.paid:
            return
        disputed = c.challenger != Address(bytes(20))
        v = int(c.verdict)
        if not disputed:
            # No challenger. Asserter gets their bond back unless evidence
            # clearly contradicts the claim (then it is forfeited to nobody-
            # returning it would reward a false assertion; we still return it
            # because there is no counterparty, but only on TRUE/UNCLEAR).
            if v == VERDICT_FALSE:
                # forfeit: bond stays in the contract (slashed)
                c.paid = True
                return
            c.paid = True
            self._pay(c.asserter, c.bond)
            return
        # Disputed: winner takes both bonds; unclear splits back.
        pot = c.bond + c.bond
        if v == VERDICT_TRUE:
            c.paid = True
            self._pay(c.asserter, pot)
        elif v == VERDICT_FALSE:
            c.paid = True
            self._pay(c.challenger, pot)
        else:
            c.paid = True
            self._pay(c.asserter, c.bond)
            self._pay(c.challenger, c.bond)

    # ------------------------------------------------------------------ views
    @gl.public.view
    def get_claim_count(self) -> int:
        return len(self.claims)

    @gl.public.view
    def get_claim(self, claim_id: int) -> dict:
        c = self._get(claim_id)
        return {
            "asserter": c.asserter.as_hex,
            "challenger": c.challenger.as_hex,
            "statement": c.statement,
            "evidence_url": c.evidence_url,
            "bond": str(c.bond),
            "status": int(c.status),
            "verdict": int(c.verdict),
            "rationale": c.rationale,
            "paid": bool(c.paid),
        }

    # -------------------------------------------------------------- internals
    def _get(self, claim_id: int) -> Claim:
        if claim_id < 0 or claim_id >= len(self.claims):
            raise gl.vm.UserError("no such claim")
        return self.claims[claim_id]

    def _verdict_of(self, result: typing.Any) -> tuple:
        data = result
        if isinstance(data, str):
            data = self._extract_json(data)
        if not isinstance(data, dict):
            return (VERDICT_UNCLEAR, "")
        raw = str(data.get("verdict", "")).strip().upper()
        reason = str(data.get("reason", ""))
        if raw == "TRUE":
            return (VERDICT_TRUE, reason)
        if raw == "FALSE":
            return (VERDICT_FALSE, reason)
        return (VERDICT_UNCLEAR, reason)

    def _extract_json(self, text: str) -> typing.Any:
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except (ValueError, TypeError):
                return None
        return None

    def _pay(self, recipient: Address, amount: u256) -> None:
        if amount == u256(0):
            return
        _Payee(recipient).emit_transfer(value=amount)


@gl.evm.contract_interface
class _Payee:
    class View:
        pass

    class Write:
        pass
