/* Theme, text size, density and font preferences for RDSO pages. Stored locally; every access is guarded because storage can be
   unavailable (private windows, blocked site data). "system" follows the operating system's light/dark setting. */
(function (root) {
  'use strict';
  var KEY = 'rdso_ui_v1';
  var THEMES = [
    { id: 'system', name: 'Match my device', swatch: ['#f3f5f8', '#0d1117', '#0a5ec2'] },
    { id: 'light', name: 'Light', swatch: ['#ffffff', '#1b1f24', '#0a5ec2'] },
    { id: 'dark', name: 'Dark', swatch: ['#161b22', '#e6edf3', '#58a6ff'] },
    { id: 'solarized-light', name: 'Solarized light', swatch: ['#fdf6e3', '#3a4a50', '#1f64a8'] },
    { id: 'solarized-dark', name: 'Solarized dark', swatch: ['#002b36', '#d2dcdc', '#4fb0f0'] },
    { id: 'paper', name: 'Paper', swatch: ['#f9f3e4', '#2e2417', '#8a3b12'] },
    { id: 'nord', name: 'Nord', swatch: ['#3b4252', '#eceff4', '#88c0d0'] },
    { id: 'signal', name: 'Signal (night, amber)', swatch: ['#10222f', '#f1f5f8', '#ffb000'] },
    { id: 'contrast', name: 'High contrast', swatch: ['#000000', '#ffffff', '#ffe000'] }
  ];
  var DEFAULTS = { theme: 'system', size: 'm', density: 'comfortable', font: 'system' };

  function read() { try { return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { return Object.assign({}, DEFAULTS); } }
  function write(p) { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) { /* not persisted */ } }
  function resolve(theme) {
    if (theme !== 'system') return theme;
    return root.matchMedia && root.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function apply(p) {
    var el = root.document.documentElement;
    el.setAttribute('data-theme', resolve(p.theme));
    el.setAttribute('data-size', p.size); el.setAttribute('data-density', p.density); el.setAttribute('data-font', p.font);
    var meta = root.document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', getComputedStyle(el).getPropertyValue('--bg').trim() || '#ffffff');
  }
  function set(key, value) { var p = read(); p[key] = value; write(p); apply(p); return p; }
  var api = { THEMES: THEMES, DEFAULTS: DEFAULTS, read: read, set: set, apply: function () { apply(read()); }, reset: function () { write(DEFAULTS); apply(DEFAULTS); } };
  api.apply();
  if (root.matchMedia) {
    var mq = root.matchMedia('(prefers-color-scheme: dark)');
    var again = function () { if (read().theme === 'system') api.apply(); };
    if (mq.addEventListener) mq.addEventListener('change', again);
  }
  root.RDSOTheme = api;
})(window);
