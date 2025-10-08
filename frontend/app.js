const API = 'http://localhost:8080/api';

document.getElementById('btnHealth').addEventListener('click', async () => {
  const out = document.getElementById('output');
  out.textContent = 'Calling /api/health...';
  try {
    const res = await fetch(`${API}/health`);
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = 'Error: ' + err.message;
  }
});
