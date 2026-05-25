from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from . import analyzer
from .exporter import export_csv, export_json
from .rakuten import HOT_GENRES, PERIODS, RakutenClient
from .yahoo import HOT_CATEGORIES, SORT_OPTIONS, YahooClient


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _print_table(rows: list[dict], columns: list[str], limit: int = 30) -> None:
    if not rows:
        print("(結果なし)")
        return
    widths = {c: max(len(c), max((len(str(r.get(c, ""))[:40]) for r in rows[:limit]), default=0)) for c in columns}
    header = " | ".join(c.ljust(widths[c]) for c in columns)
    print(header)
    print("-" * len(header))
    for r in rows[:limit]:
        print(" | ".join(str(r.get(c, ""))[:40].ljust(widths[c]) for c in columns))


def cmd_rakuten(args, env) -> int:
    client = RakutenClient(env["RAKUTEN_APP_ID"])
    items = client.ranking(genre_id=args.genre, period=args.period, page=args.page)
    rows = [it.to_dict() for it in items]
    genre_label = HOT_GENRES.get(args.genre, f"genre={args.genre}")
    print(f"\n[楽天ランキング] {genre_label} / {args.period} / {len(rows)}件\n")
    _print_table(rows, ["rank", "name", "price", "shop_name", "review_count"], limit=args.limit)
    _write_outputs(args, rows, f"rakuten_{args.genre}_{args.period}")
    return 0


def cmd_yahoo(args, env) -> int:
    client = YahooClient(env["YAHOO_APP_ID"])
    items = client.search(
        keyword=args.keyword,
        category_id=args.category,
        sort=args.sort,
        results=args.results,
    )
    rows = [it.to_dict() for it in items]
    label = args.keyword or HOT_CATEGORIES.get(args.category, f"category={args.category}")
    print(f"\n[Yahoo!ショッピング] {label} / sort={args.sort} / {len(rows)}件\n")
    _print_table(rows, ["rank", "name", "price", "shop_name", "review_count"], limit=args.limit)
    suffix = f"yahoo_{args.keyword or args.category}_{args.sort}".replace(" ", "_")
    _write_outputs(args, rows, suffix)
    return 0


def cmd_trends(args, env) -> int:
    rakuten = RakutenClient(env["RAKUTEN_APP_ID"])
    yahoo = YahooClient(env["YAHOO_APP_ID"]) if env.get("YAHOO_APP_ID") else None

    rakuten_rows: list[dict] = []
    for gid in args.genres:
        items = rakuten.ranking(genre_id=gid, period=args.period)
        rakuten_rows.extend(it.to_dict() for it in items)

    yahoo_rows: list[dict] = []
    if yahoo and args.keywords:
        for kw in args.keywords:
            items = yahoo.search(keyword=kw, sort="popular", results=args.results)
            yahoo_rows.extend(it.to_dict() for it in items)

    print(f"\n[トレンド分析] 楽天 {len(rakuten_rows)}件 / Yahoo {len(yahoo_rows)}件\n")

    rakuten_summary = analyzer.summarize(rakuten_rows)
    print("--- 楽天 価格統計 ---")
    print(rakuten_summary["price"])
    print("\n--- 楽天 頻出キーワード TOP15 ---")
    for kw, n in rakuten_summary["top_keywords"]:
        print(f"  {n:>3}  {kw}")

    if yahoo_rows:
        yahoo_summary = analyzer.summarize(yahoo_rows)
        print("\n--- Yahoo 価格統計 ---")
        print(yahoo_summary["price"])
        print("\n--- Yahoo 頻出キーワード TOP15 ---")
        for kw, n in yahoo_summary["top_keywords"]:
            print(f"  {n:>3}  {kw}")

        overlaps = analyzer.cross_platform_overlap(rakuten_rows, yahoo_rows)
        print(f"\n--- 楽天⇔Yahoo クロスマッチ {len(overlaps)}件 (TOP20) ---")
        for m in overlaps[:20]:
            print(
                f"  [{m['match_score']}] {m['rakuten_name'][:30]} / 楽天 ¥{m['rakuten_price']:,} ⇔ "
                f"Yahoo ¥{m['yahoo_price']:,} (差: {m['price_diff']:+,})"
            )

    out_dir = Path(args.out_dir or "data")
    ts = _timestamp()
    if args.format in ("csv", "both"):
        export_csv(rakuten_rows, out_dir / f"trends_rakuten_{ts}.csv")
        if yahoo_rows:
            export_csv(yahoo_rows, out_dir / f"trends_yahoo_{ts}.csv")
    if args.format in ("json", "both"):
        export_json(
            {
                "generated_at": ts,
                "period": args.period,
                "rakuten": {"items": rakuten_rows, "summary": rakuten_summary},
                "yahoo": (
                    {"items": yahoo_rows, "summary": analyzer.summarize(yahoo_rows)}
                    if yahoo_rows
                    else None
                ),
            },
            out_dir / f"trends_{ts}.json",
        )
    print(f"\n出力先: {out_dir}/")
    return 0


