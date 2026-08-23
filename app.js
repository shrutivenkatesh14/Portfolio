/* ==========================================================================
   THE COLLECTION — app behavior
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  initRailToggle();
  initCursor();
  initStampGrid();
  initOverlay();
  initPostcards();
  initCopyButtons();
});

/* --------------------------------------------------------------------------
   Mobile rail drawer
   -------------------------------------------------------------------------- */
function initRailToggle() {
  var toggle = document.querySelector('.rail-toggle');
  var rail = document.querySelector('.rail');
  if (!toggle || !rail) return;

  var scrim = document.createElement('div');
  scrim.className = 'rail-scrim';
  document.body.appendChild(scrim);

  function closeDrawer() {
    rail.classList.remove('open');
    scrim.classList.remove('visible');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.textContent = '☰';
  }

  function openDrawer() {
    rail.classList.add('open');
    scrim.classList.add('visible');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.textContent = '✕';
  }

  toggle.addEventListener('click', function () {
    if (rail.classList.contains('open')) closeDrawer(); else openDrawer();
  });

  scrim.addEventListener('click', closeDrawer);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && rail.classList.contains('open')) closeDrawer();
  });

  rail.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', closeDrawer);
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
   Render the stamp grid (project cards) from PROJECTS data
   Looks for a container: <div id="stamp-grid" data-filter="featured|all">
   -------------------------------------------------------------------------- */
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
          '<span class="stamp-tag">' + p.tag + '</span>' +
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
  var body = overlay.querySelector('.overlay-body');
  var sheet = overlay.querySelector('.overlay-sheet');
  var currentIndex = 0;
  var triggerEl = null;

  function focusableIn(container) {
    return Array.prototype.slice.call(
      container.querySelectorAll('button, a[href], [tabindex]:not([tabindex="-1"])')
    ).filter(function (el) { return el.offsetParent !== null; });
  }

  function trapTab(e) {
    if (e.key !== 'Tab') return;
    var focusable = focusableIn(sheet);
    if (!focusable.length) return;
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

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

  function open(index, trigger) {
    triggerEl = trigger || document.activeElement;
    render(index);
    overlay.classList.add('open');
    document.body.classList.add('no-scroll');
    document.addEventListener('keydown', trapTab);
    closeBtn.focus();
  }

  function close() {
    overlay.classList.remove('open');
    document.body.classList.remove('no-scroll');
    document.removeEventListener('keydown', trapTab);
    if (triggerEl && typeof triggerEl.focus === 'function') triggerEl.focus();
    triggerEl = null;
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

/* --------------------------------------------------------------------------
   Copy-to-clipboard on contact details — a small "stamping" confirmation.
   Progressive enhancement: if the Clipboard API isn't available (older
   browser, non-secure context), the button quietly does nothing extra and
   the underlying mailto/link still works normally.
   -------------------------------------------------------------------------- */
function initCopyButtons() {
  var buttons = document.querySelectorAll('.copy-btn');
  if (!buttons.length || !navigator.clipboard) return;

  var announcer = document.getElementById('copy-announcer');

  buttons.forEach(function (btn) {
    var timer = null;
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy-text');
      var what = btn.getAttribute('data-copy-what') || 'Text';
      navigator.clipboard.writeText(text).then(function () {
        btn.classList.add('copied');
        if (announcer) announcer.textContent = what + ' copied to clipboard.';
        clearTimeout(timer);
        timer = setTimeout(function () {
          btn.classList.remove('copied');
        }, 1600);
      }).catch(function () {
        /* clipboard write failed silently — link beside it still works */
      });
    });
  });
}
