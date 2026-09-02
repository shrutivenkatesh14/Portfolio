/* ==========================================================================
   THE COLLECTION — app behavior
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  initTheme();
  initRailToggle();
  initCursor();
  initStampGrid();
  initOverlay();
  initPostcards();
});

/* --------------------------------------------------------------------------
   Dark mode — same album, night, brass desk lamp.
   Preference is read before paint (see the inline snippet in <head>) so
   there is no flash; this wires up the switch and keeps it in sync.
   -------------------------------------------------------------------------- */
function initTheme() {
  var toggle = document.querySelector('.lamp-toggle');
  if (!toggle) return;

  var root = document.documentElement;

  function isDark() { return root.getAttribute('data-theme') === 'dark'; }

  function reflect() {
    var dark = isDark();
    toggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
    toggle.setAttribute('aria-label', dark ? 'Turn off the lamp (light mode)' : 'Turn on the lamp (dark mode)');
  }

  reflect();

  toggle.addEventListener('click', function () {
    var next = isDark() ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) { /* private mode etc. */ }
    reflect();
  });
}

/* --------------------------------------------------------------------------
   Mobile rail drawer
   -------------------------------------------------------------------------- */
function initRailToggle() {
  var toggle = document.querySelector('.rail-toggle');
  var rail = document.querySelector('.rail');
  if (!toggle || !rail) return;

  toggle.addEventListener('click', function () {
    var isOpen = rail.classList.toggle('open');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    toggle.textContent = isOpen ? '✕' : '☰';
  });

  rail.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      rail.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = '☰';
    });
  });
}

/* --------------------------------------------------------------------------
   Custom magnifying-glass cursor (desktop / fine-pointer only)
   -------------------------------------------------------------------------- */
function initCursor() {
  var canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!canHover || reduced) return;

  var loupe = document.createElement('div');
  loupe.className = 'loupe-cursor';
  loupe.innerHTML = '<span class="loupe-glass"></span><span class="loupe-handle"></span>';
  document.body.appendChild(loupe);
  document.body.classList.add('has-loupe-cursor');

  var x = window.innerWidth / 2, y = window.innerHeight / 2;
  var raf = null;

  function writePosition() {
    loupe.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    raf = null;
  }

  window.addEventListener('mousemove', function (e) {
    x = e.clientX;
    y = e.clientY;
    loupe.style.opacity = '1';
    if (raf === null) raf = requestAnimationFrame(writePosition);
  }, { passive: true });

  document.addEventListener('mouseleave', function () { loupe.style.opacity = '0'; });

  var interactive = 'a, button, summary, .stamp-card, [role="button"]';
  document.addEventListener('mouseover', function (e) {
    if (e.target.closest && e.target.closest(interactive)) {
      loupe.classList.add('is-active');
    }
  }, { passive: true });
  document.addEventListener('mouseout', function (e) {
    if (e.target.closest && e.target.closest(interactive)) {
      loupe.classList.remove('is-active');
    }
  }, { passive: true });
}

/* --------------------------------------------------------------------------
   Render the stamp grid (project cards) from PROJECTS data
   Looks for a container: <div id="stamp-grid" data-filter="featured|all">
   -------------------------------------------------------------------------- */
/* --------------------------------------------------------------------------
   Stamp category icons — one small monoline glyph per project tag, so each
   stamp reads at a glance instead of relying on color + text alone.
   -------------------------------------------------------------------------- */
var STAMP_ICONS = {
  "Data Analysis": '<path d="M4 16V10M10 16V4M16 16V12"/>',
  "Process Improvement": '<circle cx="10" cy="10" r="3.4"/><path d="M10 2.5v2.4M10 15.1v2.4M17.5 10h-2.4M4.9 10H2.5M15.6 4.4l-1.7 1.7M6.1 13.9l-1.7 1.7M15.6 15.6l-1.7-1.7M6.1 6.1L4.4 4.4"/>',
  "Strategy": '<circle cx="10" cy="10" r="7.2"/><path d="M10 5.2l1.5 3.3 3.3 1.5-3.3 1.5-1.5 3.3-1.5-3.3-3.3-1.5 3.3-1.5z"/>',
  "Financial Modelling": '<rect x="3.5" y="2.5" width="13" height="15" rx="1"/><path d="M6 6.5h8M6 10h2.7M11.3 10h2.7M6 13.5h2.7M11.3 13.5h2.7"/>',
  "Data Visualisation": '<circle cx="10" cy="10" r="7.2"/><path d="M10 2.8V10h7.2"/>',
  "Case Competition": '<path d="M6 3h8v3.6a4 4 0 0 1-8 0V3z"/><path d="M6 4H3.2v1.8A2.8 2.8 0 0 0 6 8.6M14 4h2.8v1.8A2.8 2.8 0 0 1 14 8.6M8 12.6v2.9h4v-2.9M7 17h6"/>'
};
var STAMP_ICON_FALLBACK = '<path d="M10 2.2l1.9 4.7 5.1.4-3.9 3.3 1.2 5-4.3-2.8-4.3 2.8 1.2-5-3.9-3.3 5.1-.4z"/>';

function stampIconSvg(tag) {
  var inner = STAMP_ICONS[tag] || STAMP_ICON_FALLBACK;
  return '<svg class="stamp-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + '</svg>';
}

