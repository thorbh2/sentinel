# Sentinel

Sentinel is a GenLayer claim-sentinel protocol for assertions, source evidence, challenge markets, adjudication and appeal review.

This repository is a public proof package: it includes the product UI, the deployed GenLayer Studionet contract source, deployment metadata, finalized smoke transactions, and test evidence. Local wallet secrets are not included.

## Live System

| Surface | Link |
| --- | --- |
| App | https://sentinel-five-xi.vercel.app |
| GitHub | https://github.com/thorbh2/sentinel |
| Contract | https://explorer-studio.genlayer.com/contracts/0xFDF377cB5Fb982B4D3f908FB8D3D9dA7aD529032 |
| Deploy tx | https://explorer-studio.genlayer.com/tx/0xfccf5be1d316a0df4794a000e677a84c98b042ff6355bd4218e86ae7ca25357f |
| Vercel inspect | https://vercel.com/aspros-projects-07dbbeb8/sentinel/6dZ52dyNEt4EHLHYU1MgCbjUvY4v |

## Why Sentinel Exists

A GenLayer bonded fact-verification court. Operators file source-backed claims, post bonds, counter-bond disputed statements, attach evidence and obligations, run GenLayer web/LLM review, then resolve challenges, appeals, payouts, archives, reputation and audit trails.

The frontend keeps the original product experience, while the contract adds a reviewable on-chain lifecycle: source records, GenLayer reasoning, challenge and appeal paths, indexed reads, and an audit trail that can be inspected after deployment.

## Contract Architecture

| Area | Detail |
| --- | --- |
| Contract | `contracts/sentinel_v2.py` |
| Size | 50033 bytes |
| Network | GenLayer Studionet, chain id `61999` |
| Write methods | 31 |
| Read methods | 22 |
| GenLayer features | live web rendering, LLM execution, validator-comparative consensus |
| Deployment wallet | 0x393F435b0B6B9784a35686Ad089A856aFB460179 |
| Contract address | 0xFDF377cB5Fb982B4D3f908FB8D3D9dA7aD529032 |

Architecture note:

> Sentinel V2 (# v0.2.16), 50033 bytes, 31 write + 22 view. Objects: Claim/Dossier, Stake, Obligation, Evidence, Review, Challenge, Appeal, Reputation/Profile + AuditEntry. Lifecycle OPEN->REVIEWING->REVIEWED->CHALLENGE_WINDOW->APPEALED->RESOLVED->ARCHIVED. GenLayer nondet (web.render + exec_prompt inside eq_principle.prompt_comparative) reviews public source evidence, challenges and appeals; strict JSON normalization, confidence/trigger bps, URL validation and prompt-injection guardrails. Backward-compatible assert_claim/challenge/adjudicate/get_claim/get_claim_count keep the static case-file app intact.

Core smoke flow:

```text
set_claim_standard
  -> assert_claim
  -> add_obligation
  -> add_evidence_docs
  -> add_evidence_web
  -> challenge
  -> open_review
  -> review
  -> open_challenge_window
  -> submit_challenge
  -> resolve_challenge
  -> submit_appeal
  -> resolve_appeal
```

## Verification Trail

| Step | Transaction |
| --- | --- |
| Set Claim Standard | https://explorer-studio.genlayer.com/tx/0xbf208b6ccabbf31792be75b3abd506ff2aa439b36f2982d3b52f0b0ecc259efc |
| Assert Claim | https://explorer-studio.genlayer.com/tx/0x945a0683d181099a1b8c23d43043ebc67ef75a6e6e618a8c21000466b1cd9a99 |
| Add Obligation | https://explorer-studio.genlayer.com/tx/0x6884467131cf8e10eebf47bef818986c118f15966f8c03bd9b0f4daf12c831b2 |
| Add Evidence Docs | https://explorer-studio.genlayer.com/tx/0x38f9d6e765dd3878dfd7cdaad85bdadcdf45397c529e338a5a5c0362014578de |
| Add Evidence Web | https://explorer-studio.genlayer.com/tx/0x431170bd4944556c4746bfb87c8d52be1d84d2bafea4d6b0d80cb879cecaab22 |
| Challenge | https://explorer-studio.genlayer.com/tx/0x1855b36beb5dcce64ff039e0c227e6348fa5a682bf5c177706abf895ae8ab106 |
| Open Review | https://explorer-studio.genlayer.com/tx/0x46e6376a4cf38087a383e351a0072d20acb90f79561b6bdaf108cdd77464f227 |
| Review | https://explorer-studio.genlayer.com/tx/0x709ec4417b799b3eb78643f6dc2a9c084c7be982c08439baeef9d6797c5795ff |
| Open Challenge Window | https://explorer-studio.genlayer.com/tx/0x65de9ac3c9d1cf1dea5b05e174e322a23494b6f77663253730d4fa265df95688 |
| Submit Challenge | https://explorer-studio.genlayer.com/tx/0x7d7f4a1fbb5fca0f57a5456eb2840f3d5fc7dd57ee0e255b0c9c6193b7976ea4 |
| Resolve Challenge | https://explorer-studio.genlayer.com/tx/0x78d498ff25f2585486a884fc198a4ac128865d6a887b6b2c272eec76bb6bfb71 |
| Submit Appeal | https://explorer-studio.genlayer.com/tx/0x5ccca5654d9b312bd0b98c36239995eb97f219bdd56112a87df442e6368da424 |
| Resolve Appeal | https://explorer-studio.genlayer.com/tx/0x114b71d497b025b2d8ecf23d11c908ec575fc27431bd18eaec51fbcc059fa9b1 |
| Adjudicate | https://explorer-studio.genlayer.com/tx/0x12c52e869461d5e4c7650a19a91bf58a01380fb9d4485cf260abc9be0e06fa68 |

Test result:

```text
Schema valid
19 smoke writes finalized
41/41
Static frontend bundled for standalone Vercel deployment
```

## Frontend

Sentinel ships as a standalone static app:

- wallet connection through the bundled browser client
- GenLayer reads through `genlayer-js`
- writes routed through the connected EVM wallet
- local `shared/` client files included so Vercel does not depend on the private workspace router
- deployed contract address pinned in `app.js` and `deployment.json`

## Run Locally

From the private workspace:

```powershell
cd <private-workspace-root>
npm run preview:start
npm run preview:project -- 04-sentinel
```

Open:

```text
http://localhost:8080/04-sentinel/
```

## Publish / Redeploy

```powershell
cd <private-workspace-root>
npm run publish:project -- -Project 04-sentinel -Repo https://github.com/thorbh2/sentinel.git
```

Vercel production redeploy from a clean project folder:

```powershell
npx --yes vercel@latest --prod --yes
```

## Repository Safety

This public repository intentionally excludes local secrets:

- no private keys
- no vault files
- no `.env` files
- no `.vercel` project state
- no local dashboard data

Public files include frontend code, contract source, deployment metadata, tests, and non-sensitive proof links.
