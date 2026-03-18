let allDates = [];
let currentDateIndex = 0;

async function renderDaily(targetDate) {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Loading daily feed...</div>';

  // Load index
  try {
    const index = await fetchJSON('index.json');
    allDates = index.dates || [];
  } catch (e) {
    allDates = [];
  }

  if (!allDates.length) {
    content.innerHTML = `
      <div class="no-data">
        <div class="no-data-icon">📭</div>
        <p>No daily data yet. The agent runs every morning at 6 AM ET.</p>
      </div>`;
    return;
  }

  // Determine which date to show
  if (targetDate && allDates.includes(targetDate)) {
    currentDateIndex = allDates.indexOf(targetDate);
  } else {
    currentDateIndex = 0; // newest
  }

  await renderDayContent(content);
}

async function renderDayContent(content) {
  const dateStr = allDates[currentDateIndex];
  let dayData;

  try {
    dayData = await fetchJSON(`${dateStr}.json`);
  } catch (e) {
    content.innerHTML = `
      ${renderDateNav(dateStr)}
      <div class="no-data">
        <div class="no-data-icon">⚠️</div>
        <p>No data available for ${formatDate(dateStr)}.</p>
        <p style="margin-top:8px;font-size:12px;color:var(--text3)">The agent may have encountered an error on this day.</p>
      </div>`;
    bindDateNavEvents(content);
    return;
  }

  const videos = dayData.videos || [];
  const channels = [...new Set(videos.map(v => v.channel))].sort();

  content.innerHTML = `
    ${renderDateNav(dateStr, dayData)}
    <div class="channel-filter">
      <label>Filter by channel:</label>
      <select id="channel-filter">
        <option value="">All channels (${videos.length} videos)</option>
        ${channels.map(ch => `<option value="${escHtml(ch)}">${escHtml(ch)}</option>`).join('')}
      </select>
    </div>

    ${dayData.daily_themes?.length ? `
      <div class="section card" style="margin-bottom:20px;">
        <div class="card-title"><span class="icon">📈</span> Today's Themes</div>
        <div class="theme-list">
          ${dayData.daily_themes.map(t => {
            const theme = typeof t === 'string' ? t : t.theme;
            const url = t?.video_url || null;
            const title = t?.video_title || null;
            const channel = t?.channel || null;
            return `
              <div class="theme-item">
                <span class="theme-tag">${escHtml(theme)}</span>
                ${url ? `<a class="theme-source" href="${escHtml(url)}" target="_blank" rel="noopener">▶ ${escHtml(channel)} — ${escHtml(title)}</a>` : ''}
              </div>`;
          }).join('')}
        </div>
      </div>
    ` : ''}

    <div id="video-list">
      ${videos.length ? videos.map(v => renderVideoCard(v)).join('') : `
        <div class="no-data">
          <div class="no-data-icon">🎬</div>
          <p>No videos with sufficient wholesaling relevance were found today.</p>
        </div>
      `}
    </div>
  `;

  bindDateNavEvents(content);
  bindVideoCards();
  bindChannelFilter(videos);
}

function renderDateNav(dateStr, dayData) {
  const canPrev = currentDateIndex < allDates.length - 1;
  const canNext = currentDateIndex > 0;
  const analyzed = dayData?.videos_analyzed || 0;
  const found = dayData?.videos_found || 0;

  return `
    <div class="date-nav">
      <button id="btn-prev" ${canPrev ? '' : 'disabled'}>← Older</button>
      <div>
        <div class="date-display">${formatDate(dateStr)}</div>
        ${dayData ? `<div class="date-sub">${analyzed} videos analyzed of ${found} found</div>` : ''}
      </div>
      <button id="btn-next" ${canNext ? '' : 'disabled'}>Newer →</button>
    </div>
  `;
}

function bindDateNavEvents(content) {
  const prevBtn = content.querySelector('#btn-prev');
  const nextBtn = content.querySelector('#btn-next');

  prevBtn?.addEventListener('click', async () => {
    currentDateIndex++;
    await renderDayContent(content);
  });

  nextBtn?.addEventListener('click', async () => {
    currentDateIndex--;
    await renderDayContent(content);
  });
}

function bindChannelFilter(allVideos) {
  const select = document.getElementById('channel-filter');
  const list = document.getElementById('video-list');
  if (!select || !list) return;

  select.addEventListener('change', () => {
    const ch = select.value;
    const filtered = ch ? allVideos.filter(v => v.channel === ch) : allVideos;
    list.innerHTML = filtered.length
      ? filtered.map(v => renderVideoCard(v)).join('')
      : '<div class="no-data"><p>No videos from this channel today.</p></div>';
    bindVideoCards();
  });
}

