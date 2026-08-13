/**
 * Claude Usage Monitor — Client Application Script
 */

document.addEventListener('DOMContentLoaded', () => {
  // Tab Navigation
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(`tab-${targetTab}`).classList.add('active');

      if (targetTab === 'history') {
        loadHistory(24);
      } else if (targetTab === 'settings') {
        loadSettings();
      }
    });
  });

  // Theme Toggle
  const themeToggleBtn = document.getElementById('btn-theme-toggle');
  const themeLabel = document.getElementById('theme-toggle-label');

  let currentTheme = 'dark';
  themeToggleBtn.addEventListener('click', () => {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    themeLabel.textContent = currentTheme === 'dark' ? 'DARK MODE' : 'LIGHT MODE';
  });

  // Manual Refresh Button
  document.getElementById('btn-refresh').addEventListener('click', () => {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.refresh_now();
    }
  });

  // History Range Buttons
  const rangeBtns = document.querySelectorAll('.range-btn');
  rangeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      rangeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const hours = parseInt(btn.getAttribute('data-range'), 10);
      loadHistory(hours);
    });
  });

  // Settings Form Submit
  document.getElementById('settings-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const pollInterval = parseInt(document.getElementById('setting-poll-interval').value, 10);
    const warningThresh = parseFloat(document.getElementById('setting-warning-threshold').value);
    const criticalThresh = parseFloat(document.getElementById('setting-critical-threshold').value);
    const startup = document.getElementById('setting-startup').checked;
    const customToken = document.getElementById('setting-custom-token').value.trim();

    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.save_settings({
        poll_interval: pollInterval,
        warning_threshold: warningThresh,
        critical_threshold: criticalThresh,
        run_at_startup: startup,
        theme: currentTheme,
        custom_token: customToken
      }).then(() => {
        const saveToast = document.getElementById('save-toast');
        saveToast.classList.add('show');
        setTimeout(() => saveToast.classList.remove('show'), 2000);
      });
    }
  });

  // Poll for data periodically from Python backend
  window.addEventListener('pywebviewready', () => {
    loadOverview();
    setInterval(loadOverview, 5000);
  });
});

function loadOverview() {
  if (!window.pywebview || !window.pywebview.api) return;

  window.pywebview.api.get_overview().then(data => {
    if (!data) return;

    // Update Status Banner
    const statusDot = document.getElementById('status-dot');
    const statusLabel = document.getElementById('status-label');
    const statusTime = document.getElementById('status-time');

    statusLabel.textContent = data.status || 'CONNECTED';
    statusTime.textContent = `Updated ${data.last_updated || '--:--'}`;

    if (data.status === 'SAFE') {
      statusDot.style.backgroundColor = 'var(--status-safe)';
    } else if (data.status === 'WARNING') {
      statusDot.style.backgroundColor = 'var(--status-warning)';
    } else if (data.status === 'CRITICAL') {
      statusDot.style.backgroundColor = 'var(--status-critical)';
    } else {
      statusDot.style.backgroundColor = 'var(--status-offline)';
    }

    // 5-Hour Window
    document.getElementById('fh-val').textContent = data.five_hour.utilization.toFixed(0);
    document.getElementById('fh-bar').style.width = `${Math.min(data.five_hour.utilization, 100)}%`;
    document.getElementById('fh-reset').textContent = `Resets in ${data.five_hour.relative_reset}`;
    document.getElementById('fh-reset-exact').textContent = data.five_hour.resets_at ? `Resets: ${data.five_hour.resets_at}` : '';

    // Weekly Window
    document.getElementById('sd-val').textContent = data.seven_day.utilization.toFixed(0);
    document.getElementById('sd-bar').style.width = `${Math.min(data.seven_day.utilization, 100)}%`;
    document.getElementById('sd-reset').textContent = `Resets in ${data.seven_day.relative_reset}`;
    document.getElementById('sd-reset-exact').textContent = data.seven_day.resets_at ? `Resets: ${data.seven_day.resets_at}` : '';

    // Analytics Summary
    if (data.analytics) {
      document.getElementById('analytics-summary').textContent = data.analytics.summary || 'Usage is steady.';
      document.getElementById('stat-peak-5h').textContent = `${data.analytics.peak_today_5h}%`;
      document.getElementById('stat-peak-weekly').textContent = `${data.analytics.peak_today_weekly}%`;
      document.getElementById('stat-velocity').textContent = `${data.analytics.rate_per_hour}%/hr`;
    }
  });
}

function loadHistory(hours) {
  if (!window.pywebview || !window.pywebview.api) return;

  window.pywebview.api.get_history(hours).then(records => {
    renderSVGChart(records || []);
  });
}

function loadSettings() {
  if (!window.pywebview || !window.pywebview.api) return;

  window.pywebview.api.get_settings().then(s => {
    if (!s) return;
    document.getElementById('setting-poll-interval').value = s.poll_interval || 15;
    document.getElementById('setting-warning-threshold').value = s.warning_threshold || 80;
    document.getElementById('setting-critical-threshold').value = s.critical_threshold || 90;
    document.getElementById('setting-startup').checked = !!s.run_at_startup;
  });
}

function renderSVGChart(records) {
  const svg = document.getElementById('history-chart');
  svg.innerHTML = ''; // Clear

  if (!records || records.length === 0) {
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', '50%');
    text.setAttribute('y', '50%');
    text.setAttribute('dominant-baseline', 'middle');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', 'var(--text-muted)');
    text.setAttribute('font-size', '12');
    text.textContent = 'No usage history recorded yet.';
    svg.appendChild(text);
    return;
  }

  const width = 560;
  const height = 180;
  const margin = { top: 20, right: 20, bottom: 30, left: 40 };
  const graphWidth = width - margin.left - margin.right;
  const graphHeight = height - margin.top - margin.bottom;

  // Grid lines
  for (let pct = 0; pct <= 100; pct += 25) {
    const y = margin.top + graphHeight - (pct / 100.0) * graphHeight;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', margin.left);
    line.setAttribute('y1', y);
    line.setAttribute('x2', width - margin.right);
    line.setAttribute('y2', y);
    line.setAttribute('stroke', 'var(--border)');
    line.setAttribute('stroke-dasharray', '3,3');
    svg.appendChild(line);

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', margin.left - 8);
    label.setAttribute('y', y + 4);
    label.setAttribute('text-anchor', 'end');
    label.setAttribute('fill', 'var(--text-muted)');
    label.setAttribute('font-size', '9');
    label.textContent = `${pct}%`;
    svg.appendChild(label);
  }

  // Draw 5-Hour line path
  const points = records.map((r, idx) => {
    const x = margin.left + (idx / Math.max(records.length - 1, 1)) * graphWidth;
    const y = margin.top + graphHeight - (Math.min(r.five_hour, 100) / 100.0) * graphHeight;
    return { x, y, val: r.five_hour, time: r.timestamp };
  });

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', pathD);
  path.setAttribute('fill', 'none');
  path.setAttribute('stroke', 'var(--text-main)');
  path.setAttribute('stroke-width', '2');
  svg.appendChild(path);

  // Draw points
  points.forEach(p => {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', p.x);
    circle.setAttribute('cy', p.y);
    circle.setAttribute('r', '3');
    circle.setAttribute('fill', 'var(--bg-primary)');
    circle.setAttribute('stroke', 'var(--text-main)');
    circle.setAttribute('stroke-width', '1.5');
    svg.appendChild(circle);
  });
}
