"""Web console for the Xenovia demo agents.

Each of the four agents runs independently: POST /api/run starts one isolated
run (fresh world, own tool set) and streams NDJSON events until the outcome.
Runs are concurrent — the console can drive all four at once.

Endpoints are configured by environment (or .env locally):
  XENOVIA_BASE_URL / XENOVIA_API_KEY / XENOVIA_MODEL       the governed tenant
  UNGOVERNED_BASE_URL / UNGOVERNED_API_KEY / UNGOVERNED_MODEL
                                    optional raw endpoint for the "before" run
  DEMO_PASSWORD          optional access key; set it on any public deployment
"""

from __future__ import annotations

import json
import pathlib
import threading

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from agents import AGENTS
from harness import load_env, run_agent_events

ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_MODEL = "claude-sonnet-5"
MAX_CONCURRENT_RUNS = 6

app = FastAPI(title="Xenovia demo console")

_active_runs = 0
_runs_lock = threading.Lock()


def _endpoint(mode: str) -> dict | None:
    env = load_env()
    if mode == "ungoverned":
        base_url = env.get("UNGOVERNED_BASE_URL")
        if not base_url:
            return None
        return {
            "base_url": base_url,
            "api_key": env.get("UNGOVERNED_API_KEY", ""),
            "model": env.get("UNGOVERNED_MODEL") or env.get("XENOVIA_MODEL", DEFAULT_MODEL),
        }
    base_url = env.get("XENOVIA_BASE_URL")
    if not base_url:
        return None
    return {
        "base_url": base_url,
        "api_key": env.get("XENOVIA_API_KEY", ""),
        "model": env.get("XENOVIA_MODEL", DEFAULT_MODEL),
    }


def _authorized(request: Request) -> bool:
    password = load_env().get("DEMO_PASSWORD", "")
    return not password or request.headers.get("x-demo-key", "") == password


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/agents")
def roster(request: Request) -> dict:
    env = load_env()
    return {
        "gated": bool(env.get("DEMO_PASSWORD")),
        "authorized": _authorized(request),
        "modes": {
            "governed": _endpoint("governed") is not None,
            "ungoverned": _endpoint("ungoverned") is not None,
        },
        "endpoints": {
            "governed": (_endpoint("governed") or {}).get("base_url"),
            "ungoverned": (_endpoint("ungoverned") or {}).get("base_url"),
        },
        "agents": [
            {
                "key": agent.key,
                "title": agent.title,
                "tagline": agent.tagline,
                "scenarios": [
                    {"key": s.key, "blurb": s.blurb, "red_team": s.key != "normal"}
                    for s in agent.scenarios.values()
                ],
            }
            for agent in AGENTS.values()
        ],
    }


def _event_stream(agent_key: str, scenario_key: str, endpoint: dict):
    global _active_runs
    try:
        for event in run_agent_events(
            AGENTS[agent_key],
            scenario_key,
            base_url=endpoint["base_url"],
            api_key=endpoint["api_key"],
            model=endpoint["model"],
        ):
            yield json.dumps(event) + "\n"
    except Exception as exc:  # keep the console alive whatever a run does
        yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
        yield json.dumps({"type": "done", "finished": False}) + "\n"
    finally:
        with _runs_lock:
            _active_runs -= 1


@app.post("/api/run", response_model=None)
async def run(request: Request) -> StreamingResponse | JSONResponse:
    global _active_runs
    if not _authorized(request):
        return JSONResponse({"error": "access key required"}, status_code=401)

    body = await request.json()
    agent_key = body.get("agent", "")
    scenario_key = body.get("scenario", "normal")
    mode = body.get("mode", "governed")

    agent = AGENTS.get(agent_key)
    if agent is None:
        return JSONResponse({"error": f"unknown agent '{agent_key}'"}, status_code=404)
    if scenario_key not in agent.scenarios:
        return JSONResponse({"error": f"unknown scenario '{scenario_key}'"}, status_code=404)
    if mode not in ("governed", "ungoverned"):
        return JSONResponse({"error": f"unknown mode '{mode}'"}, status_code=400)

    endpoint = _endpoint(mode)
    if endpoint is None:
        variable = "UNGOVERNED_BASE_URL" if mode == "ungoverned" else "XENOVIA_BASE_URL"
        return JSONResponse({"error": f"{mode} endpoint is not configured — set {variable}"},
                            status_code=409)

    with _runs_lock:
        if _active_runs >= MAX_CONCURRENT_RUNS:
            return JSONResponse({"error": "too many runs in flight — wait for one to finish"},
                                status_code=429)
        _active_runs += 1

    return StreamingResponse(
        _event_stream(agent_key, scenario_key, endpoint),
        media_type="application/x-ndjson",
        headers={"cache-control": "no-store", "x-accel-buffering": "no"},
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")
