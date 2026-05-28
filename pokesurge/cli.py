"""Command-line entry point for pokesurge."""
from __future__ import annotations

import argparse
import json
import sys

from . import catalog, prices, surge
from .db import DEFAULT_DB, init_db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pokesurge",
        description="Detect Pokemon cards surging on overseas markets (TCGPlayer / Cardmarket).",
    )
    parser.add_argument("--db", default=DEFAULT_DB, help=f"SQLite path (default: {DEFAULT_DB})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the SQLite database")

    p_cat = sub.add_parser("catalog", help="Sync set & card catalog from pokemontcg.io")
    p_cat.add_argument("--years", type=int, default=5,
                       help="Only include sets released in the last N years (default: 5)")

    p_snap = sub.add_parser("snapshot", help="Snapshot current prices into the time-series table")
    p_snap.add_argument("--set", dest="set_id", default=None,
                        help="Only snapshot one set (default: all synced sets)")

    p_surge = sub.add_parser("surge", help="Rank top surging cards")
    p_surge.add_argument("--source", choices=["cardmarket", "local"], default="cardmarket",
                         help="cardmarket: use avg1/avg7/avg30 from latest snapshot (works day 1). "
                              "local: compare snapshots in our own DB (needs >=2 snapshots).")
    p_surge.add_argument("--window", default="30d",
                         help="cardmarket: '7d' or '30d' (default 30d). "
                              "local: integer days (default 7).")
    p_surge.add_argument("--top", type=int, default=30)
    p_surge.add_argument("--min-price", type=float, default=1.0,
                         help="Minimum baseline price to filter out near-zero noise (default 1.0)")
    p_surge.add_argument("--json", action="store_true", help="Emit raw JSON")

    args = parser.parse_args(argv)

    if args.cmd == "init":
        init_db(args.db)
        print(f"Initialized {args.db}")
        return 0

    if args.cmd == "catalog":
        init_db(args.db)
        catalog.sync(args.db, years_back=args.years)
        return 0

    if args.cmd == "snapshot":
        prices.snapshot(args.db, set_id=args.set_id)
        return 0

    if args.cmd == "surge":
        if args.source == "cardmarket":
            window = args.window if args.window in {"7d", "30d"} else "30d"
            rows = surge.rank_cardmarket_trend(
                args.db, top_n=args.top, min_price=args.min_price, window=window,
            )
        else:
            try:
                window_days = int(args.window.rstrip("d"))
            except ValueError:
                print(f"Invalid --window for local source: {args.window!r}", file=sys.stderr)
                return 2
            rows = surge.rank_local_history(
                args.db, top_n=args.top, window_days=window_days, min_price=args.min_price,
            )
        if args.json:
            print(json.dumps(rows, indent=2, default=str))
        else:
            _print_table(rows, args.source)
        return 0

    return 1


def _print_table(rows: list[dict], source: str) -> None:
    if not rows:
        print("No results yet. Run `pokesurge catalog` then `pokesurge snapshot` first.")
        return
    if source == "cardmarket":
        print(f"{'#':<3} {'Surge30d':>9} {'Surge7d':>8} {'avg1':>7} {'avg30':>7}  Card")
        for i, r in enumerate(rows, 1):
            print(
                f"{i:<3} {r['surge_30d']*100:>8.1f}% {r['surge_7d']*100:>7.1f}% "
                f"{r['avg1']:>7.2f} {r['avg30']:>7.2f}  "
                f"{r['name']} #{r['number']} [{r['set_name']}]"
            )
    else:
        print(f"{'#':<3} {'Surge':>7} {'Old':>7} {'New':>7} {'n':>3} {'Variant':<18}  Card")
        for i, r in enumerate(rows, 1):
            print(
                f"{i:<3} {r['surge']*100:>6.1f}% {r['old_price']:>7.2f} {r['new_price']:>7.2f} "
                f"{r['n_points']:>3} {r['variant']:<18}  "
                f"{r['name']} #{r['number']} [{r['set_name']}]"
            )


if __name__ == "__main__":
    raise SystemExit(main())
