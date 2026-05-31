"""Arbitrage ranking: overseas surge x JP price gap.

For each English card with linked Japanese candidates, we compare the
Cardmarket ``avg1`` (in EUR) — converted to JPY — against the latest
Japanese ``lowest_ask`` snapshot, and weight that gap by the recent
30-day surge. Highest score = best "still cheap in Japan" candidate.
"""
from __future__ import annotations

import os

from .db import connect

DEFAULT_EUR_JPY = 170.0
DEFAULT_USD_JPY = 155.0


def _fx(env_key: str, fallback: float) -> float:
    raw = os.environ.get(env_key)
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return fallback


def rank_arbitrage(
    db_path: str,
    top_n: int = 30,
    min_surge_30d: float = 0.10,
    min_spread: float = 0.10,
    min_en_price_eur: float = 2.0,
    eur_jpy: float | None = None,
    only_best_link: bool = True,
) -> list[dict]:
    """Returns rows sorted by arb_score = surge_30d * spread (descending)."""
    eur_jpy = eur_jpy if eur_jpy is not None else _fx("POKESURGE_EUR_JPY", DEFAULT_EUR_JPY)

    link_filter = ""
    if only_best_link:
        link_filter = """
        AND cl.score = (
            SELECT MAX(score) FROM card_links cl2
             WHERE cl2.en_card_id = cl.en_card_id
        )
        """

    sql = f"""
    WITH cm_latest AS (
        SELECT card_id, metric, price,
               ROW_NUMBER() OVER (PARTITION BY card_id, metric
                                  ORDER BY snapshot_at DESC) AS rn
          FROM price_snapshots
         WHERE source = 'cardmarket'
           AND metric IN ('avg1', 'avg30')
    ),
    en_cm AS (
        SELECT card_id,
               MAX(CASE WHEN metric='avg1'  AND rn=1 THEN price END) AS avg1,
               MAX(CASE WHEN metric='avg30' AND rn=1 THEN price END) AS avg30
          FROM cm_latest
         GROUP BY card_id
    ),
    jp_latest AS (
        SELECT jp_card_id, source, condition, price, snapshot_at, source_url
          FROM (
              SELECT *,
                     ROW_NUMBER() OVER (PARTITION BY jp_card_id
                                        ORDER BY snapshot_at DESC) AS rn
                FROM jp_price_snapshots
               WHERE metric = 'lowest_ask' AND currency = 'JPY'
          )
         WHERE rn = 1
    )
    SELECT c.id    AS en_id,    c.name    AS en_name,
           c.number AS en_number, c.rarity AS en_rarity,
           c.image_small AS en_image,
           s.name  AS en_set_name,
           jp.id   AS jp_id,    jp.name   AS jp_name,
           jp.local_id AS jp_local_id, jp.rarity AS jp_rarity,
           jp.image_url AS jp_image,
           js.name AS jp_set_name,
           cl.score AS link_score, cl.reason AS link_reason,
           en_cm.avg1  AS en_avg1_eur,
           en_cm.avg30 AS en_avg30_eur,
           (en_cm.avg1 - en_cm.avg30) / en_cm.avg30 AS surge_30d,
           en_cm.avg1 * ? AS en_price_jpy,
           jp_latest.source    AS jp_source,
           jp_latest.condition AS jp_condition,
           jp_latest.price     AS jp_price_jpy,
           (en_cm.avg1 * ? - jp_latest.price) / jp_latest.price AS spread,
           ((en_cm.avg1 - en_cm.avg30) / en_cm.avg30)
             * ((en_cm.avg1 * ? - jp_latest.price) / jp_latest.price) AS arb_score,
           c.cardmarket_url, c.tcgplayer_url,
           jp_latest.source_url AS jp_url
      FROM en_cm
      JOIN cards     c  ON c.id  = en_cm.card_id
      JOIN sets      s  ON s.id  = c.set_id
      JOIN card_links cl ON cl.en_card_id = c.id
      JOIN jp_cards  jp ON jp.id = cl.jp_card_id
      JOIN jp_sets   js ON js.id = jp.set_id
      JOIN jp_latest    ON jp_latest.jp_card_id = jp.id
     WHERE en_cm.avg1  > ?
       AND en_cm.avg30 > 0
       AND jp_latest.price > 0
       AND (en_cm.avg1 - en_cm.avg30) / en_cm.avg30 >= ?
       AND (en_cm.avg1 * ? - jp_latest.price) / jp_latest.price >= ?
       {link_filter}
     ORDER BY arb_score DESC
     LIMIT ?
    """

    params = (
        eur_jpy, eur_jpy, eur_jpy,
        min_en_price_eur,
        min_surge_30d,
        eur_jpy, min_spread,
        top_n,
    )
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def fx_rate(currency: str) -> float:
    if currency.upper() == "EUR":
        return _fx("POKESURGE_EUR_JPY", DEFAULT_EUR_JPY)
    if currency.upper() == "USD":
        return _fx("POKESURGE_USD_JPY", DEFAULT_USD_JPY)
    return 1.0
