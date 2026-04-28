/* =============================================
   Inventory overview — search, filter, validate
   ============================================= */

const searchInput  = document.getElementById('search-input');
const statusFilter = document.getElementById('status-filter');
const tbody        = document.getElementById('inv-tbody');
const noResults    = document.getElementById('no-results');

function filterTable() {
  const query  = searchInput.value.toLowerCase().trim();
  const status = statusFilter.value;
  const rows   = tbody.querySelectorAll('tr[data-name]');
  let visible  = 0;

  rows.forEach(row => {
    const nameMatch   = row.dataset.name.includes(query);
    const statusMatch = !status || row.dataset.status === status;
    const show        = nameMatch && statusMatch;
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });

  noResults.style.display = visible === 0 ? 'block' : 'none';
}

searchInput.addEventListener('input', filterTable);
statusFilter.addEventListener('change', filterTable);

/* Restock validation */
function validateRestock(form) {
  const qty = parseInt(form.querySelector('.restock-input').value);
  if (!qty || qty < 1) {
    alert('Please enter a quantity of at least 1.');
    return false;
  }
  return true;
}

/* Auto-hide Django messages after 3s */
document.querySelectorAll('.messages li').forEach(msg => {
  setTimeout(() => {
    msg.style.transition = 'opacity .5s';
    msg.style.opacity    = '0';
    setTimeout(() => msg.remove(), 500);
  }, 3000);
});