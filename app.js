/* ==========================================================================
   THE COLLECTION — app behavior
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  initRailToggle();
  initCursor();
  initProjectGrid();
  initPostcards();
});

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
  var cx = x, cy = y;

  window.addEventListener('mousemove', function (e) {
    x = e.clientX;
    y = e.clientY;
    loupe.style.opacity = '1';
  });

  document.addEventListener('mouseleave', function () { loupe.style.opacity = '0'; });

  var interactive = 'a, button, summary, .stamp-card, [role="button"]';
  document.addEventListener('mouseover', function (e) {
    if (e.target.closest && e.target.closest(interactive)) {
      loupe.classList.add('is-active');
    }
  });
  document.addEventListener('mouseout', function (e) {
    if (e.target.closest && e.target.closest(interactive)) {
      loupe.classList.remove('is-active');
    }
  });

  function tick() {
    cx += (x - cx) * 0.18;
    cy += (y - cy) * 0.18;
    loupe.style.transform = 'translate(' + cx + 'px,' + cy + 'px)';
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* --------------------------------------------------------------------------
   Case-file overlay markup — injected once, only on pages that render a
   stamp grid. Was previously duplicated by hand in index.html and
   projects.html; now it exists in exactly one place.
   -------------------------------------------------------------------------- */
var OVERLAY_HTML =
  '<div class="overlay" id="case-overlay">' +
    '<div class="overlay-sheet" role="dialog" aria-modal="true" aria-label="Case file">' +
      '<button class="overlay-close" aria-label="Close">✕</button>' +
      '<div class="overlay-head">' +
        '<div class="overlay-stamp stamp-shape"></div>' +
        '<div><span class="overlay-tag"></span><h3 class="overlay-title"></h3></div>' +
      '</div>' +
      '<span class="overlay-denom"></span>' +
      '<p class="overlay-outcome"></p>' +
      '<div class="overlay-body">' +
        '<div><h4>The problem</h4><p class="o-problem"></p></div>' +
        '<div><h4>What I did</h4><ul class="o-approach"></ul></div>' +
        '<div><h4>The outcome</h4><p class="o-result"></p></div>' +
      '</div>' +
      '<div class="overlay-nav">' +
        '<button class="overlay-prev">← Previous</button>' +
        '<button class="overlay-next">Next →</button>' +
      '</div>' +
    '</div>' +
  '</div>';

/* --------------------------------------------------------------------------
   Render the stamp grid (project cards) and wire up its overlay from one
   shared `items` list, computed once.
   Looks for a container: <div id="stamp-grid" data-filter="featured|all">
   -------------------------------------------------------------------------- */
function initProjectGrid() {
  var grid = document.getElementById('stamp-grid');
  if (!grid || typeof PROJECTS === 'undefined') return;

  var filter = grid.getAttribute('data-filter') || 'all';
  var items = filter === 'featured' ? PROJECTS.filter(function (p) { return p.featured; }) : PROJECTS;

  grid.innerHTML = items.map(function (p) {
    var tilt = (Math.random() * 5.5 - 2.75).toFixed(2) + 'deg';
    return '' +
      '<button type="button" class="stamp-card stamp-shape" data-id="' + p.id + '" style="--tilt:' + tilt + ';--accent:var(--' + p.color + ');">' +
        '<span class="stamp-inner">' +
          '<span class="stamp-tag">' + p.tag + '</span>' +
          '<span class="stamp-title">' + p.title + '</span>' +
          '<span class="stamp-denom-badge"><span class="stamp-denom-num">' + p.num + '</span></span>' +
        '</span>' +
        '<span class="postmark">Completed<br>' + p.date + '</span>' +
      '</button>';
  }).join('');

  grid.dataset.rendered = 'true';
  initOverlay(items);
}

/* --------------------------------------------------------------------------
   Case-file overlay — opens when a stamp card is clicked. Takes the same
   `items` list the grid already computed, instead of recomputing it.
   -------------------------------------------------------------------------- */
function initOverlay(items) {
  document.body.insertAdjacentHTML('beforeend', OVERLAY_HTML);
  var overlay = document.getElementById('case-overlay');

  var closeBtn = overlay.querySelector('.overlay-close');
  var prevBtn = overlay.querySelector('.overlay-prev');
  var nextBtn = overlay.querySelector('.overlay-next');
  var body = overlay.querySelector('.overlay-body');
  var currentIndex = 0;

  function render(index) {
    var p = items[index];
    if (!p) return;
    currentIndex = index;
    overlay.querySelector('.overlay-tag').textContent = p.tag;
    overlay.querySelector('.overlay-title').textContent = p.title;
    overlay.querySelector('.overlay-denom').textContent = p.denom + ' — ' + p.date;
    overlay.querySelector('.overlay-outcome').textContent = p.outcome;
    body.querySelector('.o-problem').textContent = p.problem;
    body.querySelector('.o-approach').innerHTML = p.approach.map(function (a) { return '<li>' + a + '</li>'; }).join('');
    body.querySelector('.o-result').textContent = p.result;
  }

  function open(index) {
    render(index);
    overlay.classList.add('open');
    document.body.classList.add('no-scroll');
    closeBtn.focus();
  }

  function close() {
    overlay.classList.remove('open');
    document.body.classList.remove('no-scroll');
  }

  document.addEventListener('click', function (e) {
    var card = e.target.closest ? e.target.closest('.stamp-card') : null;
    if (!card) return;
    var id = card.getAttribute('data-id');
    var index = items.findIndex(function (p) { return p.id === id; });
    if (index > -1) {
      card.classList.add('lifting');
      setTimeout(function () { card.classList.remove('lifting'); }, 260);
      open(index);
    }
  });

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
  prevBtn.addEventListener('click', function () { render((currentIndex - 1 + items.length) % items.length); });
  nextBtn.addEventListener('click', function () { render((currentIndex + 1) % items.length); });

  document.addEventListener('keydown', function (e) {
    if (!overlay.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') render((currentIndex + 1) % items.length);
    if (e.key === 'ArrowLeft') render((currentIndex - 1 + items.length) % items.length);
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
