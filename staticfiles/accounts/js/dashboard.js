function toggleMenu() {
  const sidebar      = document.getElementById('sidebar');
  const mobileMenu   = document.getElementById('mobileMenu');
  const overlay      = document.getElementById('sidebarOverlay');

  // on mobile — toggle sidebar slide-in
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
  }

  // mobile dropdown menu (below topbar)
  mobileMenu.classList.toggle('open');
}

// close sidebar when screen resizes to desktop
window.addEventListener('resize', function () {
  if (window.innerWidth > 768) {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('open');
    document.getElementById('mobileMenu').classList.remove('open');
  }
});

// highlight active sidebar link
document.querySelectorAll('#sidebar-links a').forEach(link => {
  if (link.href === window.location.href) {
    link.classList.add('active');
  }
});