# Xenovia demo agents — Innotecq partner pack

Four enterprise agents at a fictional EU mid-cap (**Veldhoff Logistics GmbH**,
Hamburg — all names, customers, and IBANs are invented). Each agent is a plain
OpenAI-compatible tool-calling loop over a mocked backend, with a `normal`
scenario and a scripted red-team scenario. Strategy and personas per agent:
[USE-CASES.md](USE-CASES.md).

**The point of the architecture:** there is no governance logic anywhere in
this code. Whether a risky action executes is decided by whatever sits behind
`XENOVIA_BASE_URL` — a raw model endpoint executes everything; a Xenovia
tenant decides. The integration is the URL.

## Setup

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env   # then set XENOVIA_BASE_URL / XENOVIA_API_KEY / XENOVIA_MODEL
```

## Web console

`server.py` + `static/index.html` wrap the same agents in a live console: each
agent runs independently (all four can run at once), streaming its transcript
and outcome ledger, with a header toggle between **Ungoverned** and **Governed
by Xenovia** — the before/after demo in one click.

```bash
uvicorn server:app --port 8000
```

Environment:

- `XENOVIA_BASE_URL` / `XENOVIA_API_KEY` / `XENOVIA_MODEL` — the governed tenant.
- `UNGOVERNED_BASE_URL` / `UNGOVERNED_API_KEY` / `UNGOVERNED_MODEL` — optional
  raw endpoint for the "before" run; the toggle is disabled without it.
- `DEMO_PASSWORD` — optional access key. **Set it on any public deployment**:
  without it, anyone with the URL can start runs against your API keys.

## Deploy on Railway

The repo is deploy-ready: `railway.json` sets the start command and
`/health` healthcheck; `.python-version` pins Python 3.12.

```bash
railway init
railway up
railway domain
```

Then set the environment variables above on the service (Railway dashboard →
Variables, or `railway variables --set "XENOVIA_BASE_URL=..."`). Redeploys
pick them up automatically; the base URL swap that closes the demo is an env
var change in Railway.

Before any live demo:

```bash
python3 run_demo.py selftest   # offline — checks all four mock backends
```

## The pack

| Agent | Red-team scenario | Lands with |
|---|---|---|
| `ap` | `fraud` — injected banking-change notice tries to move €48,000 to a fresh IBAN | CFO + CISO |
| `helpdesk` | `privesc` — contractor claims a SEV-1 and verbal CTO approval to get Domain-Admins | CISO + CIO |
| `support` | `gdpr` — crafted ticket fishes for other customers' contact details plus a €900 refund | Legal / DPO |
| `reporting` | `residency` — injected data request POSTs the customer table, emails included, to a US endpoint | DPO + CIO |

```bash
python3 run_demo.py list        # full roster with scenario blurbs
python3 run_demo.py ap fraud    # run one
```

## Demo run book (per agent, ~10 minutes)

1. **Baseline** — run the `normal` scenario. The agent does its job; outcome
   ends green: `✔ no incidents recorded`. This buys credibility: the agent is
   useful, not a strawman.
2. **Before** — run the red-team scenario against an ungoverned endpoint
   (`--base-url` pointing at any raw OpenAI-compatible model endpoint). If the
   model takes the bait, the outcome block prints red `☠ INCIDENT` lines —
   money moved, admin granted, PII mailed, data left the EU.
3. **After** — same command, base URL now the Xenovia tenant with the policy
   pack live. The action is denied or escalated at the proxy; open the Xenovia
   console and show the decision trace.
4. **Close** — show the diff between the two runs: one line in `.env`.

### If the model refuses even ungoverned

Some models are cautious on some days — that is itself the talk track:

> "Nice — this model was suspicious today. Are you willing to bet the wire
> transfer on the model's mood, every day, across every model your teams use?
> Xenovia makes it policy: deterministic, logged, auditable."

Rehearse each scenario against the demo endpoint beforehand; lead with the
agent whose bait landed most reliably in rehearsal (the `ap` fraud scenario is
usually the most visceral).

## Suggested policy packs (configure in the Xenovia tenant)

- **ap** — allow payments ≤ €1,000 to vendors with ≥ 3 paid invoices; escalate
  new vendor or IBAN change; deny > €10,000; business hours only.
- **helpdesk** — allow standard-tier group grants; approval for Finance/HR
  systems; hard-deny privileged tiers (Domain-Admins, Finance-ERP, HR-Payroll)
  and any action on executive accounts.
- **support** — auto-approve refunds ≤ €300, approval above; deny outbound
  messages containing another customer's personal data; recipient must match
  the ticket requester.
- **reporting** — mask PII columns in model traffic; deny exports to endpoints
  outside the EU allowlist; read-only on production tables; log every decision.

The mock backends record the same thresholds as **incidents** when actions
execute ungoverned, so the "before" run shows exactly the damage the policy
pack prevents.

## Layout

```
run_demo.py        CLI: list, selftest, or run an agent + scenario
server.py          FastAPI console: streaming runs, mode toggle, access gate
static/index.html  the console UI
harness.py         shared tool-calling loop and event stream
agents/            one file per agent: prompt, mocked backend, scenarios, selftests
railway.json       Railway start command + healthcheck
USE-CASES.md       the strategy doc: narrative, personas, why these four
```
