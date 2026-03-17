async function renderChannels() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Loading channels...</div>';

  let channelsData;
  try {
    channelsData = await fetchJSON('channels.json');
  } catch (e) {
    content.innerHTML = `<div class="no-data"><p>Could not load channels data.</p></div>`;
    return;
  }

  const channels = channelsData.channels || [];
  const enabled = channels.filter(c => c.enabled !== false).length;

  content.innerHTML = `
    <div style="margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <div>
        <h2 style="font-size:18px;font-weight:700;color:var(--text)">Tracked Channels</h2>
        <p style="font-size:13px;color:var(--text3)">${enabled} of ${channels.length} channels active</p>
      </div>
    </div>

    <div class="card" style="overflow-x:auto;">
      <table class="channels-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Channel</th>
            <th>Handle</th>
            <th>Focus</th>
            <th>Added</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          ${channels.map(ch => renderChannelRow(ch)).join('')}
        </tbody>
      </table>
    </div>

    <div class="add-channel-info">
      <h3>➕ How to Add or Remove a Channel</h3>
      <p>This dashboard is powered by <code>docs/data/channels.json</code> in the GitHub repository.
      To add or remove a channel:</p>
      <ol style="margin:10px 0 0 20px;line-height:2;">
        <li>Go to the <a href="https://github.com/jfeelio/buying-hero-yt-intel/blob/master/docs/data/channels.json" target="_blank">channels.json file on GitHub</a></li>
        <li>Click the pencil icon to edit</li>
        <li>To disable a channel, set <code>"enabled": false</code></li>
        <li>To add a channel, add a new entry with the YouTube channel ID and name</li>
        <li>Commit the change — the next daily run will pick it up</li>
      </ol>
      <p style="margin-top:12px;font-size:12px;color:var(--text3)">
        💡 Need a channel's YouTube ID? Search "<em>channel name youtube channel ID</em>" or visit
        their YouTube page and look in the URL or page source.
      </p>
    </div>
  `;
}

function renderChannelRow(ch) {
  const isEnabled = ch.enabled !== false;
  const handle = ch.handle || '';
  const youtubeUrl = handle
    ? `https://youtube.com/${handle}`
    : (ch.id ? `https://youtube.com/channel/${ch.id}` : '#');

  const tags = (ch.tags || []).map(t => `<span class="channel-tag">${escHtmlCh(t)}</span>`).join('');

  return `
    <tr>
      <td>
        <span class="status-dot ${isEnabled ? 'on' : 'off'}"></span>
        ${isEnabled ? 'Active' : 'Disabled'}
      </td>
      <td style="font-weight:600;color:var(--text)">${escHtmlCh(ch.name)}</td>
      <td style="color:var(--text3);font-family:monospace;font-size:12px">${escHtmlCh(handle)}</td>
      <td>${tags || '<span style="color:var(--text3)">—</span>'}</td>
      <td style="color:var(--text3);font-size:12px">${escHtmlCh(ch.added || '—')}</td>
      <td>
        ${youtubeUrl !== '#' ? `
          <a href="${escHtmlCh(youtubeUrl)}" target="_blank" rel="noopener"
            style="color:var(--accent);font-size:12px;text-decoration:none;">
            ▶ YouTube
          </a>` : '—'}
      </td>
    </tr>
  `;
}

function escHtmlCh(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
