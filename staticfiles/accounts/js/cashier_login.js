// Toggle password visibility
document.getElementById('toggle-password').addEventListener('click', function () {
  const input    = document.getElementById('id_password');
  const eyeOpen  = document.getElementById('eye-open');
  const eyeClosed = document.getElementById('eye-closed');

  if (input.type === 'password') {
    input.type = 'text';
    eyeOpen.style.display   = 'none';
    eyeClosed.style.display = 'block';
  } else {
    input.type = 'password';
    eyeOpen.style.display   = 'block';
    eyeClosed.style.display = 'none';
  }
});