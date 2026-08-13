/**
 * Claude Usage Monitor — Landing Website Interactive Script
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Toggle
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeText = document.getElementById('theme-text');
  let currentTheme = 'dark';

  themeToggleBtn.addEventListener('click', () => {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    themeText.textContent = currentTheme === 'dark' ? 'LIGHT' : 'DARK';
  });

  // Interactive Mockup State Simulator
  const simBtns = document.querySelectorAll('.sim-btn');
  const demoDot = document.getElementById('demo-dot');
  const demoStatusText = document.getElementById('demo-status-text');

  const demoFhNum = document.getElementById('demo-fh-num');
  const demoFhFill = document.getElementById('demo-fh-fill');
  const demoFhReset = document.getElementById('demo-fh-reset');

  const demoSdNum = document.getElementById('demo-sd-num');
  const demoSdFill = document.getElementById('demo-sd-fill');
  const demoSdReset = document.getElementById('demo-sd-reset');

  simBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      simBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const state = btn.getAttribute('data-state');
      demoDot.className = 'demo-dot ' + state;

      if (state === 'safe') {
        demoStatusText.textContent = 'CONNECTED';
        demoFhNum.textContent = '42';
        demoFhFill.style.width = '42%';
        demoFhReset.textContent = 'Resets in 1h 32m';

        demoSdNum.textContent = '67';
        demoSdFill.style.width = '67%';
        demoSdReset.textContent = 'Resets in 3d 4h';
      } else if (state === 'warning') {
        demoStatusText.textContent = 'WARNING (82% REACHED)';
        demoFhNum.textContent = '82';
        demoFhFill.style.width = '82%';
        demoFhReset.textContent = 'Resets in 48m';

        demoSdNum.textContent = '74';
        demoSdFill.style.width = '74%';
        demoSdReset.textContent = 'Resets in 2d 18h';
      } else if (state === 'critical') {
        demoStatusText.textContent = 'CRITICAL (94% REACHED)';
        demoFhNum.textContent = '94';
        demoFhFill.style.width = '94%';
        demoFhReset.textContent = 'Resets in 14m';

        demoSdNum.textContent = '89';
        demoSdFill.style.width = '89%';
        demoSdReset.textContent = 'Resets in 1d 04h';
      } else if (state === 'offline') {
        demoStatusText.textContent = 'OFFLINE (NETWORK ISSUE)';
        demoFhNum.textContent = '--';
        demoFhFill.style.width = '0%';
        demoFhReset.textContent = 'Offline';

        demoSdNum.textContent = '--';
        demoSdFill.style.width = '0%';
        demoSdReset.textContent = 'Offline';
      }
    });
  });

  // Mockup Refresh Button
  const demoRefreshBtn = document.getElementById('demo-refresh-btn');
  demoRefreshBtn.addEventListener('click', () => {
    demoRefreshBtn.textContent = '↺ Syncing...';
    setTimeout(() => {
      demoRefreshBtn.textContent = '↺ Refresh';
      const now = new Date();
      document.getElementById('demo-time').textContent = `Updated ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    }, 400);
  });

  // Copy Code Button
  const copyCodeBtn = document.getElementById('copy-code-btn');
  copyCodeBtn.addEventListener('click', () => {
    const codeText = document.getElementById('code-content').textContent;
    navigator.clipboard.writeText(codeText).then(() => {
      copyCodeBtn.textContent = 'Copied!';
      setTimeout(() => { copyCodeBtn.textContent = 'Copy Commands'; }, 2000);
    });
  });
});
