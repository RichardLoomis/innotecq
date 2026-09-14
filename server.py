"""Web console for the Xenovia demo agents — a live chat surface.

Each of the four agents holds its own conversation: a session pins a fresh
dummy backend (ERP, directory, CRM, tables — bait included) plus the message
history, and every model call goes live through the endpoint behind the base
URL. POST /api/chat streams NDJSON events for one user message; sessions
persist in memory until reset.

Two modes, toggled per message:
  proxy  -> XENOVIA_BASE_URL / XENOVIA_API_KEY / XENOVIA_MODEL   (via Xenovia)
  direct -> DIRECT_BASE_URL / DIRECT_API_KEY / DIRECT_MODEL      (no proxy)
Both are real LLM endpoints; the toggle only changes the base URL. Also:
  DEMO_PASSWORD          optional access key; set it on any public deployment
"""

from __future__ import annotations

import hmac
import json
import pathlib
import threading
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from langchain_core.messages import HumanMessage, SystemMessage

from agents import AGENTS
from agents.base import load_env

ROOT = pathlib.Path(__file__).resolve().parent
WEB_DIST = ROOT / "web" / "dist"
DEFAULT_MODEL = "claude-sonnet-5"
MAX_CONCURRENT_CHATS = 8
MAX_SESSIONS = 40
MAX_MESSAGE_CHARS = 2000
MAX_ITERS_PER_MESSAGE = 10
LOGIN_WINDOW = 60.0          # seconds
LOGIN_MAX_ATTEMPTS = 10      # per IP per window, to slow brute force

app = FastAPI(title="Xenovia demo console")

_sessions: dict[str, dict] = {}
_login_hits: dict[str, list[float]] = {}
_lock = threading.Lock()
_active_chats = 0


def _env_prefix(mode: str) -> str:
    return "DIRECT" if mode == "direct" else "XENOVIA"


def _endpoint(mode: str, agent_key: str) -> dict | None:
    """Resolve one agent's LLM endpoint for a mode.

    Each agent has its own gateway, so config is per-agent:
      <PREFIX>_<AGENT>_BASE_URL / _API_KEY / _MODEL
    falling back to a global <PREFIX>_BASE_URL / ... when an agent has none.
    PREFIX is XENOVIA for the proxy mode (governed) and DIRECT for direct
    (no proxy). AGENT is the upper-cased key, e.g. XENOVIA_HELPDESK_BASE_URL.
    """
    env = load_env()
    prefix = _env_prefix(mode)
    agent = agent_key.upper()

    def get(suffix: str) -> str:
        return env.get(f"{prefix}_{agent}_{suffix}") or env.get(f"{prefix}_{suffix}", "")

    base_url = get("BASE_URL")
    if not base_url:
        return None
    return {
        "base_url": base_url,
        "api_key": get("API_KEY"),
        "model": get("MODEL") or DEFAULT_MODEL,
    }


def _demo_password() -> str:
    return load_env().get("DEMO_PASSWORD", "")


def _matches(supplied: str) -> bool:
    """Constant-time comparison against the configured password."""
    password = _demo_password()
    if not password:
        return True
    return hmac.compare_digest(str(supplied).encode(), password.encode())


def _authorized(request: Request) -> bool:
    if not _demo_password():
        return True
    return _matches(request.headers.get("x-demo-key", ""))


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(ip: str) -> bool:
    """Simple sliding-window guard on login attempts per client."""
    now = time.time()
    with _lock:
        hits = [t for t in _login_hits.get(ip, []) if now - t < LOGIN_WINDOW]
        hits.append(now)
        _login_hits[ip] = hits
        return len(hits) > LOGIN_MAX_ATTEMPTS


def _get_session(session_id: str | None, agent_key: str) -> tuple[str, dict] | None:
    """Fetch or create a session; returns None when it belongs to another agent."""
    with _lock:
        if session_id and session_id in _sessions:
            session = _sessions[session_id]
            if session["agent"] != agent_key:
                return None
            session["last_used"] = time.time()
            return session_id, session
        if len(_sessions) >= MAX_SESSIONS:
            oldest = min(_sessions, key=lambda k: _sessions[k]["last_used"])
            del _sessions[oldest]
        agent = AGENTS[agent_key]
        new_id = uuid.uuid4().hex[:16]
        _sessions[new_id] = {
            "agent": agent_key,
            "world": agent.new_world(),
            "messages": [SystemMessage(content=agent.system_prompt)],
            "busy": False,
            "last_used": time.time(),
        }
        return new_id, _sessions[new_id]


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/login")
async def login(request: Request) -> JSONResponse:
    if _rate_limited(_client_ip(request)):
        return JSONResponse({"ok": False, "error": "too many attempts, wait a minute"},
                            status_code=429)
    if not _demo_password():
        return JSONResponse({"ok": True})
    body = await request.json()
    ok = _matches(body.get("password", ""))
    return JSONResponse({"ok": ok}, status_code=200 if ok else 401)


