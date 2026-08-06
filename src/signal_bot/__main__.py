"""CLI entry: python -m signal_bot serve"""
from __future__ import annotations
import argparse, sys
import uvicorn
from signal_bot.config import get_settings

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="signal-bot", description="Safe Signal Trader")
    sub = parser.add_subparsers(dest="command")
    serve_p = sub.add_parser("serve", help="Start FastAPI health/status server")
    serve_p.add_argument("--host", default=None)
    serve_p.add_argument("--port", type=int, default=None)
    args = parser.parse_args(argv)
    if args.command == "serve" or args.command is None:
        settings = get_settings()
        host = args.host or settings.api_host
        port = args.port or settings.api_port
        uvicorn.run("signal_bot.main:app", host=host, port=port, reload=False, log_level=settings.log_level.lower())
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
