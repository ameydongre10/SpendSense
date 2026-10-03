/**
 * SpendSense — Editorial Chart Rendering Engine
 * Generates crisp SVG visualizations styled with the acid/ink/paper design system.
 */

window.Charts = {
  /**
   * Render Precision-Recall Curve comparing Logistic Regression vs XGBoost
   */
  renderPRCurve(containerId, prLr, prXgb, auprcLr, auprcXgb) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const width = 480;
    const height = 280;
    const pad = 40;

    const scaleX = (val) => pad + val * (width - 2 * pad);
    const scaleY = (val) => height - pad - val * (height - 2 * pad);

    // Path generators
    const buildPath = (points) => {
      if (!points || !points.length) return "";
      return points
        .map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.recall).toFixed(1)} ${scaleY(p.precision).toFixed(1)}`)
        .join(" ");
    };

    const pathLr = buildPath(prLr);
    const pathXgb = buildPath(prXgb);

    el.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        <!-- Gridlines -->
        <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#444" stroke-width="1"/>
        <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="#444" stroke-width="1"/>
        
        <!-- Axis labels -->
        <text x="${width / 2}" y="${height - 10}" fill="#aaa" font-size="10" text-anchor="middle" letter-spacing="1">RECALL (DETECTION RATE)</text>
        <text x="14" y="${height / 2}" fill="#aaa" font-size="10" text-anchor="middle" transform="rotate(-90 14 ${height / 2})" letter-spacing="1">PRECISION</text>
        
        <!-- Baseline Reference line -->
        <line x1="${pad}" y1="${scaleY(0.0017)}" x2="${width - pad}" y2="${scaleY(0.0017)}" stroke="#ff4444" stroke-dasharray="3,3" stroke-width="1" opacity="0.6"/>
        <text x="${width - pad - 5}" y="${scaleY(0.0017) - 4}" fill="#ff6666" font-size="8" text-anchor="end">RANDOM PREVALENCE (0.17%)</text>
        
        <!-- LR Curve -->
        <path d="${pathLr}" fill="none" stroke="#888899" stroke-width="2" stroke-dasharray="4,2"/>
        
        <!-- XGBoost Curve -->
        <path d="${pathXgb}" fill="none" stroke="#d5ff00" stroke-width="2.5"/>
        
        <!-- Legend & AUC Readout -->
        <rect x="${pad + 10}" y="${pad + 10}" width="200" height="48" fill="#111116" stroke="#333" rx="2"/>
        <line x1="${pad + 18}" y1="${pad + 24}" x2="${pad + 38}" y2="${pad + 24}" stroke="#d5ff00" stroke-width="2.5"/>
        <text x="${pad + 44}" y="${pad + 27}" fill="#d5ff00" font-size="10" font-weight="700">XGBoost (AUPRC: ${(auprcXgb || 0.997).toFixed(4)})</text>
        
        <line x1="${pad + 18}" y1="${pad + 42}" x2="${pad + 38}" y2="${pad + 42}" stroke="#888899" stroke-width="2" stroke-dasharray="4,2"/>
        <text x="${pad + 44}" y="${pad + 45}" fill="#aaa" font-size="10">Logistic Reg (AUPRC: ${(auprcLr || 0.999).toFixed(4)})</text>
      </svg>
    `;
  },

  /**
   * Render Monthly Fraud Trends (dual-axis rate and loss volume)
   */
  renderFraudTrends(containerId, trends) {
    const el = document.getElementById(containerId);
    if (!el || !trends || !trends.length) return;

    const width = 500;
    const height = 240;
    const padL = 40;
    const padR = 40;
    const padT = 25;
    const padB = 40;

    const maxRate = Math.max(...trends.map((t) => t.fraud_rate_pct), 0.5);
    const maxAmt = Math.max(...trends.map((t) => t.fraud_amount), 1000);

    const stepX = (width - padL - padR) / (trends.length - 1 || 1);

    // Build bars for amount and polyline for rate
    let barsSvg = "";
    let ratePoints = [];

    trends.forEach((t, i) => {
      const x = padL + i * stepX;
      const barH = (t.fraud_amount / maxAmt) * (height - padT - padB);
      const yBar = height - padB - barH;
      barsSvg += `<rect x="${x - 7}" y="${yBar}" width="14" height="${barH}" fill="#2a2a38" rx="1"/>`;

      const yRate = height - padB - (t.fraud_rate_pct / maxRate) * (height - padT - padB);
      ratePoints.push(`${x.toFixed(1)},${yRate.toFixed(1)}`);
    });

    el.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        <line x1="${padL}" y1="${height - padB}" x2="${width - padR}" y2="${height - padB}" stroke="#444" stroke-width="1"/>
        ${barsSvg}
        <polyline points="${ratePoints.join(" ")}" fill="none" stroke="#d5ff00" stroke-width="2.5"/>
        ${ratePoints
          .map((pt) => {
            const [px, py] = pt.split(",");
            return `<circle cx="${px}" cy="${py}" r="3" fill="#111116" stroke="#d5ff00" stroke-width="2"/>`;
          })
          .join("")}
        <!-- X-axis labels (first, middle, last) -->
        <text x="${padL}" y="${height - 12}" fill="#888" font-size="9">${trends[0]?.period || ""}</text>
        <text x="${width / 2}" y="${height - 12}" fill="#888" font-size="9" text-anchor="middle">${trends[Math.floor(trends.length / 2)]?.period || ""}</text>
        <text x="${width - padR}" y="${height - 12}" fill="#888" font-size="9" text-anchor="end">${trends[trends.length - 1]?.period || ""}</text>
        <!-- Legend -->
        <text x="${padL}" y="${padT - 6}" fill="#d5ff00" font-size="9" font-weight="700">● FRAUD RATE (%)</text>
        <text x="${padL + 120}" y="${padT - 6}" fill="#6b6b80" font-size="9">■ MONTHLY FRAUD LOSS ($)</text>
      </svg>
    `;
  },

  /**
   * Render Category Spend Mix
   */
  renderCategoryMix(containerId, categories) {
    const el = document.getElementById(containerId);
    if (!el || !categories) return;

    const topCats = categories.slice(0, 6);
    const maxSpend = Math.max(...topCats.map((c) => c.total_spend), 1);

    let rowsHtml = topCats
      .map((c) => {
        const pct = ((c.total_spend / maxSpend) * 100).toFixed(0);
        return `
        <div style="margin-bottom:0.75rem;">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:0.25rem;">
            <span style="font-weight:600; color:#fff;">${c.category.toUpperCase()}</span>
            <span style="color:#d5ff00;">$${c.total_spend.toLocaleString()} (${c.fraud_rate_pct.toFixed(3)}% fraud)</span>
          </div>
          <div style="height:6px; background:#222; width:100%;">
            <div style="height:100%; background:var(--acid); width:${pct}%;"></div>
          </div>
        </div>
      `;
      })
      .join("");

    el.innerHTML = rowsHtml;
  },

  /**
   * Render Cohort Retention Matrix
   */
  renderCohortMatrix(containerId, cohortData) {
    const el = document.getElementById(containerId);
    if (!el || !cohortData || !cohortData.cohorts) return;

    const { cohorts, cohort_months, max_periods } = cohortData;
    const periodsToShow = Math.min(max_periods, 6);
    const monthsToShow = cohort_months.slice(0, 6);

    // Map into 2D lookup: [month][period] -> retention_rate
    const lookup = {};
    cohorts.forEach((c) => {
      if (!lookup[c.cohort_month]) lookup[c.cohort_month] = {};
      lookup[c.cohort_month][c.period_index] = c.retention_rate;
    });

    let thead = `<tr><th>Cohort</th><th>Size</th>`;
    for (let p = 0; p <= periodsToShow; p++) {
      thead += `<th>M+${p}</th>`;
    }
    thead += `</tr>`;

    let tbody = monthsToShow
      .map((m) => {
        const initialCount = cohorts.find((c) => c.cohort_month === m && c.period_index === 0)?.customer_count || "-";
        let cols = `<td><strong>${m}</strong></td><td>${initialCount}</td>`;
        for (let p = 0; p <= periodsToShow; p++) {
          const rate = lookup[m]?.[p];
          if (rate !== undefined) {
            const opacity = Math.max(0.15, (rate / 100) * 0.85);
            cols += `<td style="background:rgba(213,255,0,${opacity}); color:${rate > 50 ? "#000" : "#fff"}; text-align:center; font-weight:600;">${rate.toFixed(0)}%</td>`;
          } else {
            cols += `<td style="color:#555; text-align:center;">-</td>`;
          }
        }
        return `<tr>${cols}</tr>`;
      })
      .join("");

    el.innerHTML = `
      <table class="data-table-editorial">
        <thead>${thead}</thead>
        <tbody>${tbody}</tbody>
      </table>
    `;
  },
};
