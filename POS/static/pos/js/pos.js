/* =============================================
   POS Terminal JavaScript
   Cart management + AJAX sale processing
   ============================================= */

let cart = {};           // { productId: { name, price, stock, qty } }
let paymentMethod = 'cash';

/* ─── Cart operations ─────────────────────────────────────── */

function addToCart(id, name, price, quantity) {
  if (cart[id]) {
    if (cart[id].qty >= quantity) {
      flashMsg(`Only ${quantity} in quantity`);
      return;
    }
    cart[id].qty += 1;
  } else {
    cart[id] = { name, price: parseFloat(price), quantity, qty: 1 };
  }
  renderCart();
  flashTile(id);
}

function updateQty(id, delta) {
  if (!cart[id]) return;
  const newQty = cart[id].qty + delta;
  if (newQty <= 0) {
    delete cart[id];
  } else if (newQty > cart[id].quantity) {
    flashMsg(`Only ${cart[id].quantity} in quantity`);
    return;
  } else {
    cart[id].qty = newQty;
  }
  renderCart();
}

function removeItem(id) {
  delete cart[id];
  renderCart();
}

function voidCart() {
  if (Object.keys(cart).length === 0) return;
  if (!confirm('Void this sale?')) return;
  cart = {};
  renderCart();
}

/* ─── Render cart ─────────────────────────────────────────── */

function renderCart() {
  const items     = Object.entries(cart);
  const emptyEl   = document.getElementById('cart-empty');
  const itemsEl   = document.getElementById('cart-items');
  const totalQtyEl  = document.getElementById('total-qty');
  const totalAmtEl  = document.getElementById('total-amount');
  const chargeBtn   = document.getElementById('btn-charge');

  emptyEl.style.display = items.length ? 'none' : 'flex';

  let totalQty = 0;
  let totalAmt = 0;

  itemsEl.innerHTML = items.map(([id, item]) => {
    totalQty += item.qty;
    totalAmt += item.price * item.qty;
    return `
      <div class="cart-item">
        <span class="ci-name" title="${item.name}">${item.name}</span>
        <div class="ci-qty">
          <button class="ci-qty-btn" onclick="updateQty(${id}, -1)">−</button>
          <span class="ci-qty-num">${item.qty}</span>
          <button class="ci-qty-btn" onclick="updateQty(${id}, 1)">+</button>
        </div>
        <span class="ci-subtotal">${fmt(item.price * item.qty)}</span>
        <button class="ci-remove" onclick="removeItem(${id})" title="Remove">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>`;
  }).join('');

  totalQtyEl.textContent = totalQty;
  totalAmtEl.textContent = fmt(totalAmt);
  chargeBtn.disabled = items.length === 0;

  renderQuickAmounts(totalAmt);
  calcChange();
}

/* ─── Payment ─────────────────────────────────────────────── */

