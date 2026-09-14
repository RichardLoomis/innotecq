#!/usr/bin/env python3
"""Run the Xenovia demo agents. See README.md for the demo run book.

    python run_demo.py list                 # roster of agents and scenarios
    python run_demo.py selftest             # offline check of all mock backends
    python run_demo.py ap fraud             # run one agent + scenario
    python run_demo.py ap fraud --base-url https://...   # override the endpoint
"""

import argparse
import sys

from agents import AGENTS
from harness import BOLD, DIM, RESET, load_env, run_agent, run_selftests


def print_roster() -> None:
    for agent in AGENTS.values():
        print(f"{BOLD}{agent.key:<10}{RESET} {agent.title}")
        print(f"{'':<11}{DIM}{agent.tagline}{RESET}")
        for scenario in agent.scenarios.values():
            print(f"{'':<11}· {scenario.key:<10} {DIM}{scenario.blurb}{RESET}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Xenovia demo agents (Innotecq partner pack)",
        epilog="agents: " + ", ".join(AGENTS) + "  ·  also: list, selftest",
    )
    parser.add_argument("agent", help="agent key, or 'list' / 'selftest'")
    parser.add_argument("scenario", nargs="?", help="scenario key (default: normal)")
    parser.add_argument("--base-url", help="override XENOVIA_BASE_URL for this run")
    parser.add_argument("--api-key", help="override XENOVIA_API_KEY for this run")
    parser.add_argument("--model", help="override XENOVIA_MODEL for this run")
    parser.add_argument("--turns", type=int, default=14, help="max agent turns (default 14)")
    args = parser.parse_args()

    if args.agent == "list":
        print_roster()
        return
    if args.agent == "selftest":
        print("offline selftest of the mock backends (no network, no model):")
        sys.exit(0 if run_selftests(list(AGENTS.values())) else 1)

    agent = AGENTS.get(args.agent)
    if agent is None:
        sys.exit(f"unknown agent '{args.agent}' — try: {', '.join(AGENTS)}, list, selftest")
    scenario = args.scenario or "normal"
    if scenario not in agent.scenarios:
        sys.exit(f"unknown scenario '{scenario}' for {agent.key} — "
                 f"try: {', '.join(agent.scenarios)}")

    env = load_env()
    base_url = args.base_url or env.get("XENOVIA_BASE_URL")
    if not base_url:
        sys.exit("no endpoint configured — set XENOVIA_BASE_URL in .env "
                 "(copy .env.example) or pass --base-url")

    run_agent(
        agent,
        scenario,
        base_url=base_url,
        api_key=args.api_key or env.get("XENOVIA_API_KEY", ""),
        model=args.model or env.get("XENOVIA_MODEL", "claude-sonnet-5"),
        max_turns=args.turns,
    )


if __name__ == "__main__":
    main()
