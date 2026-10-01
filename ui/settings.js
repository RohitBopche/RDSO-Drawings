/* Appearance button ("Aa") and panel for pages other than the chat: theme swatches, text size, spacing, reading font.
   RDSOSettings.mount(hostElement). Needs ui/themes.css and ui/theme.js. */
(function (root) {
  'use strict';
  var css = '.rs-pop{position:fixed;z-index:60;right:12px;top:52px;width:min(340px,94vw);background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 10px 34px rgba(0,0,0,.28);padding:14px}' +
    '.rs-pop[hidden]{display:none}.rs-pop h3{margin:0 0 8px;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}' +
    '.rs-sw{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}.rs-sw button{border:2px solid var(--line);border-radius:10px;padding:6px;cursor:pointer;background:var(--surface);color:var(--ink);text-align:center;font-size:.74rem}' +
    '.rs-sw i{display:block;height:20px;border-radius:5px;margin-bottom:4px;border:1px solid rgba(128,128,128,.4)}.rs-sw button[aria-pressed="true"]{border-color:var(--accent)}' +
    '.rs-seg{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}.rs-seg button{flex:1;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:8px;padding:5px 6px;cursor:pointer;min-width:60px}' +
    '.rs-seg button[aria-pressed="true"]{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}';
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function mount(host) {
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var btn = document.createElement('button'); btn.className = 'iconbtn'; btn.id = 'settingsBtn'; btn.textContent = 'Aa';
    btn.title = 'Appearance'; btn.setAttribute('aria-label', 'Appearance and reading settings'); btn.setAttribute('aria-expanded', 'false');
    var pop = document.createElement('div'); pop.className = 'rs-pop'; pop.id = 'settings'; pop.hidden = true; pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', 'Appearance');
    host.appendChild(btn); document.body.appendChild(pop);
    function seg(id, key, items) {
      return '<h3>' + key[1] + '</h3><div class="rs-seg" data-key="' + key[0] + '">' + items.map(function (i) { return '<button data-v="' + i[0] + '">' + i[1] + '</button>'; }).join('') + '</div>';
    }
    function draw() {
      var p = root.RDSOTheme.read();
      pop.innerHTML = '<h3>Theme</h3><div class="rs-sw">' + root.RDSOTheme.THEMES.map(function (t) {
        return '<button data-theme="' + t.id + '" aria-pressed="' + (p.theme === t.id) + '"><i style="background:linear-gradient(90deg,' + t.swatch[0] + ' 0 50%,' + t.swatch[2] + ' 50% 100%)"></i>' + esc(t.name) + '</button>'; }).join('') + '</div>' +
        seg('size', ['size', 'Text size'], [['s', 'Small'], ['m', 'Normal'], ['l', 'Large'], ['xl', 'Extra']]) +
        seg('density', ['density', 'Spacing'], [['comfortable', 'Comfortable'], ['compact', 'Compact']]) +
        seg('font', ['font', 'Reading font'], [['system', 'Standard'], ['readable', 'Easy to read'], ['serif', 'Serif'], ['mono', 'Mono']]) +
        '<button class="iconbtn" data-reset="1">Reset appearance</button>';
      pop.querySelectorAll('.rs-seg').forEach(function (g) { g.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(p[g.dataset.key] === b.dataset.v)); }); });
    }
    pop.addEventListener('click', function (e) {
      var t = e.target.closest('button'); if (!t) return;
      if (t.dataset.theme) root.RDSOTheme.set('theme', t.dataset.theme);
      else if (t.dataset.reset) root.RDSOTheme.reset();
      else if (t.dataset.v) root.RDSOTheme.set(t.parentNode.dataset.key, t.dataset.v);
      draw();
    });
    btn.addEventListener('click', function (e) { e.stopPropagation(); pop.hidden = !pop.hidden; btn.setAttribute('aria-expanded', String(!pop.hidden)); if (!pop.hidden) draw(); });
    document.addEventListener('click', function (e) { if (!pop.hidden && !pop.contains(e.target) && e.target !== btn) { pop.hidden = true; btn.setAttribute('aria-expanded', 'false'); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !pop.hidden) { pop.hidden = true; btn.setAttribute('aria-expanded', 'false'); } });
  }
  root.RDSOSettings = { mount: mount };
})(window);
