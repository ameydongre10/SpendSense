/**
 * SpendSense — Editorial Chart & Visualization Engine
 * Generates crisp SVG visualizations and dynamic data tables
 * styled with the acid/ink/paper design system.
 */

window.Charts = {
  /**
   * Render Precision-Recall Curve comparing Logistic Regression vs XGBoost
   * with dynamic operating point indicator
   */
  renderPRCurve(containerId, prLr, prXgb, auprcLr, auprcXgb, activePoint = null) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const width = 480;
    const height = 280;
    const pad = 40;

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
        <line x1="${cx}" y1="${height - pad}" x2="${cx}" y2="${cy}" stroke="var(--acid)" stroke-dasharray="3,3" stroke-width="1.5" opacity="0.8"/>
        <line x1="${pad}" y1="${cy}" x2="${cx}" y2="${cy}" stroke="var(--acid)" stroke-dasharray="3,3" stroke-width="1.5" opacity="0.8"/>
        <circle cx="${cx}" cy="${cy}" r="6" fill="var(--acid)" stroke="#111116" stroke-width="2"/>
        <circle cx="${cx}" cy="${cy}" r="12" fill="none" stroke="var(--acid)" stroke-width="1.5" opacity="0.5">
          <animate attributeName="r" values="6;16;6" dur="2s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite"/>
        </circle>
      `;
    }

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

        <!-- Active point indicator -->
        ${activeMarkerSvg}
        
        <!-- Legend & AUC Readout -->
        <rect x="${pad + 10}" y="${pad + 10}" width="200" height="48" fill="#111116" stroke="#333" rx="2"/>
        <line x1="${pad + 18}" y1="${pad + 24}" x2="${pad + 38}" y2="${pad + 24}" stroke="#d5ff00" stroke-width="2.5"/>
        <text x="${pad + 44}" y="${pad + 27}" fill="#d5ff00" font-size="10" font-weight="700">XGBoost (AUPRC: ${(auprcXgb || 0.9971).toFixed(4)})</text>
        
        <line x1="${pad + 18}" y1="${pad + 42}" x2="${pad + 38}" y2="${pad + 42}" stroke="#888899" stroke-width="2" stroke-dasharray="4,2"/>
        <text x="${pad + 44}" y="${pad + 45}" fill="#aaa" font-size="10">Logistic Reg (AUPRC: ${(auprcLr || 0.9999).toFixed(4)})</text>
      </svg>
    `;
  },

  /**
   * Render Monthly Fraud Trends (interactive dual-axis rate and loss volume)
   * Supports viewMode: 'all', 'rate', 'amount'
   */
  renderFraudTrends(containerId, trends, viewMode = "all", onHover = null) {
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

    let barsSvg = "";
    let ratePoints = [];
    let interactiveHitAreas = "";

    trends.forEach((t, i) => {
      const x = padL + i * stepX;
      const barH = (t.fraud_amount / maxAmt) * (height - padT - padB);
      const yBar = height - padB - barH;

      const barOpacity = viewMode === "rate" ? "0.15" : "1";
      barsSvg += `<rect class="trend-bar" data-idx="${i}" x="${x - 7}" y="${yBar}" width="14" height="${barH}" fill="#2a2a38" rx="1" opacity="${barOpacity}"/>`;

      const yRate = height - padB - (t.fraud_rate_pct / maxRate) * (height - padT - padB);
      ratePoints.push(`${x.toFixed(1)},${yRate.toFixed(1)}`);

      // Invisible hit area for crisp mouse interaction
      interactiveHitAreas += `
        <rect class="trend-hit" data-idx="${i}" x="${x - stepX / 2}" y="${padT}" width="${stepX}" height="${height - padT - padB}" fill="transparent" style="cursor:pointer;"/>
      `;
    });

    const rateLineOpacity = viewMode === "amount" ? "0.15" : "1";

    el.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        <line x1="${padL}" y1="${height - padB}" x2="${width - padR}" y2="${height - padB}" stroke="#444" stroke-width="1"/>
        
        <!-- Volume bars -->
        ${barsSvg}
        
        <!-- Rate polyline and markers -->
        <g opacity="${rateLineOpacity}">
          <polyline points="${ratePoints.join(" ")}" fill="none" stroke="#d5ff00" stroke-width="2.5"/>
          ${ratePoints
            .map((pt, i) => {
              const [px, py] = pt.split(",");
              return `<circle class="trend-point" data-idx="${i}" cx="${px}" cy="${py}" r="3.5" fill="#111116" stroke="#d5ff00" stroke-width="2"/>`;
            })
            .join("")}
        </g>

        <!-- Hit areas for interaction -->
        ${interactiveHitAreas}

        <!-- X-axis labels (first, middle, last) -->
        <text x="${padL}" y="${height - 12}" fill="#888" font-size="9">${trends[0]?.period || ""}</text>
        <text x="${width / 2}" y="${height - 12}" fill="#888" font-size="9" text-anchor="middle">${trends[Math.floor(trends.length / 2)]?.period || ""}</text>
        <text x="${width - padR}" y="${height - 12}" fill="#888" font-size="9" text-anchor="end">${trends[trends.length - 1]?.period || ""}</text>
        
        <!-- Legend -->
        <text x="${padL}" y="${padT - 6}" fill="#d5ff00" font-size="9" font-weight="700">● FRAUD RATE (%)</text>
        <text x="${padL + 120}" y="${padT - 6}" fill="#6b6b80" font-size="9">■ MONTHLY FRAUD LOSS ($)</text>
      </svg>
    `;

    // Bind interaction events
    const hitRects = el.querySelectorAll(".trend-hit");
    hitRects.forEach((rect) => {
      rect.addEventListener("mouseenter", (e) => {
        const idx = parseInt(e.target.getAttribute("data-idx"), 10);
        const item = trends[idx];
        if (item && onHover) onHover(item);

        // Highlight bar and circle
        const bar = el.querySelector(`.trend-bar[data-idx="${idx}"]`);
        if (bar) bar.setAttribute("fill", "var(--acid)");
        const circle = el.querySelector(`.trend-point[data-idx="${idx}"]`);
        if (circle) circle.setAttribute("r", "6");
      });

      rect.addEventListener("mouseleave", (e) => {
        const idx = parseInt(e.target.getAttribute("data-idx"), 10);
        const bar = el.querySelector(`.trend-bar[data-idx="${idx}"]`);
        if (bar) bar.setAttribute("fill", "#2a2a38");
        const circle = el.querySelector(`.trend-point[data-idx="${idx}"]`);
        if (circle) circle.setAttribute("r", "3.5");
      });
    });
  },

  /**
   * Render Category Spend Mix with sorting and interactive selection
   * Supports sortMode: 'spend', 'rate', 'alpha'
   */
  renderCategoryMix(containerId, categories, sortMode = "spend", onSelect = null) {
    const el = document.getElementById(containerId);
    if (!el || !categories) return;

    let sorted = [...categories];
    if (sortMode === "rate") {
      sorted.sort((a, b) => b.fraud_rate_pct - a.fraud_rate_pct);
    } else if (sortMode === "alpha") {
      sorted.sort((a, b) => a.category.localeCompare(b.category));
    } else {
      sorted.sort((a, b) => b.total_spend - a.total_spend);
    }

    const topCats = sorted.slice(0, 6);
    const maxSpend = Math.max(...topCats.map((c) => c.total_spend), 1);

    let rowsHtml = topCats
      .map((c, i) => {
        const pct = ((c.total_spend / maxSpend) * 100).toFixed(0);
        return `
        <div class="category-mix-row" data-cat="${c.category}" style="margin-bottom:0.75rem; padding:0.4rem 0.6rem; border-radius:3px; cursor:pointer; transition:all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:0.35rem;">
            <span style="font-weight:600; color:#fff;">${c.category.toUpperCase()}</span>
            <span style="color:#d5ff00;">$${c.total_spend.toLocaleString()} · <span style="color:#bbb;">${c.fraud_rate_pct.toFixed(3)}% fraud</span></span>
          </div>
          <div style="height:6px; background:#222; width:100%; border-radius:2px; overflow:hidden;">
            <div style="height:100%; background:var(--acid); width:${pct}%; transition:width 0.8s ease;"></div>
          </div>
        </div>
      `;
      })
      .join("");

    el.innerHTML = rowsHtml;

    if (onSelect) {
      el.querySelectorAll(".category-mix-row").forEach((row) => {
        row.addEventListener("click", () => {
          const catName = row.getAttribute("data-cat");
          const item = categories.find((c) => c.category === catName);
          if (item) onSelect(item);
        });
      });
    }
  },

  /**
   * Render Cohort Retention Matrix or Lifecycle Decay Curve
   * Supports viewMode: 'matrix' | 'curve'
   */
  renderCohortMatrix(containerId, cohortData, viewMode = "matrix") {
    const el = document.getElementById(containerId);
    if (!el || !cohortData || !cohortData.cohorts) return;

    const { cohorts, cohort_months, max_periods } = cohortData;
    const periodsToShow = Math.min(max_periods, 6);

    const lookup = {};
    cohorts.forEach((c) => {
      if (!lookup[c.cohort_month]) lookup[c.cohort_month] = {};
      lookup[c.cohort_month][c.period_index] = c.retention_rate;
    });

    if (viewMode === "curve") {
      // Calculate average retention decay curve across all cohorts
      const avgCurve = [];
      for (let p = 0; p <= periodsToShow; p++) {
        const rates = [];
        cohort_months.forEach((m) => {
          if (lookup[m] && lookup[m][p] !== undefined) rates.push(lookup[m][p]);
        });
        const avg = rates.length ? rates.reduce((a, b) => a + b, 0) / rates.length : 0;
        avgCurve.push({ period: p, rate: avg });
      }

      const width = 480;
      const height = 220;
      const padL = 40;
      const padR = 30;
      const padT = 20;
      const padB = 35;

      const scaleX = (p) => padL + (p / periodsToShow) * (width - padL - padR);
      const scaleY = (r) => height - padB - (r / 100) * (height - padT - padB);

      const pathPts = avgCurve.map((pt) => `${scaleX(pt.period).toFixed(1)},${scaleY(pt.rate).toFixed(1)}`).join(" ");
      const areaPts = `${scaleX(0)},${height - padB} ` + pathPts + ` ${scaleX(periodsToShow)},${height - padB}`;

      el.innerHTML = `
        <svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
          <!-- 50% Benchmark line -->
          <line x1="${padL}" y1="${scaleY(50)}" x2="${width - padR}" y2="${scaleY(50)}" stroke="#ff5555" stroke-dasharray="3,3" stroke-width="1" opacity="0.6"/>
          <text x="${width - padR}" y="${scaleY(50) - 4}" fill="#ff7777" font-size="8" text-anchor="end">50% ADOPTION BENCHMARK</text>
          
          <!-- Area fill -->
          <polygon points="${areaPts}" fill="rgba(213,255,0,0.12)"/>
          
          <!-- Curve line -->
          <polyline points="${pathPts}" fill="none" stroke="var(--acid)" stroke-width="2.5"/>
          
          <!-- Data markers with labels -->
          ${avgCurve
            .map((pt) => {
              const cx = scaleX(pt.period);
              const cy = scaleY(pt.rate);
              return `
                <circle cx="${cx}" cy="${cy}" r="4" fill="#111116" stroke="var(--acid)" stroke-width="2"/>
                <text x="${cx}" y="${cy - 8}" fill="#fff" font-size="9" font-weight="700" text-anchor="middle">${pt.rate.toFixed(0)}%</text>
                <text x="${cx}" y="${height - 12}" fill="#888" font-size="9" text-anchor="middle">M+${pt.period}</text>
              `;
            })
            .join("")}
          
          <!-- Axis line -->
          <line x1="${padL}" y1="${height - padB}" x2="${width - padR}" y2="${height - padB}" stroke="#444" stroke-width="1"/>
        </svg>
      `;
      return;
    }

    // Default: Heatmap Matrix
    const monthsToShow = cohort_months.slice(0, 6);
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
            cols += `<td style="background:rgba(213,255,0,${opacity}); color:${rate > 50 ? "#000" : "#fff"}; text-align:center; font-weight:600; border-radius:2px; cursor:help;" title="${m} M+${p}: ${rate.toFixed(1)}% active">${rate.toFixed(0)}%</td>`;
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

  /**
   * Render Customer Segment Profitability & Unit Economics (Pillar 05)
   * Dynamically recalculates Gross Revenue, Fraud Losses, Net Contribution, and Profit Index
   * based on the adjustable Network Take Rate.
   */
  renderProfitability(containerId, segments, takeRate = 0.025, onSelect = null) {
    const el = document.getElementById(containerId);
    if (!el || !segments || !segments.length) return;

    // Recalculate economics dynamically
    const computed = segments.map((s) => {
      const grossRev = s.total_spend * takeRate;
      // Observed fraud losses (either from explicit fraud_amount or based on fraud_rate)
      const fraudLoss = s.fraud_amount !== undefined ? s.fraud_amount : s.total_spend * ((s.fraud_rate || 0.1748) / 100);
      const netContribution = grossRev - fraudLoss;
      const netPerCust = netContribution / s.customer_count;
      return {
        ...s,
        grossRev,
        fraudLoss,
        netContribution,
        netPerCust
      };
    });

    const totalCustomers = computed.reduce((acc, s) => acc + s.customer_count, 0);
    const totalNetContribution = computed.reduce((acc, s) => acc + s.netContribution, 0);
    const portfolioAvgPerCust = totalNetContribution / (totalCustomers || 1);

    // Compute dynamic profit index normalized to portfolio average
    const rows = computed
      .map((s) => {
        const dynProfitIndex = (s.netPerCust / (portfolioAvgPerCust || 1)).toFixed(2);
        const marginPct = ((s.netContribution / (s.grossRev || 1)) * 100).toFixed(1);
        return `
        <tr class="clickable-row" data-seg="${s.segment_label}">
          <td><strong style="color:#fff;">${s.segment_label}</strong></td>
          <td>${s.customer_count.toLocaleString()}</td>
          <td>$${s.grossRev.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
          <td style="color:#ff7777;">-$${s.fraudLoss.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
          <td style="color:#fff; font-weight:600;">$${s.netContribution.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
          <td><span style="background:rgba(213,255,0,0.15); color:var(--acid); font-weight:700; padding:0.15rem 0.4rem; border-radius:2px;">${dynProfitIndex}x</span></td>
        </tr>
      `;
      })
      .join("");

    el.innerHTML = `
      <table class="data-table-editorial">
        <thead>
          <tr>
            <th>Segment Tier</th>
            <th>Cards</th>
            <th>Gross Rev</th>
            <th>Fraud Write-off</th>
            <th>Net Margin</th>
            <th>Profit Index</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;

    if (onSelect) {
      el.querySelectorAll(".clickable-row").forEach((row) => {
        row.addEventListener("click", () => {
          const segName = row.getAttribute("data-seg");
          const item = computed.find((s) => s.segment_label === segName);
          if (item) onSelect(item);
        });
      });
    }
  }
};