def cmd_genres(args, env) -> int:
    print("\n[楽天 主要ジャンル]")
    for gid, name in HOT_GENRES.items():
        print(f"  {gid:>8}  {name}")
    print("\n[Yahoo!ショッピング 主要カテゴリ]")
    for cid, name in HOT_CATEGORIES.items():
        print(f"  {cid:>8}  {name}")
    return 0


def _write_outputs(args, rows: list[dict], suffix: str) -> None:
    if not args.format:
        return
    out_dir = Path(args.out_dir or "data")
    ts = _timestamp()
    if args.format in ("csv", "both"):
        path = export_csv(rows, out_dir / f"{suffix}_{ts}.csv")
        print(f"\nCSV出力: {path}")
    if args.format in ("json", "both"):
        path = export_json(rows, out_dir / f"{suffix}_{ts}.json")
        print(f"JSON出力: {path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trend-research",
        description="楽天 / Yahoo!ショッピングの公式APIを使ったトレンド商品リサーチツール",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("rakuten", help="楽天市場ランキング取得")
    pr.add_argument("--genre", type=int, default=0, help="ジャンルID (0=全体)")
    pr.add_argument("--period", choices=PERIODS, default="realtime")
    pr.add_argument("--page", type=int, default=1)
    pr.add_argument("--limit", type=int, default=30, help="表示件数")
    pr.add_argument("--format", choices=["csv", "json", "both"], default=None)
    pr.add_argument("--out-dir", default="data")
    pr.set_defaults(func=cmd_rakuten)

    py = sub.add_parser("yahoo", help="Yahoo!ショッピング検索/ランキング")
    py.add_argument("--keyword", default=None)
    py.add_argument("--category", type=int, default=None, help="カテゴリID")
    py.add_argument("--sort", choices=list(SORT_OPTIONS.keys()), default="popular")
    py.add_argument("--results", type=int, default=30)
    py.add_argument("--limit", type=int, default=30)
    py.add_argument("--format", choices=["csv", "json", "both"], default=None)
    py.add_argument("--out-dir", default="data")
    py.set_defaults(func=cmd_yahoo)

    pt = sub.add_parser("trends", help="楽天 + Yahoo を横断したトレンド分析")
    pt.add_argument(
        "--genres",
        type=int,
        nargs="+",
        default=[101240, 101205, 101164, 566382],
        help="楽天ジャンルID (複数指定可)",
    )
    pt.add_argument("--keywords", nargs="*", default=[], help="Yahoo検索キーワード (複数指定可)")
    pt.add_argument("--period", choices=PERIODS, default="realtime")
    pt.add_argument("--results", type=int, default=30)
    pt.add_argument("--format", choices=["csv", "json", "both"], default="both")
    pt.add_argument("--out-dir", default="data")
    pt.set_defaults(func=cmd_trends)

    pg = sub.add_parser("genres", help="主要ジャンル/カテゴリID一覧を表示")
    pg.set_defaults(func=cmd_genres)

    return p


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    env = {
        "RAKUTEN_APP_ID": os.getenv("RAKUTEN_APP_ID", ""),
        "YAHOO_APP_ID": os.getenv("YAHOO_APP_ID", ""),
    }
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args, env)
    except ValueError as e:
        print(f"設定エラー: {e}", file=sys.stderr)
        print("→ .env.example を参考に .env を作成してください", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"エラー: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
