# Xenovia demo agents — Innotecq partner pack

Four enterprise agents at a fictional EU mid-cap (**Veldhoff Logistics GmbH**,
Hamburg; all names, customers, and IBANs are invented). Each agent is a
LangChain tool-calling loop (`ChatOpenAI` + `bind_tools`) over a mocked
backend, with a `normal` scenario and a scripted red-team scenario. Strategy
and personas per agent: [USE-CASES.md](USE-CASES.md).

**The point of the architecture:** there is no governance logic anywhere in
this code. LangChain's `ChatOpenAI` points at `XENOVIA_BASE_URL`, so whatever
sits behind it decides whether a risky action executes: a raw model endpoint
runs everything, a Xenovia tenant governs it. The integration is the URL.

## Setup

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env   # then set XENOVIA_BASE_URL / XENOVIA_API_KEY / XENOVIA_MODEL
```

## Web console (chat)

The console is a ChatGPT-style app (React UI in `web/`, FastAPI in `server.py`):
pick an agent in the sidebar and **talk to it**. Each agent holds its own conversation over its
own dummy backend (ERP, directory, CRM, tables — seeded with the bait), and
every reply is a live model call through the selected endpoint. Tool calls and
their results render inline in the thread; when the agent does something a
policy pack would stop, an incident block appears and the sidebar badge counts
it. A header toggle switches between **Xenovia** (model calls routed through the
proxy) and **Direct** (straight to the model, no proxy), the before/after in one
click. Both are real LangChain calls; only the base URL differs.

There are no scripted scenarios: the red-team moments happen because the bait
lives in the data (invoice `INV-2204`, ticket `T-102`, ticket `T-502`, request
`DR-2288`). Ask the agent to work its queue, or hand it the poisoned item by
name, and watch what it does.

The UI is a **React app** (`web/`, Vite) styled to match app.xenovia.io. The
FastAPI backend (`server.py`) holds the sessions, dummy backends, and the live
Xenovia proxy; it also serves the built React app in production.

### Run it locally

Two processes in dev — the backend, and the Vite dev server that proxies `/api`
to it:

```bash
# terminal 1 — backend
XENOVIA_BASE_URL=... uvicorn server:app --port 8000

# terminal 2 — UI with hot reload + React Grab
cd web && npm install && npm run dev      # http://localhost:5173
```

To run the production path (what Railway serves) from one process:

```bash
npm --prefix web install && npm --prefix web run build
uvicorn server:app --port 8000            # serves web/dist at /
```

Environment (backend). Both are real, OpenAI-compatible endpoints; there is no
mock. Point both at the same model for a clean before/after.

- `XENOVIA_BASE_URL` / `XENOVIA_API_KEY` / `XENOVIA_MODEL` — the Xenovia proxy
  (the "Xenovia" mode).
- `DIRECT_BASE_URL` / `DIRECT_API_KEY` / `DIRECT_MODEL` — the model provider
  called directly (the "Direct" mode). A mode's toggle is disabled until set.
- `DEMO_PASSWORD` — password gate. When set, the console shows a login screen and
  the API withholds everything (roster, modes, chat) until the visitor enters it;
  the key is checked with a constant-time compare and login attempts are
  rate-limited per IP. **Set it on any public deployment** — without it, anyone
  with the URL can start conversations against your API keys.

## Grab UI elements while iterating

[React Grab](https://github.com/aidenybai/react-grab) is a devDependency
(`web/`) loaded only in Vite dev (`import.meta.env.DEV`), so it never ships in
the production build. In `npm run dev`, hover any part of the console, grab it
(⌘C / Ctrl+C or the send-to-agent box), and the agent gets your selection
mapped to the actual **component and source line** (e.g.
`web/src/components/Topbar.jsx:26`) — click a component, don't describe it.

## Deploy on Railway

The build is a two-stage `Dockerfile` (Node builds `web/`, Python serves the API
+ built UI); `railway.json` points Railway at it with a `/health` healthcheck.

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
server.py          FastAPI: /api chat streaming, sessions, gate; serves web/dist
harness.py         LangChain tool-calling loop and event stream (continue_events)
agents/            one file per agent: prompt, dummy backend, starters, selftests
web/               React UI (Vite) — components in web/src/components/
  src/App.jsx      state, streaming reducer, agent switching
  src/components/  Sidebar, ChatPane, Topbar, RegimeToggle, Hero, Thread, …
run_demo.py        CLI: list, selftest, or run an agent scenario headless
Dockerfile         two-stage build (Node builds web/, Python serves) for Railway
railway.json       points Railway at the Dockerfile + /health healthcheck
USE-CASES.md       the strategy doc: narrative, personas, why these four
```

The `agents/` backends still ship canned scenarios, used by `run_demo.py` for
headless CLI runs and by the offline selftests. The chat console ignores the
scenario framing and just seeds the fullest backend (bait included) per
conversation.
