#!/usr/bin/env python3
"""CLI for the demo agents.

    python run_demo.py list        # the four agents
    python run_demo.py selftest    # offline check of every agent's mocked backend

Each agent is its own class (agents/*_agent.py). The web console (server.py) is
the way to actually chat with them; this CLI is for the offline selftests.
"""

import sys

from agents import AGENTS
from agents.base import BOLD, DIM, RESET, run_selftests


def print_roster() -> None:
    for agent in AGENTS.values():
        name = agent.title.split(" — ")[0]
        print(f"{BOLD}{agent.key:<10}{RESET} {name}")
        print(f"{'':<11}{DIM}{agent.tagline}{RESET}")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        print_roster()
    elif cmd == "selftest":
        print("offline selftest of the mocked backends (no network, no model):")
        sys.exit(0 if run_selftests(list(AGENTS.values())) else 1)
    else:
        sys.exit(f"unknown command '{cmd}' — try: list, selftest")


if __name__ == "__main__":
    main()
