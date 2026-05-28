"""Rank surging cards.

Two strategies:

- ``cardmarket`` uses Cardmarket's built-in ``avg1`` / ``avg7`` / ``avg30``
  fields from the latest snapshot. Works from a single snapshot — useful on
  day one before we've built our own history.
- ``local`` compares earliest vs latest TCGPlayer market price within a
  rolling window of locally-stored snapshots. Becomes useful once a few
  daily snapshots have accumulated.
"""
from __future__ import annotations

from .db import connect


def rank_cardmarket_trend(
    db_path: str,
    top_n: int = 30,
    min_price: float = 1.0,
    window: str = "30d",
) -> list[dict]:
    """Surge proxy from Cardmarket avg1 vs avg7 / avg30 in the latest snapshot."""
    surge_expr = {
        "7d": "(avg1 - avg7) / avg7",
        "30d": "(avg1 - avg30) / avg30",
    }[window]

    sql = f"""
    WITH latest AS (
        SELECT card_id, metric, price,
               ROW_NUMBER() OVER (PARTITION BY card_id, metric
                                  ORDER BY snapshot_at DESC) AS rn
          FROM price_snapshots
         WHERE source = 'cardmarket'
           AND metric IN ('avg1', 'avg7', 'avg30')
    ),
    pivoted AS (
        SELECT card_id,
               MAX(CASE WHEN metric = 'avg1'  AND rn = 1 THEN price END) AS avg1,
               MAX(CASE WHEN metric = 'avg7'  AND rn = 1 THEN price END) AS avg7,
               MAX(CASE WHEN metric = 'avg30' AND rn = 1 THEN price END) AS avg30
          FROM latest
         GROUP BY card_id
    )
    SELECT c.id, c.name, c.number, c.rarity,
           s.name AS set_name, s.release_date,
           p.avg1, p.avg7, p.avg30,
           (p.avg1 - p.avg7)  / p.avg7  AS surge_7d,
           (p.avg1 - p.avg30) / p.avg30 AS surge_30d,
           c.cardmarket_url, c.tcgplayer_url, c.image_small
      FROM pivoted p
      JOIN cards c ON c.id = p.card_id
      JOIN sets  s ON s.id = c.set_id
     WHERE p.avg1  IS NOT NULL
       AND p.avg7  IS NOT NULL AND p.avg7  > 0
       AND p.avg30 IS NOT NULL AND p.avg30 > 0
       AND p.avg30 >= ?
     ORDER BY {surge_expr} DESC
     LIMIT ?
    """
    with connect(db_path) as conn:
        rows = conn.execute(sql, (min_price, top_n)).fetchall()
    return [dict(r) for r in rows]


def rank_local_history(
    db_path: str,
    top_n: int = 30,
    window_days: int = 7,
    min_price: float = 1.0,
) -> list[dict]:
    """Earliest vs latest TCGPlayer market price within the rolling window."""
    sql = """
    WITH win AS (
        SELECT card_id, variant, price, snapshot_at
          FROM price_snapshots
         WHERE source = 'tcgplayer' AND metric = 'market'
           AND snapshot_at >= datetime('now', ?)
    ),
    bookends AS (
        SELECT card_id, variant,
               FIRST_VALUE(price) OVER w_asc  AS old_price,
               FIRST_VALUE(price) OVER w_desc AS new_price,
               COUNT(*)           OVER w_asc  AS n_points
          FROM win
        WINDOW
          w_asc  AS (PARTITION BY card_id, variant ORDER BY snapshot_at ASC
                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),
          w_desc AS (PARTITION BY card_id, variant ORDER BY snapshot_at DESC
                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    ),
    dedup AS (
        SELECT DISTINCT card_id, variant, old_price, new_price, n_points
          FROM bookends
    )
    SELECT c.id, c.name, c.number, c.rarity,
           s.name AS set_name, s.release_date,
           d.variant, d.old_price, d.new_price, d.n_points,
           (d.new_price - d.old_price) / d.old_price AS surge,
           c.tcgplayer_url, c.cardmarket_url, c.image_small
      FROM dedup d
      JOIN cards c ON c.id = d.card_id
      JOIN sets  s ON s.id = c.set_id
     WHERE d.n_points >= 2
       AND d.old_price >= ?
       AND d.old_price > 0
     ORDER BY surge DESC
     LIMIT ?
    """
    with connect(db_path) as conn:
        rows = conn.execute(sql, (f"-{window_days} days", min_price, top_n)).fetchall()
    return [dict(r) for r in rows]
