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