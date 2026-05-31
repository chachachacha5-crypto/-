"""Render a self-contained HTML report (surge + spread)."""
from __future__ import annotations

import html
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from . import spread, surge

CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans",
       "Noto Sans JP", "Segoe UI", sans-serif;
       background: #0f1115; color: #e8eaed; margin: 0; padding: 0; }
header { background: #1a1d24; padding: 16px 24px;
         border-bottom: 1px solid #2a2f3a; position: sticky; top: 0; z-index: 10; }
header h1 { margin: 0; font-size: 18px; }
header .meta { color: #9aa0a6; font-size: 12px; margin-top: 4px; }
header nav { margin-top: 8px; }
header nav a { color: #8ab4f8; margin-right: 16px;
               text-decoration: none; font-size: 13px; }
section { padding: 20px 24px; }
section h2 { font-size: 16px; margin: 0 0 4px 0; }
section .sub { color: #9aa0a6; font-size: 12px; margin: 0 0 16px 0; }
.grid { display: grid; gap: 12px;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.card { background: #1a1d24; border: 1px solid #2a2f3a;
        border-radius: 10px; padding: 12px;
        display: flex; gap: 12px; min-width: 0; }
.card img.thumb { width: 80px; height: auto; border-radius: 6px;
                  flex-shrink: 0; background: #0f1115; }
.card .info { flex: 1; min-width: 0; }
.card .name { font-weight: 600; font-size: 14px; margin: 0 0 2px 0;
              overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.card .set { color: #9aa0a6; font-size: 11px; margin: 0 0 6px 0; }
.card .stats { font-size: 12px; line-height: 1.7; }
.card .stats .label { color: #9aa0a6; margin-right: 2px; }
.pos { color: #34a853; font-weight: 600; }
.neg { color: #ea4335; font-weight: 600; }
.card .links { margin-top: 6px; font-size: 11px; }
.card .links a { color: #8ab4f8; margin-right: 10px; text-decoration: none; }
.card .links a:hover { text-decoration: underline; }
.spread-pair { background: #1a1d24; border: 1px solid #2a2f3a;
               border-radius: 10px; padding: 14px; }
.spread-pair .top { display: flex; justify-content: space-between;
                    align-items: flex-start; margin-bottom: 12px; gap: 8px; }
.spread-pair .top .breadcrumb { font-size: 11px; color: #9aa0a6;
                                line-height: 1.5; }
.spread-pair .arb { font-size: 22px; font-weight: 700; color: #fbbc04;
                    line-height: 1; white-space: nowrap; }
.spread-pair .arb .label { font-size: 10px; color: #9aa0a6; font-weight: 400;
                           margin-right: 4px; }
.spread-pair .primary { display: flex; gap: 12px; margin-bottom: 12px; }
.spread-pair .primary img { width: 110px; height: auto; border-radius: 6px;
                            background: #0f1115; flex-shrink: 0; }
.spread-pair .primary .body { flex: 1; min-width: 0; }
.spread-pair .primary .name { font-size: 16px; font-weight: 700;
                              margin-bottom: 2px; overflow: hidden;
                              white-space: nowrap; text-overflow: ellipsis; }
.spread-pair .primary .set  { font-size: 11px; color: #9aa0a6; margin-bottom: 8px; }
.spread-pair .primary .price { font-size: 22px; font-weight: 700; color: #34a853; }
.spread-pair .primary .source { font-size: 11px; color: #9aa0a6;
                                font-weight: 400; margin-left: 6px; }
.spread-pair .reference { display: flex; gap: 8px;
                          background: #14171c; border: 1px solid #2a2f3a;
                          border-radius: 6px; padding: 8px; margin-bottom: 10px; }
.spread-pair .reference img { width: 40px; height: auto; border-radius: 3px;
                              background: #0f1115; flex-shrink: 0; }
.spread-pair .reference .ref-body { flex: 1; min-width: 0; font-size: 11px;
                                    line-height: 1.6; }
.spread-pair .reference .ref-name { font-weight: 600; color: #cfd2d6; }
.spread-pair .reference .ref-meta { color: #9aa0a6; }
.spread-pair .reference .ref-stats { margin-top: 4px; }
.spread-pair .links { display: flex; flex-wrap: wrap; gap: 8px;
                      font-size: 12px; margin-top: 4px; }
.spread-pair .links a { color: #8ab4f8; text-decoration: none; }
.spread-pair .links a.primary-link {
    background: #1a73e8; color: #fff; padding: 6px 12px;
    border-radius: 6px; font-weight: 600;
}
.spread-pair .links a.primary-link:hover { background: #1765cc; }
.spread-pair .links a.ref-link { padding: 6px 0; }
.spread-pair .links a:hover { text-decoration: underline; }
.empty { color: #9aa0a6; font-style: italic; padding: 12px 0; }
@media (max-width: 600px) {
  .grid { grid-template-columns: 1fr; }
}
"""


def _esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _pct(v: float) -> str:
    if v is None:
        return ""
    cls = "pos" if v > 0 else ("neg" if v < 0 else "")
    sign = "+" if v > 0 else ""
    return f'<span class="{cls}">{sign}{v * 100:.1f}%</span>'


def _link(url: str | None, label: str) -> str:
    if not url:
        return ""
    return f'<a href="{_esc(url)}" target="_blank" rel="noopener">{label}</a>'


def _img(url: str | None, klass: str) -> str:
    if not url:
        return f'<div class="{klass}"></div>'
    return f'<img class="{klass}" src="{_esc(url)}" alt="" loading="lazy">'


def _render_surge_card(r: dict) -> str:
    return f"""
    <div class="card">
      {_img(r.get('image_small'), 'thumb')}
      <div class="info">
        <div class="name">{_esc(r.get('name'))} #{_esc(r.get('number'))}</div>
        <div class="set">{_esc(r.get('set_name'))} — {_esc(r.get('rarity'))}</div>
        <div class="stats">
          <div><span class="label">30d</span> {_pct(r.get('surge_30d', 0))}
               &nbsp;<span class="label">7d</span> {_pct(r.get('surge_7d', 0))}</div>
          <div><span class="label">avg1</span> €{r.get('avg1', 0):.2f}
               &nbsp;<span class="label">avg30</span> €{r.get('avg30', 0):.2f}</div>
        </div>
        <div class="links">
          {_link(r.get('cardmarket_url'), 'Cardmarket')}
          {_link(r.get('tcgplayer_url'), 'TCGPlayer')}
        </div>
      </div>
    </div>"""


def _render_spread_pair(r: dict) -> str:
    jp_source = _esc(r.get('jp_source') or '')
    primary_label = "スニダンで見る →" if jp_source == "snkrdunk" else f"{jp_source} で見る →" if jp_source else "JP価格元 →"
    jp_url = r.get('jp_url')
    primary_link_html = (
        f'<a class="primary-link" href="{_esc(jp_url)}" target="_blank" rel="noopener">{primary_label}</a>'
        if jp_url else ""
    )
    ref_links = " &middot; ".join(filter(None, [
        f'<a class="ref-link" href="{_esc(r["cardmarket_url"])}" target="_blank" rel="noopener">Cardmarket</a>'
            if r.get("cardmarket_url") else "",
        f'<a class="ref-link" href="{_esc(r["tcgplayer_url"])}" target="_blank" rel="noopener">TCGPlayer</a>'
            if r.get("tcgplayer_url") else "",
    ]))
    return f"""
    <div class="spread-pair">
      <div class="top">
        <div class="breadcrumb">
          仕入れ候補 &middot; #{_esc(r.get('jp_local_id'))} {_esc(r.get('jp_rarity'))}
        </div>
        <div class="arb"><span class="label">arb</span>{r.get('arb_score', 0):.2f}</div>
      </div>
      <div class="primary">
        {_img(r.get('jp_image'), 'jp-thumb')}
        <div class="body">
          <div class="name">{_esc(r.get('jp_name'))}</div>
          <div class="set">{_esc(r.get('jp_set_name'))}</div>
          <div class="price">¥{r.get('jp_price_jpy', 0):,.0f}
            <span class="source">({jp_source or '出典不明'})</span>
          </div>
        </div>
      </div>
      <div class="reference">
        {_img(r.get('en_image'), 'en-thumb')}
        <div class="ref-body">
          <div><span class="ref-meta">海外参考:</span>
               <span class="ref-name">{_esc(r.get('en_name'))}</span>
               <span class="ref-meta">({_esc(r.get('en_set_name'))})</span></div>
          <div class="ref-meta">avg1 €{r.get('en_avg1_eur', 0):.2f}
               → 換算 ¥{r.get('en_price_jpy', 0):,.0f}</div>
          <div class="ref-stats">surge 30d {_pct(r.get('surge_30d', 0))}
               &middot; spread {_pct(r.get('spread', 0))}</div>
        </div>
      </div>
      <div class="links">
        {primary_link_html}
        {ref_links}
      </div>
    </div>"""


def render_html(
    db_path: str,
    *,
    top: int = 50,
    min_surge: float = 0.10,
    min_spread: float = 0.10,
    min_eur: float = 2.0,
    eur_jpy: float | None = None,
    surge_window: str = "30d",
) -> str:
    surge_rows = surge.rank_cardmarket_trend(
        db_path, top_n=top, min_price=max(2.0, min_eur), window=surge_window,
    )
    spread_rows = spread.rank_arbitrage(
        db_path, top_n=top,
        min_surge_30d=min_surge, min_spread=min_spread,
        min_en_price_eur=min_eur, eur_jpy=eur_jpy,
    )

    surge_html = (
        '<div class="grid">' + "".join(_render_surge_card(r) for r in surge_rows) + "</div>"
        if surge_rows
        else '<div class="empty">No surge data yet — run `pokesurge snapshot`.</div>'
    )
    spread_html = (
        '<div class="grid">' + "".join(_render_spread_pair(r) for r in spread_rows) + "</div>"
        if spread_rows
        else '<div class="empty">No spread data yet — needs card_links + jp_price_snapshots.</div>'
    )

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pokesurge report</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>pokesurge report</h1>
  <div class="meta">generated {generated} &middot;
    surge: {len(surge_rows)} cards &middot; spread: {len(spread_rows)} pairs</div>
  <nav>
    <a href="#spread">💴 仕入れ候補 (Spread)</a>
    <a href="#surge">🔥 海外サージ (Surge)</a>
  </nav>
</header>
<section id="spread">
  <h2>💴 仕入れ候補 — 海外サージ × 日本まだ安い</h2>
  <p class="sub">arb_score = surge_30d × spread &middot;
    min_surge={min_surge:+.0%} min_spread={min_spread:+.0%} min_eur=€{min_eur:.0f}</p>
  {spread_html}
</section>
<section id="surge">
  <h2>🔥 海外サージ — Cardmarket avg1 vs avg{surge_window[:-1]}</h2>
  <p class="sub">{surge_window} 上昇率順 &middot; min €{max(2.0, min_eur):.0f}</p>
  {surge_html}
</section>
</body>
</html>
"""


def write_report(
    db_path: str,
    out_path: str,
    *,
    open_browser: bool = False,
    **kwargs,
) -> str:
    html_text = render_html(db_path, **kwargs)
    path = Path(out_path).resolve()
    path.write_text(html_text, encoding="utf-8")
    if open_browser:
        webbrowser.open(path.as_uri())
    return str(path)
