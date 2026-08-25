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
   Shared motion helpers
   -------------------------------------------------------------------------- */
function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/* Flies a colour-matched stamp "ghost" from one element's screen position
   to another's, then hands off to the destination. This is the one
   authored transition in the site — the visual link between a stamp in
   the grid and its case file, and back again. Both endpoints must exist
   and have real geometry; anything else quietly no-ops so the underlying
   state change (already applied via CSS classes) still reads correctly. */
function flightGhost(fromRect, toEl, colorEl, opts) {
  if (prefersReducedMotion() || !toEl || !colorEl || !fromRect || !fromRect.width) return;
  if (!toEl.getBoundingClientRect || !document.createElement('div').animate) return;

  var toRect = toEl.getBoundingClientRect();
  if (!toRect.width) return;

  opts = opts || {};
  var colorMatch = colorEl.className && colorEl.className.match(/c-[\w-]+/);
  var ghost = document.createElement('div');
  ghost.className = 'stamp-flight stamp-shape' + (colorMatch ? ' ' + colorMatch[0] : '');
  ghost.style.width = fromRect.width + 'px';
  ghost.style.height = fromRect.height + 'px';
  document.body.appendChild(ghost);

  var dx = toRect.left - fromRect.left;
  var dy = toRect.top - fromRect.top;
  var sx = toRect.width / fromRect.width;
  var sy = toRect.height / fromRect.height;
  var startXf = 'translate(' + fromRect.left + 'px,' + fromRect.top + 'px)';
  var endXf = 'translate(' + (fromRect.left + dx) + 'px,' + (fromRect.top + dy) + 'px) scale(' + sx + ',' + sy + ')';

  if (opts.hideTarget) toEl.style.opacity = '0';

  var anim = ghost.animate([
    { transform: startXf + ' scale(1,1)', opacity: 1 },
    { transform: endXf, opacity: 1, offset: 0.88 },
    { transform: endXf, opacity: 0 }
  ], { duration: opts.duration || 460, easing: 'cubic-bezier(0.16,1,0.3,1)', fill: 'forwards' });

  anim.onfinish = function () {
    ghost.remove();
    if (opts.hideTarget) toEl.style.opacity = '';
    if (opts.onDone) opts.onDone();
  };
}

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

  // Below this width the rail is an off-canvas drawer, not a static sidebar —
  // its links must not be keyboard/AT-reachable while visually off-screen.
  var railMedia = window.matchMedia('(max-width: 880px)');

  function syncRailA11y() {
    var shouldHide = railMedia.matches && !rail.classList.contains('open');
    if (shouldHide) {
      rail.setAttribute('inert', '');
      rail.setAttribute('aria-hidden', 'true');
    } else {
      rail.removeAttribute('inert');
      rail.removeAttribute('aria-hidden');
    }
  }

  function closeDrawer(opts) {
    var wasOpen = rail.classList.contains('open');
    rail.classList.remove('open');
    scrim.classList.remove('visible');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.textContent = '☰';
    syncRailA11y();
    if (wasOpen && !(opts && opts.skipFocusReturn)) toggle.focus();
  }

  function openDrawer() {
    rail.classList.add('open');
    scrim.classList.add('visible');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.textContent = '✕';
    syncRailA11y();
    var firstLink = rail.querySelector('a');
    if (firstLink) firstLink.focus();
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

  if (railMedia.addEventListener) {
    railMedia.addEventListener('change', syncRailA11y);
  } else if (railMedia.addListener) {
    railMedia.addListener(syncRailA11y); // Safari <14 fallback
  }

  syncRailA11y();
}

/* --------------------------------------------------------------------------
   Custom magnifying-glass cursor (desktop / fine-pointer only)
   -------------------------------------------------------------------------- */
