/* Load synchronously before CSS. Only theme preference is stored, never account data. */
(function () {
  try {
    const theme = localStorage.getItem('m-theme');
    if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
  } catch (_) { /* System theme still works without storage. */ }
})();
