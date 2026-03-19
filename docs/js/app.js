// Router
let currentTab = 'overview';

function setTab(tab) {
  currentTab = tab;

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });

  switch (tab) {
    case 'overview': renderOverview(); break;
    case 'daily':    renderDaily();    break;
    case 'channels': renderChannels(); break;
  }

  // Update URL hash without scrolling
  history.replaceState(null, '', '#' + tab);
}

// ── Run Now ──
const REPO = 'jfeelio/buying-hero-yt-intel';
const WORKFLOW = 'daily_run.yml';
const TOKEN_KEY = 'gh_run_token';

async function triggerRun() {
  const btn = document.getElementById('run-now-btn');

  let token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    token = prompt('Enter a GitHub PAT with "workflow" scope:\n(saved locally, never leaves your browser)');
    if (!token) return;
    localStorage.setItem(TOKEN_KEY, token.trim());
    token = token.trim();
  }

  btn.disabled = true;
  btn.classList.add('running');
  btn.textContent = '⏳ Triggering...';

  try {
    const res = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/vnd.github+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ref: 'master' }),
      }
    );

    if (res.status === 204) {
      btn.classList.remove('running');
      btn.classList.add('success');
      btn.textContent = '✓ Triggered';
      setTimeout(() => {
        btn.classList.remove('success');
        btn.textContent = '▶ Run Now';
        btn.disabled = false;
      }, 4000);
    } else if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      btn.classList.remove('running');
      btn.classList.add('error');
      btn.textContent = '✗ Bad token';
      setTimeout(() => {
        btn.classList.remove('error');
        btn.textContent = '▶ Run Now';
        btn.disabled = false;
      }, 3000);
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (e) {
    btn.classList.remove('running');
    btn.classList.add('error');
    btn.textContent = '✗ Failed';
    setTimeout(() => {
      btn.classList.remove('error');
      btn.textContent = '▶ Run Now';
      btn.disabled = false;
    }, 3000);
  }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  // Tab click events
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => setTab(btn.dataset.tab));
  });

  // Run Now button
  document.getElementById('run-now-btn').addEventListener('click', triggerRun);

  // Right-click to reset saved token
  document.getElementById('run-now-btn').addEventListener('contextmenu', (e) => {
    e.preventDefault();
    if (confirm('Reset saved GitHub token?')) localStorage.removeItem(TOKEN_KEY);
  });

  // Restore tab from URL hash
  const hash = location.hash.replace('#', '');
  const validTabs = ['overview', 'daily', 'channels'];
  const startTab = validTabs.includes(hash) ? hash : 'overview';

  setTab(startTab);
});