function initCursor() {
  var canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (!canHover || prefersReducedMotion()) return;

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

  grid.innerHTML = items.map(function (p, i) {
    var tilt = (Math.random() * 5.5 - 2.75).toFixed(2) + 'deg';
    var enterDelay = Math.min(i * 55, 300) + 'ms';
    return '' +
      '<button type="button" class="stamp-card stamp-shape c-' + p.color + '" data-id="' + p.id + '" style="--tilt:' + tilt + '; --enter-delay:' + enterDelay + ';">' +
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
  var stampEl = overlay.querySelector('.overlay-stamp');
  var contentEls = [
    overlay.querySelector('.overlay-head'),
    overlay.querySelector('.overlay-denom'),
    overlay.querySelector('.overlay-outcome'),
    body
  ];
  var currentIndex = 0;
  var openedIndex = -1;
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

  function fillContent(p) {
    stampEl.className = 'overlay-stamp stamp-shape c-' + p.color;
    overlay.querySelector('.overlay-tag').textContent = p.tag;
    overlay.querySelector('.overlay-title').textContent = p.title;
    overlay.querySelector('.overlay-denom').textContent = p.denom + ' — ' + p.date;
    overlay.querySelector('.overlay-outcome').textContent = p.outcome;
    body.querySelector('.o-problem').textContent = p.problem;
    body.querySelector('.o-approach').innerHTML = p.approach.map(function (a) { return '<li>' + a + '</li>'; }).join('');
    body.querySelector('.o-result').textContent = p.result;
  }

  /* direction: 'next' | 'prev' | undefined. Undefined means "just opened" —
     no content transition, since the flight ghost already carries the
     arrival. next/prev get a quick directional swap so paging through
     case files reads as movement, not a jump cut. */
  function render(index, direction) {
    var p = items[index];
    if (!p) return;
    currentIndex = index;

    if (!direction || prefersReducedMotion() || !sheet.animate) {
      fillContent(p);
      return;
    }

    var dx = direction === 'next' ? -14 : 14;
    var outAnims = contentEls.map(function (el) {
      if (!el) return null;
      return el.animate(
        [{ opacity: 1, transform: 'translateX(0)' }, { opacity: 0, transform: 'translateX(' + dx + 'px)' }],
        { duration: 90, easing: 'ease-in', fill: 'forwards' }
      );
    });

    Promise.all(outAnims.map(function (a) { return a ? a.finished : Promise.resolve(); })).then(function () {
      fillContent(p);
      contentEls.forEach(function (el) {
        if (!el) return;
        el.animate(
          [{ opacity: 0, transform: 'translateX(' + (dx * -1) + 'px)' }, { opacity: 1, transform: 'translateX(0)' }],
          { duration: 200, easing: 'cubic-bezier(0.16,1,0.3,1)' }
        );
      });
    }).catch(function () { fillContent(p); });
  }

  function open(index, trigger) {
    triggerEl = trigger || document.activeElement;
    openedIndex = index;
    var originRect = triggerEl && triggerEl.getBoundingClientRect ? triggerEl.getBoundingClientRect() : null;
    var willFly = !!(originRect && originRect.width && !prefersReducedMotion());

    // The sheet normally eases in on its own; when the stamp is about to
    // fly, let the sheet appear at rest instead so its final position is
    // stable the moment we measure it, and so the two motions don't compete.
    if (willFly) sheet.classList.add('no-entrance-motion');

    render(index);
    overlay.classList.add('open');
    document.body.classList.add('no-scroll');
    document.addEventListener('keydown', trapTab);
    closeBtn.focus();

    if (willFly) {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          sheet.classList.remove('no-entrance-motion');
          flightGhost(originRect, stampEl, triggerEl, {
            duration: 460,
            hideTarget: true,
            onDone: function () {
              stampEl.classList.add('stamped-in');
              setTimeout(function () { stampEl.classList.remove('stamped-in'); }, 380);
            }
          });
        });
      });
    }
  }

  function close() {
    var returnRect = stampEl.getBoundingClientRect();
    var landingCard = triggerEl;

    overlay.classList.remove('open');
    document.body.classList.remove('no-scroll');
    document.removeEventListener('keydown', trapTab);

    if (landingCard && document.body.contains(landingCard) && currentIndex === openedIndex) {
      flightGhost(returnRect, landingCard, stampEl, { duration: 300 });
    }

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
  prevBtn.addEventListener('click', function () { render((currentIndex - 1 + items.length) % items.length, 'prev'); });
  nextBtn.addEventListener('click', function () { render((currentIndex + 1) % items.length, 'next'); });

  document.addEventListener('keydown', function (e) {
    if (!overlay.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') render((currentIndex + 1) % items.length, 'next');
    if (e.key === 'ArrowLeft') render((currentIndex - 1 + items.length) % items.length, 'prev');
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
    var enterDelay = Math.min(i * 55, 300) + 'ms';
    return '' +
      '<a class="postcard" href="' + post.url + '" target="_blank" rel="noopener noreferrer" style="--tilt:' + tilt + '; --enter-delay:' + enterDelay + ';">' +
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
