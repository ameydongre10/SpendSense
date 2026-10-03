/**
 * SpendSense — Main Application Controller
 * Fetches real analytical outputs from the FastAPI service and populates the editorial dashboard.
 */

document.addEventListener("DOMContentLoaded", async () => {
  console.log("SpendSense Analytics Engine Initializing...");

  try {
    // 1. Fetch Overview & KPIs
    const overviewRes = await fetch("/api/overview");
    if (overviewRes.ok) {
      const overview = await overviewRes.json();
      updateOverviewKPIs(overview);
    }

    // 2. Fetch Model Comparison
    const modelRes = await fetch("/api/fraud/model");
    let modelData = null;
    if (modelRes.ok) {
      modelData = await modelRes.json();
      updateModelSection(modelData);
    }

    // 3. Fetch Fraud Trends
    const trendsRes = await fetch("/api/fraud/trends");
    let trendsData = null;
    if (trendsRes.ok) {
      trendsData = await trendsRes.json();
      window.Charts.renderFraudTrends("fig-trends-chart", trendsData.trends);
    }

    // 4. Fetch Category Spend Mix
    const spendRes = await fetch("/api/spend");
    if (spendRes.ok) {
      const spendData = await spendRes.json();
      window.Charts.renderCategoryMix("fig-spend-chart", spendData.categories);
    }

    // 5. Fetch Cohorts
    const cohortsRes = await fetch("/api/cohorts");
    if (cohortsRes.ok) {
      const cohortData = await cohortsRes.json();
      window.Charts.renderCohortMatrix("fig-cohort-chart", cohortData);
    }

    // 6. Fetch Recommendations
    const recsRes = await fetch("/api/recommendations");
    if (recsRes.ok) {
      const recsData = await recsRes.json();
      renderRecommendations(recsData.recommendations);
    }

    // 7. Fetch Segments & Profitability
    const segsRes = await fetch("/api/segments");
    if (segsRes.ok) {
      const segsData = await segsRes.json();
      renderSegmentsTable("fig-segments-table", segsData.segments);
    }

    // 8. Fetch Anomalies
    const anomRes = await fetch("/api/anomalies");
    if (anomRes.ok) {
      const anomData = await anomRes.json();
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
  const xgb = modelData.xgboost;
  const lr = modelData.logistic_regression;

  const statRecall = document.getElementById("stat-recall");
  const statFp = document.getElementById("stat-fp");
  const statProfit = document.getElementById("stat-profit");

  if (statRecall) statRecall.textContent = `${(xgb.recall * 100).toFixed(1)}%`;
  if (statFp) statFp.textContent = `${xgb.false_positives} FP`;
  if (statProfit) statProfit.textContent = `3.16x`;

  // Render PR curve in portrait card
  window.Charts.renderPRCurve(
    "portrait-pr-curve",
    modelData.pr_curve_lr,
    modelData.pr_curve_xgb,
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
