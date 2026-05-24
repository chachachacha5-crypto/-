import { useState } from "react";

const SYSTEM_PROMPT = `あなたはアニメグッズの海外需要を分析する専門家です。
ユーザーが入力した商品情報を元に、以下の4軸で需要スコアを算出してください。
eBayの落札実績データが提供された場合は、それを最優先の根拠として分析に活用してください。

必ずJSON形式のみで返答してください（マークダウン不要）：
{
  "totalScore": 0〜100の整数,
  "axes": [
    {"name": "海外ファン熱量", "score": 0〜25, "max": 25, "reason": "短い理由"},
    {"name": "入手困難度",     "score": 0〜25, "max": 25, "reason": "短い理由"},
    {"name": "転売差益ポテンシャル", "score": 0〜25, "max": 25, "reason": "短い理由"},
    {"name": "需要持続性",     "score": 0〜25, "max": 25, "reason": "短い理由"}
  ],
  "verdict": "BUY" | "WATCH" | "SKIP",
  "estimatedResaleMultiplier": "例: 2.5x〜4x",
  "targetMarkets": ["市場名1", "市場名2"],
  "riskNote": "リスクの簡潔な説明",
  "quickTip": "仕入れ・販売で差をつける具体的なアドバイス1文"
}`;

const PRESETS = [
  { label: "ワンピース 限定フィギュア", value: "ワンピース ジャンプフェスタ限定 ルフィ フィギュア 2024 会場販売のみ" },
  { label: "鬼滅 コラボカフェグッズ", value: "鬼滅の刃 コラボカフェ限定 缶バッジセット 炭治郎 全5種" },
  { label: "呪術廻戦 原画展グッズ", value: "呪術廻戦 原画展限定 アクリルスタンド 五条悟 全国5会場限定" },
];

const VERDICT_CONFIG = {
  BUY:   { label: "仕入れ推奨", color: "#00ff9d", bg: "rgba(0,255,157,0.12)",  border: "rgba(0,255,157,0.4)"  },
  WATCH: { label: "様子見",     color: "#ffcc00", bg: "rgba(255,204,0,0.10)",  border: "rgba(255,204,0,0.4)"  },
  SKIP:  { label: "見送り",     color: "#ff4466", bg: "rgba(255,68,102,0.10)", border: "rgba(255,68,102,0.4)" },
};

