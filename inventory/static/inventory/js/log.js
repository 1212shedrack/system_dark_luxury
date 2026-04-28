/* =============================================
   Inventory log — summary counters
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {
  const rows    = document.querySelectorAll('.log-row');
  let outTotal  = 0;
  let inTotal   = 0;

  rows.forEach(row => {
    const qty = parseInt(row.dataset.qty || 0);
    if (qty < 0) outTotal += Math.abs(qty);
    else         inTotal  += qty;
  });

  const outEl = document.getElementById('out-total');
  const inEl  = document.getElementById('in-total');

  if (outEl) outEl.textContent = outTotal;
  if (inEl)  inEl.textContent  = inTotal;
});

/* Auto-submit filter form on select change */
document.querySelectorAll('#filter-form select').forEach(sel => {
  sel.addEventListener('change', () => {
    document.getElementById('filter-form').submit();
  });
});