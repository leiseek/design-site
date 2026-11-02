// design-site i18n: language from localStorage ('dp-lang') or browser
// language (navigator.language; zh* -> zh, everything else -> en),
// set before first paint by the inline <head> script. This module keeps
// the manual 中文/EN toggle, <title>, meta description and search
// placeholders in sync. No framework; safe if localStorage is blocked.
(function () {
  var PH = { zh: '搜标题、作者、点评…', en: 'Search titles, authors, notes…' };
  function cur() { return document.documentElement.lang === 'en' ? 'en' : 'zh'; }
  function meta(name) {
    var m = document.querySelector('meta[name="' + name + '"]');
    return m ? m.getAttribute('content') : '';
  }
  function apply(l) {
    document.documentElement.lang = (l === 'en') ? 'en' : 'zh-CN';
    try { localStorage.setItem('dp-lang', l); } catch (e) {}
    var t = meta('dp-title-' + l), d = meta('dp-desc-' + l);
    if (t) document.title = t;
    if (d) {
      var md = document.querySelector('meta[name="description"]');
      if (md) md.setAttribute('content', d);
    }
    document.querySelectorAll('[data-ph]').forEach(function (el) {
      el.setAttribute('placeholder', PH[l] || PH.zh);
    });
    document.querySelectorAll('.langsw button').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-lang') === l);
    });
    if (window.__dpRefresh) window.__dpRefresh();
  }
  // locale-aware "N works" counter used by app.js
  window.dpFmtCount = function (n) {
    return cur() === 'en' ? (n + ' works') : ('共 ' + n + ' 个作品');
  };
  document.querySelectorAll('.langsw button').forEach(function (b) {
    b.addEventListener('click', function () { apply(b.getAttribute('data-lang')); });
  });
  apply(cur());
})();
