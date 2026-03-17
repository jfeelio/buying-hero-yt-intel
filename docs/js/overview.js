async function renderOverview() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Loading overview...</div>';

  let overview;
  try {
    overview = await fetchJSON('overview.json');
  } catch (e) {
    content.innerHTML = `
      <div class="no-data">
        <div class="no-data-icon">📭</div>
        <p>No overview data yet. The agent hasn't run yet, or this is the first setup.</p>
        <p style="margin-top:8px;font-size:12px;color:var(--text3)">Check back after the first daily run.</p>
      </div>`;
    return;
  }

  const updatedAt = new Date(overview.last_updated);
  const staleHours = (Date.now() - updatedAt.getTime()) / 3600000;
  document.getElementById('stale-banner').classList.toggle('hidden', staleHours <= 36);
  document.getElementById('last-updated-footer').textContent =
    `Last updated: ${updatedAt.toLocaleString('en-US', { timeZone: 'America/New_York' })} ET`;

  const acqLines = overview.top_acquisition_lines || [];
  const dispoLines = overview.top_disposition_lines || [];
  const lessons = overview.evergreen_lessons || [];
  const themes = overview.rolling_themes || [];
  const channels = overview.channel_activity || {};

  const totalChannels = Object.keys(channels).length;

  content.innerHTML = `
    <div class="section">
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value">${overview.days_tracked || 0}</span>
          <span class="stat-label">Days Tracked</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">${overview.total_videos_analyzed || 0}</span>
          <span class="stat-label">Videos Analyzed</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">${acqLines.length}</span>
          <span class="stat-label">Acquisition Lines</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">${dispoLines.length}</span>
          <span class="stat-label">Dispo Lines</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">${totalChannels}</span>
          <span class="stat-label">Active Channels</span>
        </div>
      </div>
    </div>

    <div class="section grid-2">
      <div class="card">
        <div class="card-title"><span class="icon">💡</span> Evergreen Lessons</div>
        ${renderLessonList(lessons)}
      </div>
      <div class="card">
        <div class="card-title"><span class="icon">📈</span> Rolling Themes</div>
        <div class="theme-tags">
          ${themes.map(t => `<span class="theme-tag">${t}</span>`).join('')}
        </div>
        ${Object.keys(channels).length > 0 ? `
          <div style="margin-top:20px;">
            <div class="insight-label">Channel Activity (last 30 days)</div>
            ${renderChannelActivity(channels)}
          </div>
        ` : ''}
      </div>
    </div>

    <div class="section grid-2">
      <div class="card">
        <div class="card-title"><span class="icon">📞</span> Top Acquisition Scripts</div>
        <p style="font-size:11px;color:var(--text3);margin-bottom:12px;">Click any line to copy to clipboard</p>
        ${renderScriptList(acqLines, false)}
      </div>
      <div class="card">
        <div class="card-title"><span class="icon">💰</span> Top Disposition Scripts</div>
        <p style="font-size:11px;color:var(--text3);margin-bottom:12px;">Click any line to copy to clipboard</p>
        ${renderScriptList(dispoLines, true)}
      </div>
    </div>
  `;

  // Bind copy events
  document.querySelectorAll('.script-list li').forEach(li => {
    li.addEventListener('click', () => {
      const text = li.querySelector('.script-text').textContent;
      copyToClipboard(text);
      li.classList.add('copied');
      showToast('Copied!');
      setTimeout(() => li.classList.remove('copied'), 1500);
    });
  });
}

function renderScriptList(lines, isDispo) {
  if (!lines.length) return '<p style="color:var(--text3);font-size:13px;">No scripts captured yet.</p>';
  return `<ul class="script-list">
    ${lines.map(l => `
      <li class="${isDispo ? 'dispo' : ''}">
        <span class="script-text">${escHtml(l)}</span>
        <span class="copy-hint">📋 copy</span>
      </li>`).join('')}
  </ul>`;
}

function renderLessonList(lessons) {
  if (!lessons.length) return '<p style="color:var(--text3);font-size:13px;">No lessons captured yet.</p>';
  return `<ul class="lesson-list">
    ${lessons.map((l, i) => `
      <li><span class="num">${i + 1}</span><span>${escHtml(l)}</span></li>
    `).join('')}
  </ul>`;
}

function renderChannelActivity(channels) {
  const sorted = Object.entries(channels).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const max = sorted[0]?.[1] || 1;
  return sorted.map(([name, count]) => `
    <div style="margin-bottom:6px;">
      <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
        <span style="color:var(--text2)">${escHtml(name)}</span>
        <span style="color:var(--text3)">${count} video${count !== 1 ? 's' : ''}</span>
      </div>
      <div style="height:4px;background:var(--bg3);border-radius:2px;">
        <div style="height:4px;background:var(--accent);border-radius:2px;width:${Math.round((count/max)*100)}%"></div>
      </div>
    </div>
  `).join('');
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
