// 设计拾集筛选：分类 pill + 关键词搜索，无框架，JS 失效时全部作品照常显示。
(function () {
  var pills = document.querySelectorAll('[data-filter]');
  var input = document.getElementById('q');
  var countEl = document.getElementById('result-count');
  var sections = document.querySelectorAll('[data-edition]');
  var current = '全部';
  function apply() {
    var q = (input ? input.value.trim().toLowerCase() : '');
    var shown = 0;
    document.querySelectorAll('.work').forEach(function (w) {
      var cats = (w.getAttribute('data-cats') || '').split(' ');
      var text = (w.textContent || '').toLowerCase();
      var okCat = current === '全部' || cats.indexOf(current) !== -1;
      var okQ = !q || text.indexOf(q) !== -1;
      var show = okCat && okQ;
      w.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    sections.forEach(function (s) {
      var any = false;
      s.querySelectorAll('.work').forEach(function (w) { if (w.style.display !== 'none') any = true; });
      s.style.display = any ? '' : 'none';
    });
    if (countEl) countEl.textContent = '共 ' + shown + ' 个作品';
    var empty = document.getElementById('empty');
    if (empty) empty.style.display = shown === 0 ? 'block' : 'none';
  }
  pills.forEach(function (p) {
    p.addEventListener('click', function () {
      pills.forEach(function (x) { x.classList.remove('active'); });
      p.classList.add('active');
      current = p.getAttribute('data-filter');
      apply();
    });
  });
  if (input) input.addEventListener('input', apply);
})();
