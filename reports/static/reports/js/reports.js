/* ── Read data ── */
const R_LABELS     = JSON.parse(document.getElementById('r-labels')?.textContent     || '[]');
const R_POS        = JSON.parse(document.getElementById('r-pos')?.textContent        || '[]');
const R_ORDERS     = JSON.parse(document.getElementById('r-orders')?.textContent     || '[]');
const R_TOP_NAMES  = JSON.parse(document.getElementById('r-top-names')?.textContent  || '[]');
const R_TOP_QTYS   = JSON.parse(document.getElementById('r-top-qtys')?.textContent   || '[]');
const R_CAT_LABELS = JSON.parse(document.getElementById('r-cat-labels')?.textContent || '[]');
const R_CAT_DATA   = JSON.parse(document.getElementById('r-cat-data')?.textContent   || '[]');
const R_PAY_DATA   = JSON.parse(document.getElementById('r-pay-data')?.textContent   || '[]');
const ORD_PENDING   = JSON.parse(document.getElementById('r-ord-pending')?.textContent   || '0');
const ORD_COMPLETED = JSON.parse(document.getElementById('r-ord-completed')?.textContent || '0');
const ORD_CANCELLED = JSON.parse(document.getElementById('r-ord-cancelled')?.textContent || '0');
const ORD_CONFIRMED = JSON.parse(document.getElementById('r-ord-confirmed')?.textContent || '0');
const ORD_PROCESSING = JSON.parse(document.getElementById('r-ord-processing')?.textContent || '0');

/* ── Constants ── */
const GRID = 'rgba(255,255,255,0.04)';
const TICK = '#555';

const PAY_LABELS    = ['Cash', 'Mobile money', 'Card'];
const PAY_COLORS    = ['#c4a45d', '#7ab3e0', '#c990e0'];

const CAT_COLORS    = [
  '#c4a45d', '#7ab3e0', '#c990e0',
  '#6ecfb2', '#e07070', '#f0a070',
];

const ORDER_STATUS_DATA   = [ORD_PENDING, 0, 0, ORD_COMPLETED, ORD_CANCELLED, ORD_CONFIRMED, ORD_PROCESSING];
const ORDER_STATUS_LABELS = ['Pending', 'Confirmed', 'Processing', 'Completed', 'Cancelled'];
const ORDER_STATUS_COLORS = ['#c4a45d', '#7ab3e0', '#c990e0', '#6ecfb2', '#e07070'];

/* ── Percentage labels inside doughnut slices ── */
const pctPlugin = {
  id: 'pctLabels',
  afterDraw(chart) {
    const { ctx, data } = chart;
    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
    if (total === 0) return;

    chart.getDatasetMeta(0).data.forEach((arc, i) => {
      const val = data.datasets[0].data[i];
      const pct = ((val / total) * 100).toFixed(1);
      if (parseFloat(pct) < 4) return;

      const mid    = arc.startAngle + (arc.endAngle - arc.startAngle) / 2;
      const radius = (arc.innerRadius + arc.outerRadius) / 2;
      const x      = arc.x + Math.cos(mid) * radius;
      const y      = arc.y + Math.sin(mid) * radius;

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

/* ── Revenue bar chart ── */
function drawRevenue() {
  const canvas = document.getElementById('revenue-chart');
  if (!canvas) return;

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: R_LABELS,
      datasets: [
        {
          label:           'POS',
          data:            R_POS,
          backgroundColor: 'rgba(196,164,93,0.75)',
          borderColor:     '#c4a45d',
          borderWidth:     1,
          borderRadius:    4,
        },
        {
          label:           'Orders',
          data:            R_ORDERS,
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
      barPercentage:       0.7,
      categoryPercentage:  0.5,
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
          grid:  { color: GRID },
          ticks: { color: TICK, font: { size: 11 } },
        },
        y: {
          grid:  { color: GRID },
          ticks: {
            color: TICK,
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
  const canvas = document.getElementById('top-chart');
  if (!canvas) return;

  const shades = [
    'rgba(196,164,93,0.95)', 'rgba(196,164,93,0.80)',
    'rgba(196,164,93,0.65)', 'rgba(196,164,93,0.50)',
    'rgba(196,164,93,0.38)', 'rgba(196,164,93,0.26)',
    'rgba(196,164,93,0.18)', 'rgba(196,164,93,0.12)',
  ];

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: R_TOP_NAMES,
      datasets: [{
        data:                 R_TOP_QTYS,
        backgroundColor:      shades,
        hoverBackgroundColor: shades.map(() => '#c4a45d'),
        borderColor:          '#c4a45d',
        borderWidth:          1,
        borderRadius:         6,
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
          grid:  { color: GRID },
          ticks: { color: TICK, font: { size: 11 } },
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
    type:    'doughnut',
    plugins: [pctPlugin],
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
      cutout:              '55%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct   = total > 0
                ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* ── Draw all — called once ── */
drawRevenue();
drawTopProducts();
drawPie('pay-chart',   R_PAY_DATA,        PAY_LABELS,          PAY_COLORS);
drawPie('cat-chart',   R_CAT_DATA,        R_CAT_LABELS,        CAT_COLORS);
drawPie('order-chart', ORDER_STATUS_DATA, ORDER_STATUS_LABELS, ORDER_STATUS_COLORS);