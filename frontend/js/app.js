/**
 * SpendSense — Main Application Controller
 * Dual-Mode Data Engine:
 * 1. Live Mode: Fetches from live FastAPI backend (/api/overview, /api/fraud/model, etc.)
 * 2. Static / GitHub Pages Mode: Gracefully falls back to precomputed analytics cache
 *    so the dashboard runs smoothly on GitHub Pages, Vercel, or local file preview.
 */

// Embedded fallback cache to guarantee 100% uptime on static hosts
const EMBEDDED_CACHE = {
  overview: {
    total_transactions: 284807,
    fraud_count: 492,
    legitimate_count: 284315,
    fraud_rate_pct: 0.1727,
    total_amount: 25162590.0,
    total_fraud_amount: 60127.97,
    total_legitimate_amount: 25102462.03,
    avg_transaction_amount: 88.35,
    avg_fraud_amount: 122.21,
    avg_legitimate_amount: 88.29,
    revenue_at_risk: 42538.90,
    unique_customers: 4665,
    segment_count: 6,
    anomaly_count: 2033
  },
  model: {
    logistic_regression: {
      model_name: "Logistic Regression (Baseline)",
      precision: 0.8750,
      recall: 1.0000,
      f1: 0.9333,
      auprc: 1.0000,
      true_positives: 98,
      false_positives: 14,
      true_negatives: 56850,
      false_negatives: 0
    },
    xgboost: {
      model_name: "XGBoost (Advanced)",
      precision: 0.9510,
      recall: 0.9898,
      f1: 0.9700,
      auprc: 0.9971,
      true_positives: 97,
      false_positives: 5,
      true_negatives: 56859,
      false_negatives: 1
    },
    pr_curve_lr: [
      { recall: 1.0, precision: 0.875 }, { recall: 0.95, precision: 0.89 }, { recall: 0.8, precision: 0.93 }, { recall: 0.0, precision: 1.0 }
    ],
    pr_curve_xgb: [
      { recall: 0.9898, precision: 0.951 }, { recall: 0.95, precision: 0.975 }, { recall: 0.8, precision: 0.99 }, { recall: 0.0, precision: 1.0 }
    ],
    recommendation: "Deploy XGBoost: cuts false-positive alerts by 64% while maintaining 98.98% recall."
  }
};

let precomputedCache = null;

async function fetchAnalytics(endpoint, cacheKey) {
  // 1. Try Live API (FastAPI backend / Vercel serverless / Render)
  try {
    const res = await fetch(endpoint);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    // API server not reachable, fallback to static cache
  }

  // 2. Try loading precomputed JSON file (GitHub Pages static host)
  if (!precomputedCache) {
    const possiblePaths = [
      "analytics/cache/precomputed_analytics.json",
      "../analytics/cache/precomputed_analytics.json",
      "./precomputed_analytics.json",
      "/SpendSense/analytics/cache/precomputed_analytics.json"
    ];
    for (const path of possiblePaths) {
      try {
        const cRes = await fetch(path);
        if (cRes.ok) {
          precomputedCache = await cRes.json();
          break;
        }
      } catch (e) {}
    }
  }

  if (endpoint.includes("fraud/model")) {
    if (precomputedCache && precomputedCache.model) return precomputedCache.model;
    return EMBEDDED_CACHE.model;
  }

  if (precomputedCache && precomputedCache[cacheKey]) {
    const data = precomputedCache[cacheKey];
    if (cacheKey === "spend") return { categories: data };
    if (cacheKey === "segments") return { segments: data, total_customers: 4665 };
    if (cacheKey === "trends") return { trends: data };
    if (cacheKey === "recommendations") return { recommendations: data };
    return data;
  }

  // 3. Fallback to embedded constants
  if (cacheKey === "overview") return EMBEDDED_CACHE.overview;
  return null;
}

document.addEventListener("DOMContentLoaded", async () => {
  console.log("SpendSense Analytics Engine Initializing...");

  try {
    // 1. Fetch Overview & KPIs
    const overview = await fetchAnalytics("/api/overview", "overview");
    if (overview) updateOverviewKPIs(overview);

    // 2. Fetch Model Comparison
    const modelData = await fetchAnalytics("/api/fraud/model", "model");
    if (modelData) updateModelSection(modelData);

    // 3. Fetch Fraud Trends
    const trendsData = await fetchAnalytics("/api/fraud/trends", "trends");
    if (trendsData && trendsData.trends) {
      window.Charts.renderFraudTrends("fig-trends-chart", trendsData.trends);
    }

    // 4. Fetch Category Spend Mix
    const spendData = await fetchAnalytics("/api/spend", "spend");
    if (spendData && spendData.categories) {
      window.Charts.renderCategoryMix("fig-spend-chart", spendData.categories);
    }

    // 5. Fetch Cohorts
    const cohortData = await fetchAnalytics("/api/cohorts", "cohorts");
    if (cohortData && cohortData.cohorts) {
      window.Charts.renderCohortMatrix("fig-cohort-chart", cohortData);
    }

    // 6. Fetch Recommendations
    const recsData = await fetchAnalytics("/api/recommendations", "recommendations");
    if (recsData && recsData.recommendations) {
      renderRecommendations(recsData.recommendations);
    }

    // 7. Fetch Segments & Profitability
    const segsData = await fetchAnalytics("/api/segments", "segments");
    if (segsData && segsData.segments) {
      renderSegmentsTable("fig-segments-table", segsData.segments);
    }

    // 8. Fetch Anomalies
    const anomData = await fetchAnalytics("/api/anomalies", "anomalies");
    if (anomData && anomData.anomalies) {
      renderAnomaliesTable("fig-anomalies-table", anomData.anomalies.slice(0, 5));
    }

    // Setup interactive agenda navigation
    setupAgendaTabs();
  } catch (err) {
    console.error("Error loading SpendSense dashboard data:", err);
  }
});

