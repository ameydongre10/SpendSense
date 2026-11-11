/**
 * SpendSense — Swiss Modernist Industrial Fintech Chart & SVG Engine
 * High-density data visualizations, tabular numerals, crisp hairline gridlines,
 * interactive tooltips, and real-time simulator recalculations.
 */

window.Charts = {
  /**
   * Render Precision-Recall Curve comparing Logistic Regression vs XGBoost
   */
  renderPRCurve(containerId, prLr, prXgb, auprcLr, auprcXgb, activePoint = null) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const width = 520;
    const height = 300;
    const pad = 44;

    const scaleX = (val) => pad + val * (width - 2 * pad);
    const scaleY = (val) => height - pad - val * (height - 2 * pad);

    const buildPath = (points) => {
      if (!points || !points.length) return "";
      return points
        .map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.recall).toFixed(1)} ${scaleY(p.precision).toFixed(1)}`)
        .join(" ");
    };

    const pathLr = buildPath(prLr);
    const pathXgb = buildPath(prXgb);

    // Active operating point markers
    let activeMarkerSvg = "";
    if (activePoint && typeof activePoint.recall === "number") {
      const cx = scaleX(activePoint.recall);
      const cy = scaleY(activePoint.precision);
      activeMarkerSvg = `
        <line x1="${cx}" y1="${height - pad}" x2="${cx}" y2="${cy}" stroke="#00E599" stroke-dasharray="3,3" stroke-width="1.5" opacity="0.9"/>
        <line x1="${pad}" y1="${cy}" x2="${cx}" y2="${cy}" stroke="#00E599" stroke-dasharray="3,3" stroke-width="1.5" opacity="0.9"/>
        <circle cx="${cx}" cy="${cy}" r="6" fill="#00E599" stroke="#080C14" stroke-width="2.5"/>
        <circle cx="${cx}" cy="${cy}" r="12" fill="none" stroke="#00E599" stroke-width="1.5" opacity="0.4">
          <animate attributeName="r" values="6;16;6" dur="2s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite"/>
        </circle>
      `;
    }

    el.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="xgbGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#00B4D8" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="#00B4D8" stop-opacity="0.0"/>
          </linearGradient>
        </defs>

        <!-- Gridlines -->
        <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        
        <!-- Intermediate Horizontal Gridlines -->
        ${[0.25, 0.5, 0.75, 1.0].map(v => `
          <line x1="${pad}" y1="${scaleY(v)}" x2="${width - pad}" y2="${scaleY(v)}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2,2"/>
          <text x="${pad - 8}" y="${scaleY(v) + 3}" fill="#64748B" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="end">${(v * 100).toFixed(0)}%</text>
        `).join("")}

        <!-- Intermediate Vertical Gridlines -->
        ${[0.2, 0.4, 0.6, 0.8, 1.0].map(v => `
          <line x1="${scaleX(v)}" y1="${pad}" x2="${scaleX(v)}" y2="${height - pad}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2,2"/>
          <text x="${scaleX(v)}" y="${height - pad + 14}" fill="#64748B" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="middle">${(v * 100).toFixed(0)}%</text>
        `).join("")}

        <!-- Axis labels -->
        <text x="${width / 2}" y="${height - 6}" fill="#94A3B8" font-family="Inter, sans-serif" font-size="10" font-weight="600" text-anchor="middle" letter-spacing="0.05em">FRAUD DETECTION RECALL (DETECTION RATE)</text>
        <text x="12" y="${height / 2}" fill="#94A3B8" font-family="Inter, sans-serif" font-size="10" font-weight="600" text-anchor="middle" transform="rotate(-90 12 ${height / 2})" letter-spacing="0.05em">MODEL PRECISION</text>
        
        <!-- Random Guess Prevalence Baseline (0.17%) -->
        <line x1="${pad}" y1="${scaleY(0.0017)}" x2="${width - pad}" y2="${scaleY(0.0017)}" stroke="#EF4444" stroke-dasharray="3,3" stroke-width="1" opacity="0.7"/>
        <text x="${width - pad - 6}" y="${scaleY(0.0017) - 4}" fill="#EF4444" font-family="JetBrains Mono, monospace" font-size="8" text-anchor="end">Prevalence (0.17%)</text>

        <!-- Logistic Regression Baseline Curve (Dashed) -->
        <path d="${pathLr}" fill="none" stroke="#64748B" stroke-dasharray="4,4" stroke-width="2" opacity="0.8"/>
        
        <!-- XGBoost Advanced Curve (Solid Cyan) -->
        <path d="${pathXgb}" fill="none" stroke="#00B4D8" stroke-width="2.5"/>

        <!-- Active Operating Point -->
        ${activeMarkerSvg}
      </svg>
    `;
  },

  /**
   * Render Monthly Loss Trajectory and Fraud Incidence (Pillar 01)
   */
  renderTrendsChart(containerId, trends, mode = "all", onHover = null) {
    const el = document.getElementById(containerId);
    if (!el || !trends || !trends.length) return;

    const width = 760;
    const height = 300;
    const pad = 44;
    const padRight = 50;

    const maxRate = Math.max(...trends.map(t => t.fraud_rate_pct)) * 1.25 || 0.25;
    const maxAmount = Math.max(...trends.map(t => t.fraud_amount)) * 1.25 || 6000;

    const scaleX = (i) => pad + (i / (trends.length - 1)) * (width - pad - padRight);
    const scaleYRate = (val) => height - pad - (val / maxRate) * (height - 2 * pad);
    const scaleYAmount = (val) => height - pad - (val / maxAmount) * (height - 2 * pad);

    const barWidth = Math.max(10, Math.floor((width - pad - padRight) / trends.length) - 6);

    let barsSvg = "";
    if (mode === "all" || mode === "amount") {
      barsSvg = trends.map((t, i) => {
        const x = scaleX(i) - barWidth / 2;
        const y = scaleYAmount(t.fraud_amount);
        const h = Math.max(2, height - pad - y);
        return `
          <rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barWidth}" height="${h.toFixed(1)}" 
                fill="rgba(0, 180, 216, 0.25)" stroke="#00B4D8" stroke-width="1" rx="2" class="trend-bar" data-idx="${i}">
            <title>${t.period}: $${t.fraud_amount.toLocaleString()} fraud</title>
          </rect>
        `;
      }).join("");
    }

    let lineSvg = "";
    if (mode === "all" || mode === "rate") {
      const points = trends.map((t, i) => `${i === 0 ? "M" : "L"} ${scaleX(i).toFixed(1)} ${scaleYRate(t.fraud_rate_pct).toFixed(1)}`).join(" ");
      const dots = trends.map((t, i) => `
        <circle cx="${scaleX(i).toFixed(1)}" cy="${scaleYRate(t.fraud_rate_pct).toFixed(1)}" r="3.5" fill="#00E599" stroke="#080C14" stroke-width="1.5">
          <title>${t.period}: ${t.fraud_rate_pct.toFixed(3)}% fraud rate</title>
        </circle>
      `).join("");
      lineSvg = `
        <path d="${points}" fill="none" stroke="#00E599" stroke-width="2.5"/>
        ${dots}
      `;
    }

    el.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        <!-- Axes -->
        <line x1="${pad}" y1="${height - pad}" x2="${width - padRight}" y2="${height - pad}" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        
        <!-- Left Y-Axis labels (Loss Amount $) -->
        ${[0, maxAmount / 2, maxAmount].map(v => `
          <line x1="${pad}" y1="${scaleYAmount(v)}" x2="${width - padRight}" y2="${scaleYAmount(v)}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2,2"/>
          <text x="${pad - 8}" y="${scaleYAmount(v) + 3}" fill="#64748B" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="end">$${Math.round(v).toLocaleString()}</text>
        `).join("")}

        <!-- Right Y-Axis labels (Fraud Rate %) -->
        ${[0, maxRate / 2, maxRate].map(v => `
          <text x="${width - padRight + 8}" y="${scaleYRate(v) + 3}" fill="#00E599" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="start">${v.toFixed(2)}%</text>
        `).join("")}

        <!-- Bars & Line -->
        ${barsSvg}
        ${lineSvg}

        <!-- X-Axis Labels (Monthly) -->
        ${trends.filter((_, i) => i % 2 === 0 || i === trends.length - 1).map(t => {
          const idx = trends.indexOf(t);
          return `<text x="${scaleX(idx)}" y="${height - pad + 16}" fill="#94A3B8" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="middle">${t.period.slice(2)}</text>`;
        }).join("")}
      </svg>
    `;

    // Attach hover listeners
    const bars = el.querySelectorAll(".trend-bar");
    bars.forEach(b => {
      b.addEventListener("mouseenter", (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        if (typeof onHover === "function") onHover(trends[idx]);
      });
    });
  },

  /**
   * Render Merchant Category Breakdown (Pillar 02)
   */
  renderSpendBars(containerId, categories, onSelect = null) {
    const el = document.getElementById(containerId);
    if (!el || !categories || !categories.length) return;

    const maxSpend = Math.max(...categories.map(c => c.total_spend));

    el.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:0.75rem; padding:0.5rem 1rem;">
        ${categories.map((c, i) => {
          const pct = ((c.total_spend / maxSpend) * 100).toFixed(1);
          return `
            <div class="category-row" data-idx="${i}" style="cursor:pointer; padding:0.4rem 0.5rem; border-radius:4px; transition:background 150ms;">
              <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; margin-bottom:0.25rem;">
                <span style="font-weight:600; color:#fff;">${c.category}</span>
                <div style="font-family:JetBrains Mono, monospace; font-size:0.78rem;">
                  <span style="color:#F8FAFC;">$${c.total_spend.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                  <span style="color:#64748B; margin-left:0.5rem;">(${c.spend_share_pct.toFixed(1)}%)</span>
                  <span style="color:#FF3366; margin-left:0.75rem; font-weight:700;">${c.fraud_rate_pct.toFixed(3)}% Fraud</span>
                </div>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:${pct}%;"></div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

    el.querySelectorAll(".category-row").forEach(row => {
      row.addEventListener("click", (e) => {
        const idx = parseInt(row.dataset.idx, 10);
        if (typeof onSelect === "function") onSelect(categories[idx]);
      });
    });
  },

  /**
   * Render RFM Segments Table (Pillar 03)
   */
  renderSegmentsTable(containerId, segments, onSelect = null) {
    const el = document.getElementById(containerId);
    if (!el || !segments || !segments.length) return;

    el.innerHTML = `
      <table class="terminal-table">
        <thead>
          <tr>
            <th>Segment Tier</th>
            <th>Cards</th>
            <th>Spend Share</th>
            <th>Avg Spend</th>
            <th>Avg Recency</th>
            <th>Profit Index</th>
            <th>Strategic Mandate</th>
          </tr>
        </thead>
        <tbody>
          ${segments.map((s, i) => {
            const isTop = s.profit_index >= 2.0;
            const isAlert = s.segment_label.includes("At-Risk");
            const badgeClass = isTop ? "color:#00E599; font-weight:700;" : (isAlert ? "color:#F59E0B; font-weight:700;" : "color:#94A3B8;");
            return `
              <tr data-idx="${i}">
                <td style="font-weight:700; color:#fff;">${s.segment_label}</td>
                <td class="table-num">${s.customer_count.toLocaleString()}</td>
                <td class="table-num">${s.revenue_share.toFixed(1)}%</td>
                <td class="table-num">$${s.avg_spend.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                <td class="table-num">${s.avg_recency.toFixed(1)} days</td>
                <td class="table-num" style="${badgeClass}">${s.profit_index.toFixed(2)}x</td>
                <td style="font-size:0.75rem; color:#94A3B8;">${s.action || "Active Lifecycle Monitoring"}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;

    el.querySelectorAll("tbody tr").forEach(row => {
      row.addEventListener("click", () => {
        const idx = parseInt(row.dataset.idx, 10);
        if (typeof onSelect === "function") onSelect(segments[idx]);
      });
    });
  },

  /**
   * Render Cohort Retention Heatmap or Curve (Pillar 04)
   */
  renderCohortMatrix(containerId, cohortData, viewMode = "matrix") {
    const el = document.getElementById(containerId);
    if (!el || !cohortData) return;

    const cohorts = cohortData.cohorts || [];
    const months = cohortData.cohort_months || [];

    if (viewMode === "curve") {
      // Average decay curve line chart
      const avgRetention = [];
      months.forEach((m, colIdx) => {
        const vals = cohorts.map(c => c.retention[colIdx]).filter(v => typeof v === "number");
        const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
        if (avg !== null) avgRetention.push({ month: colIdx, avg: avg });
      });

      const width = 760;
      const height = 280;
      const pad = 44;
      const scaleX = (m) => pad + (m / (avgRetention.length - 1)) * (width - 2 * pad);
      const scaleY = (v) => height - pad - (v / 100) * (height - 2 * pad);

      const path = avgRetention.map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.month).toFixed(1)} ${scaleY(p.avg).toFixed(1)}`).join(" ");

      el.innerHTML = `
        <div style="padding:1rem;">
          <svg class="chart-svg" viewBox="0 0 ${width} ${height}">
            <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.15)"/>
            <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.15)"/>
            ${[0, 25, 50, 75, 100].map(v => `
              <line x1="${pad}" y1="${scaleY(v)}" x2="${width - pad}" y2="${scaleY(v)}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2,2"/>
              <text x="${pad - 8}" y="${scaleY(v) + 3}" fill="#64748B" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="end">${v}%</text>
            `).join("")}
            <path d="${path}" fill="none" stroke="#00B4D8" stroke-width="2.5"/>
            ${avgRetention.map(p => `
              <circle cx="${scaleX(p.month)}" cy="${scaleY(p.avg)}" r="3" fill="#00E599"/>
              <text x="${scaleX(p.month)}" y="${height - pad + 15}" fill="#94A3B8" font-family="JetBrains Mono, monospace" font-size="9" text-anchor="middle">M+${p.month}</text>
            `).join("")}
          </svg>
        </div>
      `;
      return;
    }

    // Heatmap Matrix
    el.innerHTML = `
      <div style="overflow-x:auto; padding:0.5rem;">
        <table class="terminal-table" style="font-size:0.75rem;">
          <thead>
            <tr>
              <th style="min-width:90px;">Cohort</th>
              <th style="min-width:60px;">Cards</th>
              ${months.map(m => `<th>${m}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${cohorts.slice(0, 12).map(c => `
              <tr>
                <td style="font-weight:700; color:#fff;">${c.cohort_month}</td>
                <td class="table-num">${c.cohort_size}</td>
                ${c.retention.map(val => {
                  if (val === null || val === undefined) return `<td style="color:#334155;">-</td>`;
                  const opacity = Math.max(0.1, val / 100);
                  const bg = `rgba(0, 180, 216, ${(opacity * 0.45).toFixed(2)})`;
                  const textColor = val > 60 ? "#00E599" : (val > 40 ? "#F8FAFC" : "#94A3B8");
                  return `<td class="table-num" style="background:${bg}; color:${textColor}; font-weight:600; text-align:center;">${val.toFixed(0)}%</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  },

  /**
   * Render Customer Segment Profitability Table with dynamic Take-Rate simulation (Pillar 05)
   */
  renderProfitabilityTable(containerId, profitabilityList, takeRatePct = 2.5) {
    const el = document.getElementById(containerId);
    if (!el || !profitabilityList || !profitabilityList.length) return;

    const rate = takeRatePct / 100.0;
    
    // Dynamic recalculations
    const recomputed = profitabilityList.map(s => {
      const gross = s.total_spend * rate;
      const fraudLoss = s.fraud_amount || (s.total_spend * (s.fraud_rate || 0.0017));
      const net = gross - fraudLoss;
      const netPerCust = s.customer_count > 0 ? net / s.customer_count : 0;
      return { ...s, gross, fraudLoss, net, netPerCust };
    });

    const totalNet = recomputed.reduce((acc, c) => acc + c.net, 0);
    const totalCustomers = recomputed.reduce((acc, c) => acc + c.customer_count, 0);
    const avgNetPerCust = totalCustomers > 0 ? totalNet / totalCustomers : 1;

    el.innerHTML = `
      <table class="terminal-table">
        <thead>
          <tr>
            <th>Segment Tier</th>
            <th>Cards</th>
            <th>Spend Volume ($)</th>
            <th>Gross Take (${takeRatePct.toFixed(2)}%)</th>
            <th>Fraud Loss ($)</th>
            <th>Net Margin ($)</th>
            <th>Simulated Profit Index</th>
          </tr>
        </thead>
        <tbody>
          ${recomputed.map(s => {
            const dynamicIndex = avgNetPerCust > 0 ? s.netPerCust / avgNetPerCust : 1.0;
            const isTop = dynamicIndex >= 2.0;
            return `
              <tr>
                <td style="font-weight:700; color:#fff;">${s.segment_label}</td>
                <td class="table-num">${s.customer_count.toLocaleString()}</td>
                <td class="table-num">$${s.total_spend.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                <td class="table-num" style="color:#00B4D8;">$${s.gross.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                <td class="table-num" style="color:#EF4444;">$${s.fraudLoss.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                <td class="table-num" style="color:#00E599; font-weight:700;">$${s.net.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                <td class="table-num" style="${isTop ? 'color:#00E599; font-weight:800;' : 'color:#F8FAFC;'}">${dynamicIndex.toFixed(2)}x</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  },

  /**
   * Render Explainable Billing Anomalies Table (Pillar 06)
   */
  renderAnomaliesTable(containerId, anomalies, onSelect = null) {
    const el = document.getElementById(containerId);
    if (!el || !anomalies || !anomalies.length) {
      if (el) el.innerHTML = `<div style="padding:1.5rem; text-align:center; color:#64748B;">No anomalies matching filter.</div>`;
      return;
    }

    el.innerHTML = `
      <table class="terminal-table">
        <thead>
          <tr>
            <th>Txn ID</th>
            <th>Cardholder</th>
            <th>Category</th>
            <th>Ticket Amount</th>
            <th>Detection Method</th>
            <th>Score (Z / IQR)</th>
            <th>Explainable Rationale</th>
          </tr>
        </thead>
        <tbody>
          ${anomalies.map((a, i) => {
            const isExtreme = Math.abs(a.score) >= 4.0 || a.amount > 1500;
            return `
              <tr data-idx="${i}">
                <td class="table-num" style="color:#00B4D8; font-weight:600;">#${a.transaction_id}</td>
                <td style="color:#fff;">${a.customer_id}</td>
                <td>${a.merchant_category || "General"}</td>
                <td class="table-num" style="font-weight:700; color:#fff;">$${a.amount.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                <td><span class="classification-tag" style="font-size:0.65rem;">${a.method}</span></td>
                <td class="table-num" style="${isExtreme ? 'color:#EF4444; font-weight:700;' : 'color:#F59E0B;'}">${a.score.toFixed(2)}</td>
                <td style="font-size:0.75rem; color:#94A3B8; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${a.reason}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;

    el.querySelectorAll("tbody tr").forEach(row => {
      row.addEventListener("click", () => {
        const idx = parseInt(row.dataset.idx, 10);
        if (typeof onSelect === "function") onSelect(anomalies[idx]);
      });
    });
  }
};
