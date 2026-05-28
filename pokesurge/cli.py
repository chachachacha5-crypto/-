"""Command-line entry point for pokesurge."""
from __future__ import annotations

import argparse
import json
import sys

from . import (
    catalog, dex, jp_catalog, jp_prices, linker, prices,
    snkrdunk, spread, surge,
)
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

    p_dex = sub.add_parser("dex-sync",
                           help="Build the Pokedex name dictionary from PokeAPI (one-time)")
    p_dex.add_argument("--max-id", type=int, default=1025,
                       help="Highest national Pokedex number to fetch (default: 1025)")
    p_dex.add_argument("--delay", type=float, default=0.1,
                       help="Seconds between requests (default: 0.1)")

    p_jp = sub.add_parser("jp-catalog",
                          help="Sync Japanese set & card catalog from TCGdex")
    p_jp.add_argument("--years", type=int, default=5)
    p_jp.add_argument("--deep", action="store_true",
                      help="Also fetch per-card detail (rarity, dexId). Slow.")

    p_link = sub.add_parser("link", help="Match English cards to Japanese candidates")
    p_link.add_argument("--enrich", action="store_true",
                        help="Also (re)populate jp_cards.pokedex_numbers via name match")
    p_link.add_argument("--days-window", type=int, default=180,
                        help="Max release-date distance to consider (default: 180)")
    p_link.add_argument("--top", type=int, default=5,
                        help="Candidates kept per English card (default: 5)")

    p_show = sub.add_parser("linked", help="Show Japanese candidates for one English card")
    p_show.add_argument("en_card_id", help="e.g. sv2-50")
    p_show.add_argument("--json", action="store_true")

    p_jp_imp = sub.add_parser("jp-prices-import",
                              help="Import JP price snapshots from a CSV file")
    p_jp_imp.add_argument("csv_path", help="CSV with header: jp_card_id,price,metric,source,condition,currency,source_url")

    p_snd_add = sub.add_parser("snkrdunk-link",
                               help="Map a JP card to a Snkrdunk product URL")
    p_snd_add.add_argument("jp_card_id")
    p_snd_add.add_argument("url")
    p_snd_add.add_argument("--note", default=None)

    p_snd_fetch = sub.add_parser("snkrdunk-fetch",
                                 help="Fetch prices for all mapped Snkrdunk URLs (low-volume)")
    p_snd_fetch.add_argument("--delay", type=float, default=snkrdunk.DEFAULT_DELAY_SEC,
                             help="Seconds between requests")
    p_snd_fetch.add_argument("--limit", type=int, default=None)

    p_spread = sub.add_parser("spread",
                              help="Rank EN-surging cards still cheap in Japan (arbitrage)")
    p_spread.add_argument("--top", type=int, default=30)
    p_spread.add_argument("--min-surge", type=float, default=0.10,
                          help="Min 30d cardmarket surge ratio (default: 0.10 = +10%%)")
    p_spread.add_argument("--min-spread", type=float, default=0.10,
                          help="Min EN->JPY vs JP price spread (default: 0.10 = +10%%)")
    p_spread.add_argument("--min-eur", type=float, default=2.0,
                          help="Min EN avg1 EUR price floor (default: 2.0)")
    p_spread.add_argument("--eur-jpy", type=float, default=None,
                          help="Override EUR->JPY rate (env: POKESURGE_EUR_JPY)")
    p_spread.add_argument("--all-links", action="store_true",
                          help="Show every candidate link, not only the highest-scored")
    p_spread.add_argument("--json", action="store_true")

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

    if args.cmd == "dex-sync":
        init_db(args.db)
        dex.sync(args.db, max_id=args.max_id, delay=args.delay)
        return 0

    if args.cmd == "jp-catalog":
        init_db(args.db)
        jp_catalog.sync(args.db, years_back=args.years, deep=args.deep)
        return 0

    if args.cmd == "link":
        init_db(args.db)
        if args.enrich:
            linker.enrich_jp_pokedex(args.db)
        linker.link_all(args.db, days_window=args.days_window, top_per_card=args.top)
        return 0

    if args.cmd == "linked":
        rows = linker.show_links_for(args.db, args.en_card_id)
        if args.json:
            print(json.dumps(rows, indent=2, default=str))
        else:
            _print_links(args.en_card_id, rows)
        return 0

    if args.cmd == "jp-prices-import":
        init_db(args.db)
        jp_prices.import_csv(args.db, args.csv_path)
        return 0

    if args.cmd == "snkrdunk-link":
        init_db(args.db)
        snkrdunk.add_link(args.db, args.jp_card_id, args.url, note=args.note)
        print(f"Linked {args.jp_card_id} -> {args.url}")
        return 0

    if args.cmd == "snkrdunk-fetch":
        snkrdunk.fetch_all(args.db, delay=args.delay, limit=args.limit)
        return 0

    if args.cmd == "spread":
        rows = spread.rank_arbitrage(
            args.db, top_n=args.top,
            min_surge_30d=args.min_surge, min_spread=args.min_spread,
            min_en_price_eur=args.min_eur, eur_jpy=args.eur_jpy,
            only_best_link=not args.all_links,
        )
        if args.json:
            print(json.dumps(rows, indent=2, default=str))
        else:
            _print_spread(rows)
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


def _print_links(en_card_id: str, rows: list[dict]) -> None:
    if not rows:
        print(f"No links for {en_card_id}. "
              f"Run `pokesurge dex-sync`, `jp-catalog`, then `link --enrich`.")
        return
    print(f"Candidates for {en_card_id}:")
    print(f"{'Score':>6}  {'JP Set':<14} {'Release':<11} {'#':<6} {'Rarity':<6}  Name  [reason]")
    for r in rows:
        print(
            f"{r['score']:>6.1f}  {r['jp_set_id']:<14} {r['jp_release'] or '?':<11} "
            f"{r['local_id'] or '?':<6} {(r['jp_rarity'] or '?'):<6}  "
            f"{r['jp_name']}  [{r['reason']}]"
        )


def _print_spread(rows: list[dict]) -> None:
    if not rows:
        print("No arbitrage candidates. Need: cardmarket snapshots + card_links + jp_price_snapshots.")
        return
    print(f"{'#':<3} {'Arb':>7} {'Surge30':>8} {'Spread':>8} "
          f"{'EN¥':>7} {'JP¥':>7}  EN Card  ->  JP Card")
    for i, r in enumerate(rows, 1):
        print(
            f"{i:<3} {r['arb_score']:>7.2f} "
            f"{r['surge_30d']*100:>7.1f}% {r['spread']*100:>7.1f}% "
            f"{r['en_price_jpy']:>7.0f} {r['jp_price_jpy']:>7.0f}  "
            f"{r['en_name']} #{r['en_number']} [{r['en_set_name']}] "
            f"-> {r['jp_name']} #{r['jp_local_id']} [{r['jp_set_name']}] "
            f"({r['jp_source']})"
        )


if __name__ == "__main__":
    raise SystemExit(main())
