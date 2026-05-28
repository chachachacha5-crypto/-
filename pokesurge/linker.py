"""Link English (pokemontcg.io) cards to Japanese (TCGdex) cards.

Bridge: National Pokedex number, which appears on both sides — directly on
the English side as ``nationalPokedexNumbers``, and on the Japanese side
inferred from a name-prefix match against the PokeAPI-sourced
``pokemon_names`` dictionary.

Scoring: pokedex match is mandatory (no link without it). Release-date
proximity and rarity-tier agreement are bonuses.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone

from .db import connect


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_rarity_en(rarity: str | None) -> str:
    if not rarity:
        return "unknown"
    r = rarity.lower()
    if "special illustration" in r:           return "sar"
    if "illustration rare" in r:              return "ar"
    if "hyper" in r:                          return "hr"
    if "rainbow" in r or "secret" in r:       return "sr"
    if "shiny" in r:                          return "shiny"
    if "ultra" in r:                          return "ultra"
    if "double rare" in r:                    return "ex"
    if any(t in r for t in (" vmax", " vstar", " v ", " v-", " ex", " gx")):
        return "ex"
    if "holo" in r:                           return "holo"
    if r == "rare":                           return "rare"
    if r == "uncommon":                       return "uncommon"
    if r == "common":                         return "common"
    return "unknown"


def _normalize_rarity_jp(rarity: str | None) -> str:
    if not rarity:
        return "unknown"
    r = rarity.strip().upper()
    return {
        "C":   "common",
        "U":   "uncommon",
        "R":   "rare",
        "RR":  "ex",
        "RRR": "ex",
        "SR":  "ultra",
        "SAR": "sar",
        "AR":  "ar",
        "UR":  "hr",
        "HR":  "hr",
        "S":   "shiny",
        "K":   "character",
    }.get(r, "unknown")


def enrich_jp_pokedex(db_path: str, verbose: bool = True) -> int:
    """Populate jp_cards.pokedex_numbers by name-prefix match.

    Tries longest pokemon_name first so 'ニドリーノ' beats 'ニドラン'.
    """
    updated = 0
    with connect(db_path) as conn:
        names = conn.execute(
            """SELECT pokedex_number, name_ja FROM pokemon_names
                WHERE name_ja IS NOT NULL AND name_ja <> ''
                ORDER BY LENGTH(name_ja) DESC"""
        ).fetchall()
        if not names:
            if verbose:
                print("pokemon_names is empty — run `pokesurge dex-sync` first.")
            return 0

        targets = conn.execute(
            """SELECT id, name FROM jp_cards
                WHERE (pokedex_numbers IS NULL OR pokedex_numbers = '')
                  AND name IS NOT NULL"""
        ).fetchall()

        for jp in targets:
            jp_name = jp["name"]
            for n in names:
                if jp_name.startswith(n["name_ja"]):
                    conn.execute(
                        "UPDATE jp_cards SET pokedex_numbers = ? WHERE id = ?",
                        (str(n["pokedex_number"]), jp["id"]),
                    )
                    updated += 1
                    break
        conn.commit()
    if verbose:
        print(f"Enriched {updated} jp_cards with pokedex_numbers")
    return updated


def link_all(
    db_path: str,
    days_window: int = 180,
    top_per_card: int = 5,
    verbose: bool = True,
) -> int:
    """For each English card with a pokedex#, write up to ``top_per_card``
    Japanese candidates into card_links."""
    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = 0
    with connect(db_path) as conn:
        jp_index: dict[int, list[dict]] = defaultdict(list)
        for row in conn.execute(
            """SELECT jp.id, jp.set_id, jp.rarity, jp.pokedex_numbers, jp.name,
                      s.release_date
                 FROM jp_cards jp
                 JOIN jp_sets s ON s.id = jp.set_id
                WHERE jp.pokedex_numbers IS NOT NULL AND jp.pokedex_numbers <> ''"""
        ):
            d = dict(row)
            for raw in (d["pokedex_numbers"] or "").split(","):
                if not raw:
                    continue
                try:
                    jp_index[int(raw)].append(d)
                except ValueError:
                    continue

        if not jp_index:
            if verbose:
                print("No JP cards with pokedex_numbers yet. "
                      "Run `pokesurge link --enrich` after dex-sync + jp-catalog.")
            return 0

        en_rows = conn.execute(
            """SELECT c.id, c.name, c.rarity, c.pokedex_numbers, s.release_date
                 FROM cards c
                 JOIN sets s ON s.id = c.set_id
                WHERE c.pokedex_numbers IS NOT NULL AND c.pokedex_numbers <> ''"""
        ).fetchall()

        # Clear stale links first so deletions in the source data propagate.
        conn.execute("DELETE FROM card_links")

        for en in en_rows:
            en_dex = {int(n) for n in en["pokedex_numbers"].split(",") if n.isdigit()}
            en_rar = _normalize_rarity_en(en["rarity"])
            en_date = _parse_date(en["release_date"])

            seen: set[str] = set()
            scored: list[tuple[str, float, str]] = []
            for n in en_dex:
                for jp in jp_index.get(n, ()):
                    if jp["id"] in seen:
                        continue
                    seen.add(jp["id"])
                    jp_rar = _normalize_rarity_jp(jp["rarity"])
                    jp_date = _parse_date(jp["release_date"])
                    if en_date and jp_date:
                        days_diff = abs((en_date - jp_date).days)
                    else:
                        days_diff = 10_000
                    if days_diff > days_window:
                        continue
                    score = 10.0
                    reasons = [f"dex={n}"]
                    if days_diff <= 60:
                        score += 5; reasons.append("date<=60d")
                    elif days_diff <= 180:
                        score += 3; reasons.append("date<=180d")
                    elif days_diff <= 365:
                        score += 1; reasons.append("date<=365d")
                    if en_rar != "unknown" and jp_rar != "unknown":
                        if en_rar == jp_rar:
                            score += 4; reasons.append(f"rar={en_rar}")
                        else:
                            reasons.append(f"rar:{en_rar}!={jp_rar}")
                    scored.append((jp["id"], score, ",".join(reasons)))

            scored.sort(key=lambda x: x[1], reverse=True)
            for jp_id, score, reason in scored[:top_per_card]:
                conn.execute(
                    """INSERT OR REPLACE INTO card_links
                       (en_card_id, jp_card_id, score, reason, linked_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (en["id"], jp_id, score, reason, now_iso),
                )
                inserted += 1
        conn.commit()

    if verbose:
        print(f"Wrote {inserted} card_links rows")
    return inserted


def show_links_for(db_path: str, en_card_id: str) -> list[dict]:
    sql = """
    SELECT cl.score, cl.reason,
           jp.id AS jp_id, jp.name AS jp_name, jp.local_id, jp.rarity AS jp_rarity,
           js.id AS jp_set_id, js.name AS jp_set_name, js.release_date AS jp_release
      FROM card_links cl
      JOIN jp_cards jp ON jp.id = cl.jp_card_id
      JOIN jp_sets  js ON js.id = jp.set_id
     WHERE cl.en_card_id = ?
     ORDER BY cl.score DESC, js.release_date DESC
    """
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (en_card_id,)).fetchall()]
