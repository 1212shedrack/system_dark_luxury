/* =============================================
   Admin Dashboard JS
   Charts + live clock
   ============================================= */

/* ── Data ── */
const CHART_LABELS  = JSON.parse(document.getElementById('chart-labels').textContent);
const CHART_POS     = JSON.parse(document.getElementById('chart-pos').textContent);
const CHART_ORDERS  = JSON.parse(document.getElementById('chart-orders').textContent);
const TOP_NAMES     = JSON.parse(document.getElementById('top-names').textContent);
const TOP_QTYS      = JSON.parse(document.getElementById('top-qtys').textContent);
const TODAY_PAY     = JSON.parse(document.getElementById('today-pay').textContent);
const MONTH_PAY     = JSON.parse(document.getElementById('month-pay').textContent);
const ORDER_STATUS  = JSON.parse(document.getElementById('order-status').textContent);

/* ── Constants ── */
const PAY_LABELS     = ['Cash', 'Mobile money', 'Card'];
const PAY_COLORS     = ['#c4a45d', '#7ab3e0', '#c990e0'];
const STATUS_LABELS  = ['Pending', 'Confirmed', 'Processing', 'Completed', 'Cancelled'];
const STATUS_COLORS  = ['#c4a45d', '#7ab3e0', '#c990e0', '#6ecfb2', '#e07070'];
const GRID_COLOR     = 'rgba(255,255,255,0.04)';
const TICK_COLOR     = '#555';

/* ── Live clock ── */
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

/* ── Revenue bar chart ── */
function drawRevenue() {
  const canvas = document.getElementById('revenue-chart');
  if (!canvas) return;

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: CHART_LABELS,
      datasets: [
        {
          label:           'POS revenue',
          data:            CHART_POS,
          backgroundColor: 'rgba(196,164,93,0.75)',
          borderColor:     '#c4a45d',
          borderWidth:     1,
          borderRadius:    4,
        },
        {
          label:           'Order revenue',
          data:            CHART_ORDERS,
          backgroundColor: 'rgba(122,179,224,0.75)',
          borderColor:     '#7ab3e0',
          borderWidth:     1,
          borderRadius:    4,
        },
      ],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      barPercentage:       0.6,
      categoryPercentage:  0.7,
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
          grid:  { color: GRID_COLOR },
          ticks: { color: TICK_COLOR, font: { size: 11 } },
        },
        y: {
          grid:  { color: GRID_COLOR },
          ticks: {
            color: TICK_COLOR,
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

/* ── Top products horizontal bar ── */
function drawTopProducts() {
  const canvas = document.getElementById('top-products-chart');
  if (!canvas) return;

  const goldShades = [
    'rgba(196,164,93,0.95)',
    'rgba(196,164,93,0.78)',
    'rgba(196,164,93,0.62)',
    'rgba(196,164,93,0.46)',
    'rgba(196,164,93,0.30)',
  ];

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: TOP_NAMES,
      datasets: [{
        label:           'Units sold',
        data:            TOP_QTYS,
        backgroundColor: goldShades,
        borderColor:     '#c4a45d',
        borderWidth:     1,
        borderRadius:    6,
        hoverBackgroundColor: goldShades.map(() => '#c4a45d'),
      }],
    },
    options: {
      indexAxis:           'y',
      responsive:          true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ' ' + ctx.parsed.x + ' units sold',
          },
        },
      },
      scales: {
        x: {
          grid:  { color: GRID_COLOR },
          ticks: { color: TICK_COLOR, font: { size: 11 } },
        },
        y: {
          grid:  { display: false },
          ticks: { color: '#ccc', font: { size: 11 } },
        },
      },
    },
  });
}

/* ── Doughnut pie helper ── */
function drawPie(canvasId, data, labels, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor:      colors.map(c => c + 'bb'),
        borderColor:          '#111',
        borderWidth:          3,
        hoverBackgroundColor: colors,
        hoverBorderColor:     colors,
        hoverBorderWidth:     2,
        hoverOffset:          14,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      cutout:              '62%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct   = total > 0
                ? ((ctx.parsed / total) * 100).toFixed(1)
                : 0;
              return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* ── Draw everything ── */
drawRevenue();
drawTopProducts();
drawPie('today-pay-chart',    TODAY_PAY,    PAY_LABELS,    PAY_COLORS);
drawPie('month-pay-chart',    MONTH_PAY,    PAY_LABELS,    PAY_COLORS);
drawPie('order-status-chart', ORDER_STATUS, STATUS_LABELS, STATUS_COLORS);