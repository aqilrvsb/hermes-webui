// Ctrl+V paste an image into the Hermes chat — reuses the existing global addFiles().
// Injected into /apptoo/static/index.html by Dockerfile.railway. CSP-safe (served from 'self').
(function () {
  function onPaste(e) {
    try {
      var dt = e.clipboardData || window.clipboardData;
      if (!dt) return;
      var items = dt.items || [];
      var files = [];
      for (var i = 0; i < items.length; i++) {
        var it = items[i];
        if (it.kind === "file" && it.type && it.type.indexOf("image/") === 0) {
          var f = it.getAsFile();
          if (f) {
            var ext = (f.type.split("/")[1] || "png").replace("jpeg", "jpg");
            files.push(new File([f], "pasted-" + Date.now() + "." + ext, { type: f.type }));
          }
        }
      }
      if (files.length && typeof addFiles === "function") {
        addFiles(files);
        e.preventDefault();
      }
    } catch (_) {}
  }
  document.addEventListener("paste", onPaste, true);
})();
