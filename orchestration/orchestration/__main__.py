"""python -m orchestration worker"""

from __future__ import annotations

import argparse

from orchestration.redis_worker import main as worker_main


def main() -> None:
    p = argparse.ArgumentParser(description="PQRS orchestration")
    p.add_argument("command", choices=["worker"], help="subcomando")
    args = p.parse_args()
    if args.command == "worker":
        worker_main()


if __name__ == "__main__":
    main()