function renderVideoCard(video) {
  const insights = video.insights || {};
  const relevance = (insights.market_relevance || 'low').toLowerCase().split('/')[0].trim();
  const badgeClass = relevance === 'high' ? 'high' : relevance === 'medium' ? 'medium' : 'low';

  return `
    <div class="video-card" data-id="${escHtml(video.video_id)}">
      <div class="video-header">
        <img class="video-thumb" src="${escHtml(video.thumbnail || '')}" alt="" loading="lazy"
          onerror="this.style.display='none'">
        <div class="video-meta">
          <div class="video-title" title="${escHtml(video.title)}">${escHtml(video.title)}</div>
          <div>
            <span class="video-channel">${escHtml(video.channel)}</span>
          </div>
          <div class="video-stats">
            <span>👁 ${formatViews(video.view_count || 0)}</span>
            <span>🕐 ${timeAgo(video.published_at)}</span>
            ${video.transcript_available === false ? '<span style="color:var(--text3)">⚠️ No transcript</span>' : ''}
          </div>
        </div>
        <div>
          <span class="relevance-badge ${badgeClass}">${insights.market_relevance || 'N/A'}</span>
        </div>
      </div>

      ${insights.summary ? `
        <div class="video-insights" id="insights-${escHtml(video.video_id)}">
          <div class="insight-section">
            <div class="insight-label">Summary</div>
            <div class="insight-summary">${escHtml(insights.summary || '')}</div>
          </div>

          ${renderInsightSection('Key Lessons', insights.key_lessons)}
          ${renderScriptSection('📞 Acquisition One-Liners', insights.acquisition_one_liners, false)}
          ${renderScriptSection('💰 Disposition One-Liners', insights.disposition_one_liners, true)}
          ${renderInsightSection('Tips & Tricks', insights.tips_and_tricks)}
          ${renderInsightSection('Trends', insights.trends)}

          ${insights.south_florida_relevance ? `
            <div class="insight-section">
              <div class="insight-label">🌴 South Florida Relevance</div>
              <div class="insight-summary" style="border-left:3px solid var(--gold)">
                ${escHtml(insights.south_florida_relevance)}
              </div>
            </div>
          ` : ''}

          <a class="video-link" href="${escHtml(video.url)}" target="_blank" rel="noopener">
            ▶ Watch on YouTube →
          </a>
        </div>
      ` : `
        <div class="video-insights" id="insights-${escHtml(video.video_id)}">
          <p style="color:var(--text3);font-size:13px;">
            ${video.transcript_available === false
              ? 'No transcript available — analysis skipped.'
              : 'This video was skipped due to low wholesaling relevance.'}
          </p>
          <a class="video-link" href="${escHtml(video.url)}" target="_blank" rel="noopener">▶ Watch on YouTube →</a>
        </div>
      `}
    </div>
  `;
}

function renderInsightSection(label, items) {
  if (!items?.length) return '';
  return `
    <div class="insight-section">
      <div class="insight-label">${label}</div>
      <ul class="insight-list">
        ${items.map(item => `<li>${escHtml(item)}</li>`).join('')}
      </ul>
    </div>
  `;
}

function renderScriptSection(label, lines, isDispo) {
  if (!lines?.length) return '';
  return `
    <div class="insight-section">
      <div class="insight-label">${label} <span style="font-size:10px;color:var(--text3)">(click to copy)</span></div>
      <ul class="script-list">
        ${lines.map(l => `
          <li class="${isDispo ? 'dispo' : ''}">
            <span class="script-text">${escHtml(l)}</span>
            <span class="copy-hint">📋 copy</span>
          </li>
        `).join('')}
      </ul>
    </div>
  `;
}

function bindVideoCards() {
  // Toggle expand/collapse
  document.querySelectorAll('.video-header').forEach(header => {
    header.addEventListener('click', () => {
      const card = header.closest('.video-card');
      const id = card.dataset.id;
      const insights = document.getElementById(`insights-${id}`);
      if (insights) insights.classList.toggle('open');
    });
  });

  // Copy script lines
  document.querySelectorAll('.script-list li').forEach(li => {
    li.addEventListener('click', (e) => {
      e.stopPropagation();
      const text = li.querySelector('.script-text')?.textContent;
      if (text) {
        copyToClipboard(text);
        li.classList.add('copied');
        showToast('Copied!');
        setTimeout(() => li.classList.remove('copied'), 1500);
      }
    });
  });
}

function escHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