function setPayment(btn) {
  document.querySelectorAll('.pm-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  paymentMethod = btn.dataset.method;
  const cashWrap = document.getElementById('cash-tendered-wrap');
  cashWrap.style.display = paymentMethod === 'cash' ? 'block' : 'none';
  calcChange();
}

function calcChange() {
  const totalAmt = Object.values(cart).reduce((s, i) => s + i.price * i.qty, 0);
  const paid     = parseFloat(document.getElementById('amount-paid').value) || 0;
  const change   = Math.max(0, paid - totalAmt);
  document.getElementById('change-due').textContent = fmt(change);
}

function renderQuickAmounts(total) {
  const wrap = document.getElementById('quick-amounts');
  const rounded = [
    Math.ceil(total / 1000) * 1000,
    Math.ceil(total / 5000) * 5000,
    Math.ceil(total / 10000) * 10000,
  ];
  const unique = [...new Set(rounded)].slice(0, 3);
  wrap.innerHTML = unique.map(amt =>
    `<button class="quick-amt-btn" onclick="setTendered(${amt})">${fmtShort(amt)}</button>`
  ).join('');
}

function setTendered(amount) {
  document.getElementById('amount-paid').value = amount;
  calcChange();
}

/* ─── Process sale ────────────────────────────────────────── */

async function processSale() {
  const items = Object.entries(cart).map(([id, item]) => ({
    product_id: parseInt(id),
    quantity:   item.qty,
  }));

  if (items.length === 0) return;

  const amountPaid = paymentMethod === 'cash'
    ? (parseFloat(document.getElementById('amount-paid').value) || 0)
    : Object.values(cart).reduce((s, i) => s + i.price * i.qty, 0);

  showOverlay('Processing sale…');

  try {
    const res  = await fetch(PROCESS_URL, {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken':  CSRF,
      },
      body: JSON.stringify({
        items,
        payment_method: paymentMethod,
        amount_paid:    amountPaid,
      }),
    });

    const data = await res.json();

    if (data.success) {
      showOverlay(`Sale complete!\nChange: ${fmt(data.change)}`);
      setTimeout(() => {
        cart = {};
        renderCart();
        hideOverlay();
       window.location.href = RECEIPT_BASE_URL + data.sale_id + '/';
      }, 1200);
    } else {
      hideOverlay();
      flashMsg(data.error || 'Sale failed.');
    }
  } catch (err) {
    hideOverlay();
    flashMsg('Network error. Please try again.');
  }
}

/* ─── Product search ──────────────────────────────────────── */

let searchTimer;

document.getElementById('search-input').addEventListener('input', function () {
  clearTimeout(searchTimer);
  const q = this.value.trim();
  if (q.length < 1) {
    closeSearch();
    return;
  }
  searchTimer = setTimeout(() => doSearch(q), 280);
});

document.getElementById('search-input').addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeSearch();
});

document.addEventListener('click', function (e) {
  if (!e.target.closest('.pos-search-bar')) closeSearch();
});

async function doSearch(q) {
  try {
    const res  = await fetch(`${SEARCH_URL}?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderSearchResults(data.results);
  } catch { /* silent */ }
}

function renderSearchResults(results) {
  const box = document.getElementById('search-results');
  if (!results.length) {
    box.innerHTML = '<div class="search-result-item"><span class="sr-name" style="color:#555">No results</span></div>';
  } else {
    box.innerHTML = results.map(p => `
      <div class="search-result-item" onclick="addToCart(${p.id}, '${p.name.replace(/'/g,"\\'")}', ${p.price}, ${p.quantity}); closeSearch()">
        <span class="sr-name">${p.name}</span>
        <span class="sr-price">${fmt(p.price)}</span>
        <span class="sr-quantity">${p.quantity} left</span>
      </div>
    `).join('');
  }
  box.classList.add('open');
}

function closeSearch() {
  document.getElementById('search-results').classList.remove('open');
  document.getElementById('search-input').value = '';
}

/* ─── Helpers ─────────────────────────────────────────────── */

function fmt(n) {
  return 'TZS ' + Math.round(n).toLocaleString('en-TZ');
}

function fmtShort(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000)    return (n / 1000).toFixed(0) + 'k';
  return n.toString();
}

function flashMsg(msg) {
  const el = document.createElement('div');
  el.textContent = msg;
  el.style.cssText = `position:fixed;bottom:80px;left:50%;transform:translateX(-50%);
    background:#1a1a1a;border:1px solid #ef4444;color:#ef4444;padding:8px 18px;
    border-radius:8px;font-size:12px;z-index:999;font-family:inherit;`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}

function flashTile(id) {
  const tile = document.querySelector(`.product-tile[data-id="${id}"]`);
  if (!tile) return;
  tile.style.borderColor = '#4ade80';
  setTimeout(() => tile.style.borderColor = '', 300);
}

function showOverlay(msg) {
  document.getElementById('overlay-msg').textContent = msg;
  document.getElementById('overlay').style.display = 'flex';
}

function hideOverlay() {
  document.getElementById('overlay').style.display = 'none';
}

/* ─── Init ────────────────────────────────────────────────── */
renderCart();