@app.get("/api/agents")
def roster(request: Request) -> dict:
    gated = bool(_demo_password())
    authorized = _authorized(request)
    if gated and not authorized:
        # withhold everything until the visitor authenticates
        return {"gated": True, "authorized": False, "agents": []}
    return {
        "gated": gated,
        "authorized": authorized,
        "agents": [
            {
                "key": agent.key,
                "title": agent.title,
                "tagline": agent.tagline,
                "starters": agent.starters,
                # each agent has its own gateway, so mode availability is per-agent
                "modes": {
                    "proxy": _endpoint("proxy", agent.key) is not None,
                    "direct": _endpoint("direct", agent.key) is not None,
                },
            }
            for agent in AGENTS.values()
        ],
    }


def _chat_stream(session_id: str, session: dict, text: str, endpoint: dict):
    global _active_chats
    world = session["world"]
    agent = AGENTS[session["agent"]]
    try:
        yield json.dumps({"type": "session", "id": session_id}) + "\n"
        session["messages"].append(HumanMessage(content=text))
        seen = len(world.incidents)
        for event in agent.stream(
            world,
            session["messages"],
            base_url=endpoint["base_url"],
            api_key=endpoint["api_key"],
            model=endpoint["model"],
            max_iters=MAX_ITERS_PER_MESSAGE,
        ):
            yield json.dumps(event) + "\n"
        new_incidents = world.incidents[seen:]
        if new_incidents:
            yield json.dumps({"type": "incidents", "items": new_incidents}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"
    except Exception as exc:  # keep the console alive whatever a turn does
        yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"
    finally:
        session["busy"] = False
        session["last_used"] = time.time()
        with _lock:
            _active_chats -= 1


@app.post("/api/chat", response_model=None)
async def chat(request: Request) -> StreamingResponse | JSONResponse:
    global _active_chats
    if not _authorized(request):
        return JSONResponse({"error": "access key required"}, status_code=401)

    body = await request.json()
    agent_key = body.get("agent", "")
    text = str(body.get("message", "")).strip()
    mode = body.get("mode", "proxy")

    if agent_key not in AGENTS:
        return JSONResponse({"error": f"unknown agent '{agent_key}'"}, status_code=404)
    if not text:
        return JSONResponse({"error": "message is empty"}, status_code=400)
    if len(text) > MAX_MESSAGE_CHARS:
        return JSONResponse({"error": f"message is over {MAX_MESSAGE_CHARS} characters"},
                            status_code=400)
    if mode not in ("proxy", "direct"):
        return JSONResponse({"error": f"unknown mode '{mode}'"}, status_code=400)

    endpoint = _endpoint(mode, agent_key)
    if endpoint is None:
        variable = f"{_env_prefix(mode)}_{agent_key.upper()}_BASE_URL"
        return JSONResponse({"error": f"{mode} gateway for '{agent_key}' is not configured, set {variable}"},
                            status_code=409)

    got = _get_session(body.get("session"), agent_key)
    if got is None:
        return JSONResponse({"error": "session belongs to a different agent"}, status_code=409)
    session_id, session = got

    with _lock:
        if session["busy"]:
            return JSONResponse({"error": "this conversation is still replying"}, status_code=429)
        if _active_chats >= MAX_CONCURRENT_CHATS:
            return JSONResponse({"error": "too many conversations in flight — try again shortly"},
                                status_code=429)
        session["busy"] = True
        _active_chats += 1

    return StreamingResponse(
        _chat_stream(session_id, session, text, endpoint),
        media_type="application/x-ndjson",
        headers={"cache-control": "no-store", "x-accel-buffering": "no"},
    )


@app.post("/api/reset")
async def reset(request: Request) -> JSONResponse:
    if not _authorized(request):
        return JSONResponse({"error": "access key required"}, status_code=401)
    body = await request.json()
    with _lock:
        _sessions.pop(body.get("session", ""), None)
    return JSONResponse({"ok": True})


# Serve the built React app (see web/). In production the Docker build runs
# `vite build` first, so web/dist exists and is mounted at "/". API routes are
# declared above, so they take precedence over this catch-all mount. In local
# dev without a build, run the Vite dev server (web/: npm run dev), which
# proxies /api and /health here.
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:
    @app.get("/")
    def index() -> JSONResponse:
        return JSONResponse({
            "error": "web/dist not built",
            "hint": "Run the Vite dev server (cd web && npm run dev) for local dev, "
                    "or `npm --prefix web run build` to serve the built UI from here.",
        }, status_code=503)
