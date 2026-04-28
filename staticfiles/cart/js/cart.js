function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

document.querySelectorAll('.qty-form').forEach(form => {
  form.addEventListener('submit', () => {
    showToast('Cart updated ✓');
  });
});

document.querySelectorAll('.remove-btn').forEach(link => {
  link.addEventListener('click', e => {
    if (!confirm('Remove this item from your cart?')) e.preventDefault();
  });
});

document.querySelectorAll('.qty-input').forEach(input => {
  input.addEventListener('focus', () => input.select());
});