function initStampGrid() {
  var grid = document.getElementById('stamp-grid');
  if (!grid || typeof PROJECTS === 'undefined') return;

  var filter = grid.getAttribute('data-filter') || 'all';
  var items = filter === 'featured' ? PROJECTS.filter(function (p) { return p.featured; }) : PROJECTS;

  grid.innerHTML = items.map(function (p) {
    var tilt = (Math.random() * 5.5 - 2.75).toFixed(2) + 'deg';
    return '' +
      '<button type="button" class="stamp-card stamp-shape c-' + p.color + '" data-id="' + p.id + '" style="--tilt:' + tilt + ';">' +
        '<span class="stamp-inner">' +
          '<span class="stamp-tag-row">' + stampIconSvg(p.tag) + '<span class="stamp-tag">' + p.tag + '</span></span>' +
          '<span class="stamp-title">' + p.title + '</span>' +
          '<span class="stamp-denom-badge"><span class="stamp-denom-num">' + (p.denom || '').replace(/[^0-9]/g,'') + '</span></span>' +
        '</span>' +
        '<span class="postmark">Completed<br>' + p.date + '</span>' +
      '</button>';
  }).join('');

  grid.dataset.rendered = 'true';
}

/* --------------------------------------------------------------------------
   Case-file overlay — opens when a stamp card is clicked
   -------------------------------------------------------------------------- */
function initOverlay() {
  var overlay = document.getElementById('case-overlay');
  if (!overlay || typeof PROJECTS === 'undefined') return;

  var grid = document.getElementById('stamp-grid');
  var filter = grid ? (grid.getAttribute('data-filter') || 'all') : 'all';
  var items = filter === 'featured' ? PROJECTS.filter(function (p) { return p.featured; }) : PROJECTS;

  var closeBtn = overlay.querySelector('.overlay-close');
  var prevBtn = overlay.querySelector('.overlay-prev');
  var nextBtn = overlay.querySelector('.overlay-next');
  var content = overlay.querySelector('.overlay-content');
  var body = overlay.querySelector('.overlay-body');
  var currentIndex = 0;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function render(index) {
    var p = items[index];
    if (!p) return;
    currentIndex = index;
    overlay.querySelector('.overlay-stamp').className = 'overlay-stamp stamp-shape c-' + p.color;
    overlay.querySelector('.overlay-tag').textContent = p.tag;
    overlay.querySelector('.overlay-title').textContent = p.title;
    overlay.querySelector('.overlay-denom').textContent = p.denom + ' — ' + p.date;
    overlay.querySelector('.overlay-outcome').textContent = p.outcome;
    body.querySelector('.o-problem').textContent = p.problem;
    body.querySelector('.o-approach').innerHTML = p.approach.map(function (a) { return '<li>' + a + '</li>'; }).join('');
    body.querySelector('.o-result').textContent = p.result;
  }

  function goTo(index) {
    if (reduced) { render(index); return; }
    content.classList.add('is-switching');
    setTimeout(function () {
      render(index);
      content.classList.remove('is-switching');
    }, 150);
  }

  var lastTrigger = null;

  function open(index, trigger) {
    render(index);
    overlay.classList.add('open');
    overlay.setAttribute('aria-hidden', 'false');
    overlay.inert = false;
    document.body.classList.add('no-scroll');
    lastTrigger = trigger || null;
    closeBtn.focus();
  }

  function close() {
    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    overlay.inert = true;
    document.body.classList.remove('no-scroll');
    if (lastTrigger && typeof lastTrigger.focus === 'function') {
      lastTrigger.focus();
    }
    lastTrigger = null;
  }

  document.addEventListener('click', function (e) {
    var card = e.target.closest ? e.target.closest('.stamp-card') : null;
    if (!card) return;
    var id = card.getAttribute('data-id');
    var index = items.findIndex(function (p) { return p.id === id; });
    if (index > -1) {
      card.classList.add('lifting');
      setTimeout(function () { card.classList.remove('lifting'); }, 260);
      open(index, card);
    }
  });

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
  prevBtn.addEventListener('click', function () { goTo((currentIndex - 1 + items.length) % items.length); });
  nextBtn.addEventListener('click', function () { goTo((currentIndex + 1) % items.length); });

  document.addEventListener('keydown', function (e) {
    if (!overlay.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') goTo((currentIndex + 1) % items.length);
    if (e.key === 'ArrowLeft') goTo((currentIndex - 1 + items.length) % items.length);
  });
}

/* --------------------------------------------------------------------------
   Render postcards (writing page) from POSTS data
   Each postcard is "taped" into the album — a small washi-tape strip
   across the top edge, varied in colour, position, and tilt so the rack
   doesn't look mechanically repeated. Never a pin; never on a stamp.
   -------------------------------------------------------------------------- */
function initPostcards() {
  var rack = document.getElementById('postcard-rack');
  if (!rack || typeof POSTS === 'undefined') return;

  var tapeColors = ['washi-rose', 'washi-sage', 'washi-blue', 'washi-butter', 'washi-lavender'];

  rack.innerHTML = POSTS.map(function (post, i) {
    var tilt = (Math.random() * 2.4 - 1.2).toFixed(2) + 'deg';
    var tapeRotate = (Math.random() * 10 - 5).toFixed(2) + 'deg';
    var tapeLeft = (26 + Math.random() * 24).toFixed(1) + '%';
    var tapeColor = tapeColors[i % tapeColors.length];
    return '' +
      '<a class="postcard" href="' + post.url + '" target="_blank" rel="noopener noreferrer" style="--tilt:' + tilt + ';">' +
        '<span class="washi-tape ' + tapeColor + '" aria-hidden="true" style="left:' + tapeLeft + '; transform:translateX(-50%) rotate(' + tapeRotate + ');"></span>' +
        '<span class="postcard-frank">' + post.platform + '</span>' +
        '<span class="postcard-tag">' + post.tag + ' · ' + post.date + '</span>' +
        '<span class="postcard-title">' + post.title + '</span>' +
        '<span class="postcard-teaser">' + post.teaser + '</span>' +
        '<span class="postcard-cta">Read on ' + post.platform + ' ↗</span>' +
      '</a>';
  }).join('');
}
