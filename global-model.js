// Internal tool tweak: picking a model in the chat dropdown ALSO sets it as the GLOBAL default,
// so every agent/cron (which inherits the profile default model) switches to it too — one knob.
// The built-in onchange keeps its session-local behaviour; this runs in addition (addEventListener,
// so it does not override the existing handler). New agent runs pick up the new default; already-running
// sessions keep their current model.
(function () {
  function persistGlobal(model) {
    if (!model) return;
    try {
      fetch('/api/default-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: model }),
      }).catch(function () {});
    } catch (e) {}
  }
  function hook() {
    var sel = document.getElementById('modelSelect');
    if (!sel || sel._globalModelHooked) return;
    sel._globalModelHooked = true;
    sel.addEventListener('change', function () { persistGlobal(sel.value); });
  }
  if (document.readyState !== 'loading') hook();
  else document.addEventListener('DOMContentLoaded', hook);
  // Re-hook in case the dropdown is re-rendered after navigation.
  setInterval(hook, 2000);
})();
