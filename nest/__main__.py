# Entry point: uv run nest (not yet active — nest rewrite pending)

import argparse
import os


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Omni Lilith — Nest agent")
    parser.add_argument(
        "--model",
        default=os.environ.get("LILITH_MODEL", "claude-opus-4-6"),
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    from nest.agent import start_repl
    start_repl(model=args.model, verbose=args.verbose)


if __name__ == "__main__":
    main()