const styles = {
  app: {
    minHeight: "100vh",
    backgroundColor: "#0a0a0f",
    color: "#e0e0e0",
    fontFamily: "'Courier New', 'Lucida Console', monospace",
    padding: "40px 20px",
  },
  container: {
    maxWidth: "720px",
    margin: "0 auto",
  },
  header: {
    textAlign: "center",
    marginBottom: "40px",
  },
  headerTitle: {
    fontSize: "22px",
    letterSpacing: "4px",
    color: "#7755cc",
    margin: "0 0 8px 0",
    textTransform: "uppercase",
  },
  headerSub: {
    fontSize: "11px",
    letterSpacing: "3px",
    color: "rgba(255,255,255,0.3)",
    margin: 0,
    textTransform: "uppercase",
  },
  section: {
    marginBottom: "24px",
  },
  label: {
    display: "block",
    fontSize: "11px",
    letterSpacing: "2px",
    color: "rgba(255,255,255,0.4)",
    textTransform: "uppercase",
    marginBottom: "8px",
  },
  input: {
    width: "100%",
    backgroundColor: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "4px",
    color: "#e0e0e0",
    fontFamily: "'Courier New', 'Lucida Console', monospace",
    fontSize: "14px",
    padding: "12px 14px",
    boxSizing: "border-box",
    outline: "none",
  },
  textarea: {
    width: "100%",
    backgroundColor: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "4px",
    color: "#e0e0e0",
    fontFamily: "'Courier New', 'Lucida Console', monospace",
    fontSize: "14px",
    padding: "12px 14px",
    boxSizing: "border-box",
    outline: "none",
    resize: "vertical",
    minHeight: "100px",
  },
  presetRow: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
  },
  presetBtn: {
    backgroundColor: "rgba(119,85,204,0.12)",
    border: "1px solid rgba(119,85,204,0.3)",
    borderRadius: "3px",
    color: "#9977ee",
    fontFamily: "'Courier New', 'Lucida Console', monospace",
    fontSize: "11px",
    padding: "6px 12px",
    cursor: "pointer",
    letterSpacing: "1px",
  },
  analyzeBtn: {
    width: "100%",
    backgroundColor: "rgba(119,85,204,0.15)",
    border: "1px solid rgba(119,85,204,0.5)",
    borderRadius: "4px",
    color: "#aa88ff",
    fontFamily: "'Courier New', 'Lucida Console', monospace",
    fontSize: "14px",
    letterSpacing: "3px",
    padding: "14px",
    cursor: "pointer",
    textTransform: "uppercase",
  },
  error: {
    backgroundColor: "rgba(255,68,102,0.1)",
    border: "1px solid rgba(255,68,102,0.3)",
    borderRadius: "4px",
    color: "#ff4466",
    fontSize: "13px",
    padding: "12px 14px",
    marginBottom: "24px",
  },
  resultArea: {
    animation: "fadeIn 0.5s ease",
  },
  verdictBanner: {
    borderRadius: "6px",
    padding: "24px",
    marginBottom: "20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "12px",
  },
  verdictLabel: {
    fontSize: "28px",
    fontWeight: "bold",
    letterSpacing: "4px",
    textTransform: "uppercase",
  },
  verdictScoreNum: {
    fontSize: "52px",
    fontWeight: "bold",
    lineHeight: 1,
  },
  verdictScoreLabel: {
    fontSize: "11px",
    letterSpacing: "2px",
    opacity: 0.6,
    textTransform: "uppercase",
  },
  axesSection: {
    marginBottom: "20px",
  },
  sectionTitle: {
    fontSize: "11px",
    letterSpacing: "3px",
    color: "rgba(255,255,255,0.3)",
    textTransform: "uppercase",
    marginBottom: "12px",
  },
  axisRow: {
    marginBottom: "14px",
  },
  axisHeader: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: "6px",
  },
  axisName: {
    fontSize: "13px",
    color: "rgba(255,255,255,0.8)",
  },
  axisScore: {
    fontSize: "13px",
    fontWeight: "bold",
  },
  axisBarBg: {
    height: "6px",
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: "3px",
    overflow: "hidden",
    marginBottom: "6px",
  },
  axisReason: {
    fontSize: "11px",
    color: "rgba(255,255,255,0.4)",
    letterSpacing: "0.5px",
  },
  grid2col: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
    marginBottom: "20px",
  },
  cell: {
    backgroundColor: "rgba(255,255,255,0.02)",
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: "4px",
    padding: "14px",
  },
  cellLabel: {
    fontSize: "10px",
    letterSpacing: "2px",
    color: "rgba(255,255,255,0.3)",
    textTransform: "uppercase",
    marginBottom: "6px",
  },
  cellValue: {
    fontSize: "16px",
    fontWeight: "bold",
  },
  riskBox: {
    backgroundColor: "rgba(255,68,102,0.06)",
    border: "1px solid rgba(255,68,102,0.2)",
    borderRadius: "4px",
    padding: "14px",
    marginBottom: "12px",
  },
  riskLabel: {
    fontSize: "10px",
    letterSpacing: "2px",
    color: "rgba(255,68,102,0.6)",
    textTransform: "uppercase",
    marginBottom: "6px",
  },
  riskText: {
    fontSize: "13px",
    color: "#ff8899",
    lineHeight: 1.6,
  },
  tipBox: {
    backgroundColor: "rgba(0,255,157,0.05)",
    border: "1px solid rgba(0,255,157,0.2)",
    borderRadius: "4px",
    padding: "14px",
  },
  tipLabel: {
    fontSize: "10px",
    letterSpacing: "2px",
    color: "rgba(0,255,157,0.5)",
    textTransform: "uppercase",
    marginBottom: "6px",
  },
  tipText: {
    fontSize: "13px",
    color: "#88ffcc",
    lineHeight: 1.6,
  },
};