function updateOverviewKPIs(data) {
  const elTxns = document.getElementById("kpi-txns");
  const elFraudRate = document.getElementById("kpi-fraud-rate");
  const elRevAtRisk = document.getElementById("kpi-rev-at-risk");
  const elAuprc = document.getElementById("kpi-auprc");

  if (elTxns) elTxns.textContent = data.total_transactions.toLocaleString();
  if (elFraudRate) elFraudRate.textContent = `${data.fraud_rate_pct.toFixed(3)}%`;
  if (elRevAtRisk) elRevAtRisk.textContent = `$${data.revenue_at_risk.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  if (elAuprc) elAuprc.textContent = "0.997";
}

function updateModelSection(modelData) {
  const xgb = modelData.xgboost || EMBEDDED_CACHE.model.xgboost;
  const lr = modelData.logistic_regression || EMBEDDED_CACHE.model.logistic_regression;

  const statRecall = document.getElementById("stat-recall");
  const statFp = document.getElementById("stat-fp");
  const statProfit = document.getElementById("stat-profit");

  if (statRecall) statRecall.textContent = `${(xgb.recall * 100).toFixed(1)}%`;
  if (statFp) statFp.textContent = `${xgb.false_positives} FP`;
  if (statProfit) statProfit.textContent = `3.16x`;

  window.Charts.renderPRCurve(
    "portrait-pr-curve",
    modelData.pr_curve_lr || EMBEDDED_CACHE.model.pr_curve_lr,
    modelData.pr_curve_xgb || EMBEDDED_CACHE.model.pr_curve_xgb,
    lr.auprc,
    xgb.auprc
  );
}

function renderRecommendations(recs) {
  const container = document.getElementById("recommendations-container");
  if (!container || !recs) return;

  container.innerHTML = recs
    .map(
      (r) => `
    <div class="rec-card">
      <div class="eyebrow" style="color:var(--ink); opacity:0.8;">Recommendation 0${r.id} · Priority: ${r.priority}</div>
      <div class="rec-title">${r.title}</div>
      <div class="rec-body">
        <p style="margin:0 0 0.5rem 0;"><strong>Finding:</strong> ${r.finding}</p>
        <p style="margin:0 0 0.5rem 0;"><strong>Proposed Action:</strong> ${r.action}</p>
      </div>
      <div class="rec-impact">→ ${r.quantified_impact}</div>
    </div>
  `
    )
    .join("");
}

function renderSegmentsTable(containerId, segments) {
  const el = document.getElementById(containerId);
  if (!el || !segments) return;

  let rows = segments
    .map(
      (s) => `
    <tr>
      <td><strong style="color:#fff;">${s.segment_label}</strong></td>
      <td>${s.customer_count.toLocaleString()}</td>
      <td>$${s.total_spend.toLocaleString()}</td>
      <td style="color:var(--acid); font-weight:700;">${s.profit_index}x</td>
      <td>${s.revenue_share.toFixed(1)}%</td>
    </tr>
  `
    )
    .join("");

  el.innerHTML = `
    <table class="data-table-editorial">
      <thead>
        <tr>
          <th>Segment Tier</th>
          <th>Cards</th>
          <th>Spend Vol</th>
          <th>Profit Index</th>
          <th>Share</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderAnomaliesTable(containerId, anomalies) {
  const el = document.getElementById(containerId);
  if (!el || !anomalies) return;

  let rows = anomalies
    .map(
      (a) => `
    <tr>
      <td>#${a.transaction_id}</td>
      <td style="color:#ff6666; font-weight:700;">$${a.amount.toFixed(2)}</td>
      <td style="color:var(--acid);">${a.anomaly_score}σ</td>
      <td style="font-size:0.75rem; color:#bbb;">${a.reason}</td>
    </tr>
  `
    )
    .join("");

  el.innerHTML = `
    <table class="data-table-editorial">
      <thead>
        <tr>
          <th>Txn ID</th>
          <th>Amount</th>
          <th>Score</th>
          <th>Analytical Reason</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function setupAgendaTabs() {
  const items = document.querySelectorAll(".agenda li");
  items.forEach((item, index) => {
    item.addEventListener("click", () => {
      items.forEach((it) => it.classList.remove("active"));
      item.classList.add("active");
    });
  });
}
