"use strict";

const FEE_FIELDS = [
  "usd_jpy",
  "ebay_fvf_percent",
  "ebay_fixed_fee_usd",
  "intl_fee_percent",
  "payout_fx_percent",
  "ad_fee_percent",
];

const $ = (id) => document.getElementById(id);
const yen = (n) => "¥" + Math.round(n).toLocaleString("ja-JP");

// メモリ上の候補行。{title, ebay_price_usd, mercari_price_jpy, ...}
let rows = [];

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

function feeProfile() {
  const f = {};
  for (const k of FEE_FIELDS) f[k] = parseFloat($(k).value) || 0;
  return f;
}

async function init() {
  try {
    const health = await api("/api/health");
    const badge = $("mode-badge");
    if (health.mode === "ebay_api") {
      badge.textContent = "eBay API 接続中";
      badge.classList.add("api");
    } else {
      badge.textContent = "サンプルモード (eBay APIキー未設定)";
      badge.classList.add("sample");
    }
  } catch (e) {
    $("mode-badge").textContent = "サーバ未接続";
  }

  try {
    const { categories } = await api("/api/categories");
    const sel = $("category");
    for (const [id, name] of Object.entries(categories)) {
      const opt = document.createElement("option");
      opt.value = id;
      opt.textContent = name;
      sel.appendChild(opt);
    }
  } catch (e) {}

  try {
    const defaults = await api("/api/defaults");
    for (const k of FEE_FIELDS) if (defaults[k] != null) $(k).value = defaults[k];
  } catch (e) {}

  $("search-btn").addEventListener("click", doSearch);
  $("query").addEventListener("keydown", (e) => e.key === "Enter" && doSearch());
  $("calc-btn").addEventListener("click", calculate);
  $("csv-file").addEventListener("change", importCsv);
}

async function doSearch() {
  const q = $("query").value.trim();
  if (!q) return setStatus("キーワードを入力してください。");
  setStatus("検索中…");
  $("search-btn").disabled = true;
  try {
    const cat = $("category").value;
    const data = await api(`/api/search?q=${encodeURIComponent(q)}&category_id=${cat}&limit=25`);
    const domShip = parseFloat($("default_dom_ship").value) || 0;
    const intlShip = parseFloat($("default_intl_ship").value) || 0;
    rows = data.items.map((it) => ({
      title: it.title,
      url: it.url,
      is_sample: it.is_sample,
      condition: it.condition,
      ebay_price_usd: it.price_usd || 0,
      mercari_price_jpy: 0,
      mercari_shipping_jpy: domShip,
      intl_shipping_jpy: intlShip,
      result: null,
    }));
    renderRows();
    const src = data.source === "sample" ? "（サンプルデータ）" : "";
    setStatus(`${data.count} 件ヒット ${src}。メルカリ仕入れ価格を入力して「利益を一括計算」を押してください。`);
  } catch (e) {
    setStatus("検索に失敗しました: " + e.message);
  } finally {
    $("search-btn").disabled = false;
  }
}

async function importCsv(ev) {
  const file = ev.target.files[0];
  if (!file) return;
  setStatus("CSV 取込中…");
  const form = new FormData();
  form.append("file", file);
  try {
    const data = await api("/api/import/mercari-csv", { method: "POST", body: form });
    const domShip = parseFloat($("default_dom_ship").value) || 0;
    const intlShip = parseFloat($("default_intl_ship").value) || 0;
    rows = data.rows.map((r) => ({
      title: r.title,
      url: null,
      is_sample: false,
      ebay_price_usd: r.ebay_price_usd || 0,
      mercari_price_jpy: r.mercari_price_jpy || 0,
      mercari_shipping_jpy: r.mercari_shipping_jpy || domShip,
      intl_shipping_jpy: r.intl_shipping_jpy || intlShip,
      result: null,
    }));
    renderRows();
    setStatus(`${data.count} 行を取り込みました。`);
  } catch (e) {
    setStatus("CSV 取込に失敗しました: " + e.message);
  } finally {
    ev.target.value = "";
  }
}

async function calculate() {
  if (!rows.length) return setStatus("先に検索かCSV取込をしてください。");
  syncInputsToRows();
  const fees = feeProfile();
  setStatus("計算中…");
  try {
    const payload = {
      items: rows.map((r) => ({
        title: r.title,
        ebay_price_usd: r.ebay_price_usd,
        mercari_price_jpy: r.mercari_price_jpy,
        mercari_shipping_jpy: r.mercari_shipping_jpy,
        intl_shipping_jpy: r.intl_shipping_jpy,
        packaging_jpy: 0,
        fees,
      })),
    };
    const results = await api("/api/profit/batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    rows.forEach((r, i) => (r.result = results[i]));
    // 利益が大きい順に並べ替え
    rows.sort((a, b) => (b.result?.profit_jpy ?? -1e9) - (a.result?.profit_jpy ?? -1e9));
    renderRows();
    const profitable = results.filter((r) => r.is_profitable).length;
    setStatus(`計算完了。利益が出る候補: ${profitable} / ${results.length} 件（利益の大きい順に並べ替え済み）。`);
  } catch (e) {
    setStatus("計算に失敗しました: " + e.message);
  }
}

// テーブル上の入力値を rows に反映
function syncInputsToRows() {
  document.querySelectorAll("#results-body tr[data-idx]").forEach((tr) => {
    const i = Number(tr.dataset.idx);
    rows[i].ebay_price_usd = parseFloat(tr.querySelector(".in-ebay").value) || 0;
    rows[i].mercari_price_jpy = parseFloat(tr.querySelector(".in-mercari").value) || 0;
    rows[i].mercari_shipping_jpy = parseFloat(tr.querySelector(".in-dom").value) || 0;
    rows[i].intl_shipping_jpy = parseFloat(tr.querySelector(".in-intl").value) || 0;
  });
}

function renderRows() {
  const body = $("results-body");
  if (!rows.length) {
    body.innerHTML = '<tr class="empty"><td colspan="10">候補がありません。</td></tr>';
    return;
  }
  body.innerHTML = "";
  rows.forEach((r, i) => {
    const res = r.result;
    const tr = document.createElement("tr");
    tr.dataset.idx = i;
    if (res) tr.classList.add(res.is_profitable ? "profit-yes" : "profit-no");

    const titleHtml = r.url
      ? `<a href="${r.url}" target="_blank" rel="noopener">${escapeHtml(r.title)}</a>`
      : escapeHtml(r.title);
    const sampleTag = r.is_sample ? '<span class="sample-tag">sample</span>' : "";

    tr.innerHTML = `
      <td class="title-cell">${titleHtml}${sampleTag}</td>
      <td><input class="in-ebay" type="number" step="0.01" value="${r.ebay_price_usd}"></td>
      <td><input class="in-mercari" type="number" step="1" value="${r.mercari_price_jpy}"></td>
      <td><input class="in-dom" type="number" step="1" value="${r.mercari_shipping_jpy}"></td>
      <td><input class="in-intl" type="number" step="1" value="${r.intl_shipping_jpy}"></td>
      <td>${res ? yen(res.net_revenue_jpy) : "—"}</td>
      <td>${res ? yen(res.total_cost_jpy) : "—"}</td>
      <td class="profit-val">${res ? yen(res.profit_jpy) : "—"}</td>
      <td>${res ? res.profit_margin_percent + "%" : "—"}</td>
      <td>${res ? res.roi_percent + "%" : "—"}</td>`;
    body.appendChild(tr);
  });
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function setStatus(msg) {
  $("status").textContent = msg;
}

init();
