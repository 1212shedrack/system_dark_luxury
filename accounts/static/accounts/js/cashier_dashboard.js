/* =============================================
   Cashier Dashboard JS
   Revenue chart + payment pie + live clock
   ============================================= */

/* ── Read data ── */
const LABELS  = JSON.parse(document.getElementById('c-labels').textContent);
const REVENUE = JSON.parse(document.getElementById('c-revenue').textContent);
const CASH    = JSON.parse(document.getElementById('c-cash').textContent);
const MOBILE  = JSON.parse(document.getElementById('c-mobile').textContent);
const CARD    = JSON.parse(document.getElementById('c-card').textContent);

/* ── Live date ── */
function updateClock() {
  const el = document.getElementById('live-date');
  if (!el) return;
  el.textContent = new Date().toLocaleDateString('en-TZ', {
    weekday: 'short', day: 'numeric',
    month: 'short', year: 'numeric',
  });
}

updateClock();
setInterval(updateClock, 60000);

/* ── Update payment stat cards ── */
function fmt(n) {
  return 'TZS ' + Math.round(n).toLocaleString('en-TZ');
}

document.getElementById('cash-val').textContent   = fmt(CASH);
document.getElementById('mobile-val').textContent = fmt(MOBILE);
document.getElementById('leg-cash').textContent   = fmt(CASH);
document.getElementById('leg-mobile').textContent = fmt(MOBILE);
document.getElementById('leg-card').textContent   = fmt(CARD);

/* ── Revenue bar chart ── */
const revenueCanvas = document.getElementById('revenue-chart');
if (revenueCanvas) {
  new Chart(revenueCanvas, {
    type: 'bar',
    data: {
      labels: LABELS,
      datasets: [{
        label:           'Revenue',
        data:            REVENUE,
        backgroundColor: 'rgba(196,164,93,0.7)',
        borderColor:     '#c4a45d',
        borderWidth:     1,
        borderRadius:    4,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ' TZS ' + ctx.parsed.y.toLocaleString(),
          },
        },
      },
      scales: {
        x: {
          grid:  { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#555', font: { size: 11 } },
        },
        y: {
          grid:  { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#555',
            font:  { size: 11 },
            callback: v => {
              if (v >= 1000000) return (v / 1000000).toFixed(1) + 'M';
              if (v >= 1000)    return (v / 1000).toFixed(0) + 'k';
              return v;
            },
          },
        },
      },
    },
  });
}

/* ── Percentage labels inside pie slices ── */
const percentagePlugin = {
  id: 'percentageLabels',
  afterDraw(chart) {
    const { ctx, data } = chart;
    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
    if (total === 0) return;

    chart.getDatasetMeta(0).data.forEach((arc, i) => {
      const value = data.datasets[0].data[i];
      const pct   = ((value / total) * 100).toFixed(1);
      if (parseFloat(pct) < 3) return;

      const midAngle = arc.startAngle + (arc.endAngle - arc.startAngle) / 2;
      const radius   = (arc.innerRadius + arc.outerRadius) / 2;
      const x        = arc.x + Math.cos(midAngle) * radius;
      const y        = arc.y + Math.sin(midAngle) * radius;

      ctx.save();
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle    = '#fff';
      ctx.font         = 'bold 11px DM Sans, sans-serif';
      ctx.fillText(pct + '%', x, y);
      ctx.restore();
    });
  },
};

/* ── Payment doughnut chart ── */
const payCanvas = document.getElementById('payment-chart');
if (payCanvas) {
  const total = CASH + MOBILE + CARD;

  new Chart(payCanvas, {
    type: 'doughnut',
    plugins: [percentagePlugin],
    data: {
      labels: ['Cash', 'Mobile money', 'Card'],
      datasets: [{
        data:            [CASH, MOBILE, CARD],
        backgroundColor: [
          'rgba(196,164,93,0.85)',
          'rgba(122,179,224,0.85)',
          'rgba(201,144,224,0.85)',
        ],
        borderColor:     '#111',
        borderWidth:     3,
        hoverBackgroundColor: ['#c4a45d', '#7ab3e0', '#c990e0'],
        hoverBorderColor:     ['#c4a45d', '#7ab3e0', '#c990e0'],
        hoverBorderWidth:     2,
        hoverOffset:     14,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      cutout:              '55%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const pct = total > 0
                ? ((ctx.parsed / total) * 100).toFixed(1)
                : 0;
              return ` TZS ${ctx.parsed.toLocaleString()} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}