"""Shared demo harness: a plain OpenAI-compatible tool-calling loop.

There is deliberately NO governance logic in this codebase. Whether an agent's
risky action executes is decided by whatever sits behind XENOVIA_BASE_URL:
point it at a raw model endpoint and everything the model asks for runs; point
it at a Xenovia tenant and Xenovia decides. The agent code never changes —
that is the demo.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Callable

ROOT = pathlib.Path(__file__).resolve().parent

_TTY = sys.stdout.isatty()


def _c(code: str) -> str:
    return code if _TTY else ""


BOLD = _c("\033[1m")
DIM = _c("\033[2m")
RED = _c("\033[31m")
GREEN = _c("\033[32m")
YELLOW = _c("\033[33m")
CYAN = _c("\033[36m")
RESET = _c("\033[0m")


def load_env() -> dict[str, str]:
    """Read .env (keep comments on their own lines); real env vars win."""
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    for key in ("XENOVIA_BASE_URL", "XENOVIA_API_KEY", "XENOVIA_MODEL"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


class World:
    """Mocked backend state for one demo run.

    Subclasses expose tools and track what actually happened. `incidents`
    holds the damage report: actions that executed here but that a Xenovia
    policy pack would have denied or escalated.
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
class Scenario:
    key: str
    blurb: str
    task: str


@dataclass
class Selftest:
    name: str
    scenario: str
    calls: list[tuple[str, dict]]
    expect_incidents: bool


@dataclass
class Agent:
    key: str
    title: str
    tagline: str
    system_prompt: str
    build: Callable[[str], World]
    scenarios: dict[str, Scenario]
    selftests: list[Selftest] = field(default_factory=list)


def _short(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _schemas(tools: dict[str, Tool]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools.values()
    ]


def _execute(tools: dict[str, Tool], name: str, args: dict) -> str:
    tool = tools.get(name)
    if tool is None:
        return f"error: unknown tool '{name}'"
    try:
        return tool.fn(**args)
    except Exception as exc:  # surface bad args back to the model, keep the demo alive
        return f"error: {exc}"


def run_agent(
    agent: Agent,
    scenario_key: str,
    *,
    base_url: str,
    api_key: str,
    model: str,
    max_turns: int = 14,
) -> None:
    from openai import OpenAI  # imported lazily so `selftest` needs no packages

    scenario = agent.scenarios[scenario_key]
    world = agent.build(scenario_key)
    tools = {t.name: t for t in world.tools()}

    print(f"{BOLD}{agent.title}{RESET} — scenario: {scenario.key}")
    print(f"{DIM}{scenario.blurb}{RESET}")
    print(f"{DIM}endpoint: {base_url}  ·  model: {model}{RESET}\n")

    messages: list = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": scenario.task},
    ]
    client = OpenAI(base_url=base_url, api_key=api_key or "xenovia-demo")

    for _ in range(max_turns):
        reply = (
            client.chat.completions.create(model=model, messages=messages, tools=_schemas(tools))
            .choices[0]
            .message
        )
        messages.append(reply)
        if not reply.tool_calls:
            print(f"\n{BOLD}agent:{RESET} {reply.content or '(no final message)'}")
            break
        if reply.content:
            print(f"{DIM}agent: {_short(reply.content, 200)}{RESET}")
        for call in reply.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            pretty = ", ".join(f"{k}={_short(repr(v), 70)}" for k, v in args.items())
            print(f"  {CYAN}▶ {call.function.name}({pretty}){RESET}")
            result = _execute(tools, call.function.name, args)
            print(f"    {DIM}{_short(result, 280)}{RESET}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    else:
        print(f"\n{YELLOW}stopped at the turn limit before the agent finished{RESET}")

    print(f"\n{BOLD}── outcome ──{RESET}")
    for line in world.summary():
        print(f"  {line}")
    if world.incidents:
        for incident in world.incidents:
            print(f"  {RED}☠ INCIDENT: {incident}{RESET}")
        print(f"\n  {YELLOW}Every line above is an action a Xenovia policy pack denies or escalates.{RESET}")
        print(f"  {YELLOW}Same agent, same prompt — change the base URL to the governed tenant and rerun.{RESET}")
    else:
        print(f"  {GREEN}✔ no incidents recorded{RESET}")


def run_selftests(agents: list[Agent]) -> bool:
    """Exercise every world's tool handlers offline — no network, no model."""
    ok = True
    for agent in agents:
        for test in agent.selftests:
            world = agent.build(test.scenario)
            tools = {t.name: t for t in world.tools()}
            failure = ""
            for name, args in test.calls:
                result = _execute(tools, name, args)
                if result.startswith("error:"):
                    failure = f"{name} → {result}"
                    break
            if not failure and bool(world.incidents) != test.expect_incidents:
                expected = "incidents" if test.expect_incidents else "no incidents"
                failure = f"expected {expected}, got {world.incidents or 'none'}"
            mark = f"{GREEN}pass{RESET}" if not failure else f"{RED}FAIL{RESET}"
            print(f"  {mark}  {agent.key}: {test.name}" + (f" — {failure}" if failure else ""))
            ok = ok and not failure
    return ok
