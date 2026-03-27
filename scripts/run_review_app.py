from __future__ import annotations

import argparse

from video_atlas.review import run_review_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local review app for canonical and derived atlas directories.",
    )
    parser.add_argument(
        "--canonical-atlas-dir",
        help="Path to a canonical atlas directory to inspect.",
    )
    parser.add_argument(
        "--derived-atlas-dir",
        help="Path to a derived atlas directory to inspect.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind the local review server to.",
    )
    parser.add_argument(
        "--port",
        default=8765,
        type=int,
        help="Port to bind the local review server to.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    server = run_review_app(
        canonical_atlas_dir=args.canonical_atlas_dir,
        derived_atlas_dir=args.derived_atlas_dir,
        host=args.host,
        port=args.port,
    )
    print(f"VideoAtlas review app running at {server.url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping review app.")
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