function getBarColor(pct) {
  if (pct >= 0.7) return "#00ff9d";
  if (pct >= 0.4) return "#ffcc00";
  return "#ff4466";
}

function Cell({ label, value, accent }) {
  return (
    <div style={styles.cell}>
      <div style={styles.cellLabel}>{label}</div>
      <div style={{ ...styles.cellValue, color: accent || "#e0e0e0" }}>{value}</div>
    </div>
  );
}

async function fetchViaProxy(targetUrl) {
  const proxies = [
    `https://api.allorigins.win/raw?url=${encodeURIComponent(targetUrl)}`,
    `https://corsproxy.io/?${encodeURIComponent(targetUrl)}`,
    `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(targetUrl)}`,
  ];
  let lastErr;
  for (const proxyUrl of proxies) {
    try {
      const res = await fetch(proxyUrl, { signal: AbortSignal.timeout(8000) });
      if (res.ok) return res;
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("全プロキシ接続失敗");
}

async function fetchEbaySold(keywords, appId) {
  const params = new URLSearchParams({
    "OPERATION-NAME": "findCompletedItems",
    "SERVICE-VERSION": "1.0.0",
    "SECURITY-APPNAME": appId,
    "RESPONSE-DATA-FORMAT": "JSON",
    "keywords": keywords,
    "paginationInput.entriesPerPage": "8",
    "sortOrder": "EndTimeSoonest",
  });
  const ebayUrl = `https://svcs.ebay.com/services/search/FindingService/v1?${params}`;
  const res = await fetchViaProxy(ebayUrl);
  const rawText = await res.text();
  let data;
  try {
    data = JSON.parse(rawText);
  } catch {
    throw new Error(`レスポンス解析失敗: ${rawText.slice(0, 80)}`);
  }
  const ack = data.findCompletedItemsResponse?.[0]?.ack?.[0];
  const count = data.findCompletedItemsResponse?.[0]?.searchResult?.[0]?.["@count"];
  if (ack !== "Success") {
    const ebayMsg = data.errorMessage?.[0]?.error?.[0]?.message?.[0]
      || data.findCompletedItemsResponse?.[0]?.errorMessage?.[0]?.error?.[0]?.message?.[0]
      || JSON.stringify(data).slice(0, 120);
    throw new Error(`eBay: ${ebayMsg}`);
  }
  const items = data.findCompletedItemsResponse?.[0]?.searchResult?.[0]?.item || [];
  return { count, items: items.map(item => ({
    title: item.title?.[0],
    price: item.sellingStatus?.[0]?.currentPrice?.[0]?.["__value__"],
    currency: item.sellingStatus?.[0]?.currentPrice?.[0]?.["@currencyId"],
    condition: item.condition?.[0]?.conditionDisplayName?.[0],
  }))};
}

export default function App() {
  const [apiKey, setApiKey] = useState("");
  const [ebayAppId, setEbayAppId] = useState("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [ebayStatus, setEbayStatus] = useState("");

  async function translateToEbayKeywords(text) {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ role: "user", parts: [{ text: `以下の日本語の商品情報から、eBayで検索するための英語キーワードを5単語以内で返してください。キーワードのみ返答してください（説明不要）。\n商品情報: ${text}` }] }],
          generationConfig: { maxOutputTokens: 50, thinkingConfig: { thinkingBudget: 0 } },
        }),
      }
    );
    const data = await res.json();
    const parts = data.candidates?.[0]?.content?.parts || [];
    const textPart = parts.find(p => !p.thought);
    const translated = textPart?.text?.trim();
    if (!translated) throw new Error("翻訳失敗");
    return translated;
  }

  async function analyze() {
    if (!apiKey) {
      setError("APIキーを入力してください。");
      return;
    }
    if (!input) return;

    setLoading(true);
    setResult(null);
    setError("");
    setEbayStatus("");

    let ebayContext = "";
    if (ebayAppId) {
      try {
        setEbayStatus("キーワードを英語に変換中...");
        let enKeyword;
        try {
          enKeyword = await translateToEbayKeywords(input);
        } catch {
          enKeyword = input.replace(/[^\x20-\x7E]/g, "").trim() || "anime goods";
        }
        setEbayStatus(`eBay検索中: "${enKeyword}"`);
        const { items: sold, count } = await fetchEbaySold(enKeyword, ebayAppId);
        if (sold.length > 0) {
          ebayContext = "\n\n【eBay落札実績（直近）】\n" + sold.map(
            (s, i) => `${i + 1}. ${s.title} — ${s.currency} ${s.price}（${s.condition || "状態不明"}）`
          ).join("\n");
          setEbayStatus(`eBayデータ取得完了（${sold.length}件）`);
        } else {
          setEbayStatus(`eBay: データなし（count:${count}, keyword:"${enKeyword}"）`);
        }
      } catch (e) {
        setEbayStatus(`eBay取得失敗: ${e.message}`);
      }
    }

    try {
      const userMessage = `商品情報: ${input}${ebayContext}`;
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
            contents: [{ role: "user", parts: [{ text: userMessage }] }],
            generationConfig: { maxOutputTokens: 2048, responseMimeType: "application/json" },
          }),
        }
      );

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || `APIエラー (${res.status})`);
      }
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!text) throw new Error("レスポンスが空です");

      const cleaned = text.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim();
      const jsonStart = cleaned.indexOf("{");
      const jsonEnd = cleaned.lastIndexOf("}");
      if (jsonStart === -1 || jsonEnd === -1) throw new Error("JSONが見つかりません");
      const parsed = JSON.parse(cleaned.slice(jsonStart, jsonEnd + 1));
      setResult(parsed);
    } catch (e) {
      setError(`分析に失敗しました: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      analyze();
    }
  }

  const vc = result ? VERDICT_CONFIG[result.verdict] : null;

  return (
    <div className="as-app" style={styles.app}>
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        * { box-sizing: border-box; }
        body { margin: 0; }
        @media (max-width: 480px) {
          .as-app { padding: 24px 16px 40px !important; }
          .as-header-title { font-size: 16px !important; letter-spacing: 2px !important; }
          .as-verdict-label { font-size: 22px !important; }
          .as-verdict-score { font-size: 42px !important; }
          .as-grid-2col { grid-template-columns: 1fr !important; }
          .as-preset-btn { font-size: 12px !important; padding: 10px 14px !important; }
          .as-analyze-btn { font-size: 13px !important; padding: 16px !important; }
          .as-textarea { min-height: 80px !important; }
        }
      `}</style>

      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <h1 className="as-header-title" style={styles.headerTitle}>ANIME GOODS 需要スコアリング</h1>
          <p style={styles.headerSub}>Overseas Demand Analysis Tool</p>
        </div>

        {/* API Key */}
        <div style={styles.section}>
          <label style={styles.label}>GEMINI API KEY（無料）</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="AIza..."
            style={styles.input}
          />
          <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)", marginTop: "6px", letterSpacing: "0.5px" }}>
            キーの取得：aistudio.google.com → 「Get API key」→ 「APIキーを作成」
          </div>
        </div>

        {/* eBay App ID */}
        <div style={styles.section}>
          <label style={styles.label}>EBAY APP ID（任意・落札実績を取得）</label>
          <input
            type="password"
            value={ebayAppId}
            onChange={(e) => setEbayAppId(e.target.value)}
            placeholder="xxxx-xxxx-xxxx-xxxx"
            style={styles.input}
          />
          <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)", marginTop: "6px" }}>
            商品情報を自動で英語に変換してeBayを検索します
          </div>
          {ebayStatus && (
            <div style={{ fontSize: "11px", color: "rgba(255,204,0,0.7)", marginTop: "6px" }}>
              {ebayStatus}
            </div>
          )}
        </div>

        {/* Input */}
        <div style={styles.section}>
          <label style={styles.label}>商品情報</label>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="例：ワンピース ジャンプフェスタ限定 ルフィ フィギュア 2024 会場販売のみ"
            className="as-textarea"
            style={styles.textarea}
          />
        </div>

        {/* Presets */}
        <div style={{ ...styles.section, marginTop: "-12px" }}>
          <label style={styles.label}>PRESET</label>
          <div style={styles.presetRow}>
            {PRESETS.map((p) => (
              <button key={p.label} onClick={() => setInput(p.value)} className="as-preset-btn" style={styles.presetBtn}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Analyze Button */}
        <div style={styles.section}>
          <button
            onClick={analyze}
            disabled={loading}
            className="as-analyze-btn"
            style={{ ...styles.analyzeBtn, ...(loading ? { opacity: 0.5, cursor: "not-allowed" } : {}) }}
          >
            {loading ? "[ 分析中... ]" : "[ 需要スコアを算出する ]"}
          </button>
        </div>

        {/* Error */}
        {error && <div style={styles.error}>{error}</div>}

        {/* Result */}
        {result && vc && (
          <div style={styles.resultArea}>
            {/* Verdict Banner */}
            <div style={{ ...styles.verdictBanner, backgroundColor: vc.bg, border: `1px solid ${vc.border}` }}>
              <div className="as-verdict-label" style={{ ...styles.verdictLabel, color: vc.color }}>{vc.label}</div>
              <div style={{ textAlign: "right" }}>
                <div className="as-verdict-score" style={{ ...styles.verdictScoreNum, color: vc.color }}>{result.totalScore}</div>
                <div style={{ ...styles.verdictScoreLabel, color: vc.color }}>/ 100 POINTS</div>
              </div>
            </div>

            {/* Axes */}
            <div style={styles.axesSection}>
              <div style={styles.sectionTitle}>SCORE BREAKDOWN</div>
              {result.axes.map((axis) => {
                const pct = axis.score / axis.max;
                const barColor = getBarColor(pct);
                return (
                  <div key={axis.name} style={styles.axisRow}>
                    <div style={styles.axisHeader}>
                      <span style={styles.axisName}>{axis.name}</span>
                      <span style={{ ...styles.axisScore, color: barColor }}>
                        {axis.score} / {axis.max}
                      </span>
                    </div>
                    <div style={styles.axisBarBg}>
                      <div
                        style={{
                          height: "100%",
                          width: `${pct * 100}%`,
                          backgroundColor: barColor,
                          borderRadius: "3px",
                          transition: "width 0.6s ease",
                        }}
                      />
                    </div>
                    <div style={styles.axisReason}>{axis.reason}</div>
                  </div>
                );
              })}
            </div>

            {/* Multiplier & Markets */}
            <div className="as-grid-2col" style={styles.grid2col}>
              <Cell label="推定転売倍率" value={result.estimatedResaleMultiplier} accent="#aa88ff" />
              <Cell label="狙い目マーケット" value={result.targetMarkets.join(" · ")} accent="#66ccff" />
            </div>

            {/* Risk Note */}
            <div style={styles.riskBox}>
              <div style={styles.riskLabel}>RISK NOTE</div>
              <div style={styles.riskText}>{result.riskNote}</div>
            </div>

            {/* Quick Tip */}
            <div style={styles.tipBox}>
              <div style={styles.tipLabel}>QUICK TIP</div>
              <div style={styles.tipText}>{result.quickTip}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
