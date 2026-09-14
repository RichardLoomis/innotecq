"""Shared primitives for the demo agents.

This is NOT an agent runner. Each agent (agents/*_agent.py) is its own
self-contained class that owns its LangChain loop, its tools, its mocked
backend, and its gateway. What lives here is only the plumbing they have in
common: the mocked-backend base, the tool type, and small helpers.

There is deliberately no governance logic anywhere. Whether a risky action
executes is decided by whatever sits behind the base URL each agent is pointed
at: a Xenovia gateway governs it, a direct endpoint runs it.
"""

from __future__ import annotations

import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Callable

ROOT = pathlib.Path(__file__).resolve().parents[1]  # project root (one up from agents/)

_TTY = sys.stdout.isatty()


def _c(code: str) -> str:
    return code if _TTY else ""


BOLD = _c("\033[1m")
DIM = _c("\033[2m")
RED = _c("\033[31m")
GREEN = _c("\033[32m")
RESET = _c("\033[0m")


def load_env() -> dict[str, str]:
    """Read .env (comments on their own lines); real env vars win."""
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    for key, value in os.environ.items():
        if key.startswith(("XENOVIA_", "DIRECT_", "DEMO_")) and value:
            env[key] = value
    return env


class World:
    """Mocked backend state for one conversation.

    Subclasses expose tools and track what actually happened. `incidents` holds
    the damage report: actions that executed here but that a Xenovia policy pack
    would have denied or escalated.
    """

    def __init__(self) -> None:
        self.incidents: list[str] = []

    def tools(self) -> list["Tool"]:
        raise NotImplementedError

    def summary(self) -> list[str]:
        return []


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable[..., str]


@dataclass
class Selftest:
    name: str
    scenario: str
    calls: list[tuple[str, dict]]
    expect_incidents: bool


def short(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def tool_schemas(tools: dict[str, Tool]) -> list[dict]:
    return [
        {"type": "function",
         "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
        for t in tools.values()
    ]


def execute(tools: dict[str, Tool], name: str, args: dict) -> str:
    tool = tools.get(name)
    if tool is None:
        return f"error: unknown tool '{name}'"
    try:
        return tool.fn(**args)
    except Exception as exc:  # surface bad args back to the model, keep the demo alive
        return f"error: {exc}"


def make_llm(base_url: str, api_key: str, model: str, tools: dict[str, Tool]):
    """Build a LangChain ChatOpenAI bound to an agent's tools.

    base_url points at the agent's gateway (Xenovia proxy) or a direct endpoint;
    that choice is the whole demo. Every agent builds its own via this helper.
    """
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=model, base_url=base_url, api_key=api_key or "xenovia-demo")
    return llm.bind_tools(tool_schemas(tools))


def run_selftests(agents) -> bool:
    """Exercise every agent's mocked backend offline — no network, no model."""
    ok = True
    for agent in agents:
        for test in agent.selftests:
            world = agent.build_world(test.scenario)
            tools = {t.name: t for t in world.tools()}
            failure = ""
            for name, args in test.calls:
                result = execute(tools, name, args)
                if result.startswith("error:"):
                    failure = f"{name} -> {result}"
                    break
            if not failure and bool(world.incidents) != test.expect_incidents:
                expected = "incidents" if test.expect_incidents else "no incidents"
                failure = f"expected {expected}, got {world.incidents or 'none'}"
            mark = f"{GREEN}pass{RESET}" if not failure else f"{RED}FAIL{RESET}"
            print(f"  {mark}  {agent.key}: {test.name}" + (f" — {failure}" if failure else ""))
            ok = ok and not failure
    return ok
