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

// Init
document.addEventListener('DOMContentLoaded', () => {
  // Tab click events
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => setTab(btn.dataset.tab));
  });

  // Restore tab from URL hash
  const hash = location.hash.replace('#', '');
  const validTabs = ['overview', 'daily', 'channels'];
  const startTab = validTabs.includes(hash) ? hash : 'overview';

  setTab(startTab);
});
