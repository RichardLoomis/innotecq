#!/usr/bin/env python3
"""CLI: list the standalone agents. Chat with them via the web console (server.py)."""

import sys

from agents import AGENTS


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for agent in AGENTS.values():
            print(f"{agent.key:<10} {agent.title.split(' — ')[0]}")
            print(f"{'':<11}{agent.tagline}")
    else:
        sys.exit(f"unknown command '{cmd}' — try: list")


if __name__ == "__main__":
    main()
