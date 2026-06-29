# Sentinel V2

A GenLayer bonded fact-verification court.

The project is built as a small on-chain court rather than a static demo: users create records, attach sources, ask GenLayer to reason over them, and keep the decision trail readable.

## Sentinel Brief

- Project folder: `projects/04-sentinel`
- Frontend: static browser app
- Contract package: `contracts/` plus `deployment.json`
- Build status: Schema-valid (50033 bytes, 31 write + 22 view); clean redeploy + 19 write smoke txs finalized incl 4 GenLayer reasoning calls and legacy assert/challenge/adjudicate flow; 41/41 read tests passed; app.js repointed.
- QA notes: Upgraded from a compact bonded fact-check MVP into Sentinel V2. Smoke: set_claim_standard / assert_claim / add_obligation / two add_evidence calls / challenge / open_review / review_claim_with_genlayer / open_challenge_window / submit_challenge / resolve_ch...

## Network Record

- Network: studionet (61999)
- Contract: [0xFDF377cB5Fb982B4D3f908FB8D3D9dA7aD529032](https://explorer-studio.genlayer.com/contracts/0xFDF377cB5Fb982B4D3f908FB8D3D9dA7aD529032)
- Deploy tx: [0xfccf5be1...25357f](https://explorer-studio.genlayer.com/tx/0xfccf5be1d316a0df4794a000e677a84c98b042ff6355bd4218e86ae7ca25357f)
- Deployed at: 2026-06-24T00:54:33.804Z
- Smoke writes recorded: 19

## Adjudication Mechanics

- Primary source: `contracts/sentinel_v2.py` (50,033 bytes)
- Public write/action methods: 31
- Read methods: 22
- GenLayer features: live web rendering, LLM adjudication, validator-comparative consensus, indexed storage, append-only collections

Typical flow: `open_claim` -> `submit` -> `review` -> `resolve` -> `challenge` -> `submit_appeal` -> `set_claim_standard` -> `archive_claim`

Useful reads: `get_claim_count`, `get_claim`, `get_item_count`, `get_item`, `get_stake_count`, `get_stake`, `get_claim_record`, `get_recent_claims`

The contract is deliberately larger than a one-method demo. It keeps lifecycle state, evidence records and read endpoints so the UI can show real project state instead of static copy.

## Inspect The App

```powershell
cd C:\Users\aspronim\Desktop\design-skills
npm run preview:start
npm run preview:project -- 04-sentinel
```

Open http://localhost:8080/04-sentinel/.

## Smoke Transactions

- set_claim_standard: [0xbf208b6c...259efc](https://explorer-studio.genlayer.com/tx/0xbf208b6ccabbf31792be75b3abd506ff2aa439b36f2982d3b52f0b0ecc259efc)
- assert_claim: [0x945a0683...cd9a99](https://explorer-studio.genlayer.com/tx/0x945a0683d181099a1b8c23d43043ebc67ef75a6e6e618a8c21000466b1cd9a99)
- add_obligation: [0x68844671...c831b2](https://explorer-studio.genlayer.com/tx/0x6884467131cf8e10eebf47bef818986c118f15966f8c03bd9b0f4daf12c831b2)
- add_evidence_docs: [0x38f9d6e7...4578de](https://explorer-studio.genlayer.com/tx/0x38f9d6e765dd3878dfd7cdaad85bdadcdf45397c529e338a5a5c0362014578de)
- add_evidence_web: [0x431170bd...caab22](https://explorer-studio.genlayer.com/tx/0x431170bd4944556c4746bfb87c8d52be1d84d2bafea4d6b0d80cb879cecaab22)
- challenge: [0x1855b36b...8ab106](https://explorer-studio.genlayer.com/tx/0x1855b36beb5dcce64ff039e0c227e6348fa5a682bf5c177706abf895ae8ab106)
- open_review: [0x46e6376a...64f227](https://explorer-studio.genlayer.com/tx/0x46e6376a4cf38087a383e351a0072d20acb90f79561b6bdaf108cdd77464f227)
- review: [0x709ec441...5795ff](https://explorer-studio.genlayer.com/tx/0x709ec4417b799b3eb78643f6dc2a9c084c7be982c08439baeef9d6797c5795ff)

## Shipping Notes

```powershell
cd C:\Users\aspronim\Desktop\design-skills
npm run publish:project -- -Project 04-sentinel -Repo https://github.com/aspro45/<repo-name>.git
```

Replace `<repo-name>` with the GitHub repository name before publishing.

## Security Notes

- Private keys and local vault files are not part of this repository.
- Public addresses, contract source, deployment metadata and frontend code are safe to publish.
- Vercel should receive only this project folder, never the workspace dashboard or vault data.
