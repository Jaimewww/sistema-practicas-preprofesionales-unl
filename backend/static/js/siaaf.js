// Progressive enhancement for the SIAAF shell. Pages work without it:
// the sidebar stays visible and the links are plain anchors.
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  // Set the first state before paint so desktop does not flash a closed sidebar.
  if (!window.matchMedia('(max-width: 62em)').matches) root.classList.add('sidebar-open');

  document.addEventListener('DOMContentLoaded', function () {
    var button = document.querySelector('[data-sidebar-toggle]');
    var sidebar = document.getElementById('sidebar');
    var closers = document.querySelectorAll('[data-sidebar-close]');
    var mobile = window.matchMedia('(max-width: 62em)');
    if (!button || !sidebar) return;

    function setOpen(open, returnFocus) {
      root.classList.toggle('sidebar-open', open);
      button.setAttribute('aria-expanded', String(open));
      if (!open && returnFocus) button.focus();
    }

    button.setAttribute('aria-expanded', String(root.classList.contains('sidebar-open')));
    mobile.addEventListener('change', function (event) {
      setOpen(!event.matches, false);
    });

    button.addEventListener('click', function () {
      var open = !root.classList.contains('sidebar-open');
      setOpen(open, false);
      // The sidebar comes first in the DOM, so hand focus to it on small screens.
      var close = sidebar.querySelector('button[data-sidebar-close]');
      if (open && mobile.matches && close) close.focus();
    });
    closers.forEach(function (el) {
      el.addEventListener('click', function () { setOpen(false, true); });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && mobile.matches && root.classList.contains('sidebar-open')) {
        setOpen(false, true);
      }
    });

    var fullscreen = document.querySelector('[data-fullscreen-toggle]');
    if (fullscreen && document.fullscreenEnabled) {
      fullscreen.addEventListener('click', function () {
        if (document.fullscreenElement) document.exitFullscreen();
        else root.requestFullscreen();
      });
    } else if (fullscreen) {
      fullscreen.hidden = true;
    }
  });
})();
