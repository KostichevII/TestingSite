//   # --- Тема применяется до отрисовки, чтобы не было мигания --- #\
(function setTheme () {
      const saved = localStorage.getItem('theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.dataset.theme = saved || (prefersDark ? 'dark' : 'light');
    })();


(function changeTheme () {
      const btn = document.getElementById('theme-toggle');
      if (!btn) return;
      btn.addEventListener('click', () => {
        const root = document.documentElement;
        const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
        root.dataset.theme = next;
        localStorage.setItem('theme', next);
      });
})();