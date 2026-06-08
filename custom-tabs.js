// Open the custom rail tabs (Model Routing / Instruction Claude / Agent Reports / Creatives / AI Floor)
// INSIDE the Hermes page as a themed iframe overlay — instead of a new browser tab.
(function(){
  var CUSTOM=/\/static\/(model-config|instruction|reports|creatives|pixel)\.html/;
  function ensureOverlay(){
    var o=document.getElementById('customPanelOverlay');
    if(o)return o;
    o=document.createElement('div'); o.id='customPanelOverlay';
    o.style.cssText='position:fixed;inset:0;z-index:99998;background:#0a0e18;display:none;flex-direction:column';
    var bar=document.createElement('div');
    bar.style.cssText='display:flex;align-items:center;gap:10px;padding:9px 14px;background:#0e1322;border-bottom:1px solid #20283f;font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#dfe9ff;flex:none';
    bar.innerHTML='<span id="customPanelTitle" style="font-weight:700;font-size:14px;letter-spacing:.01em"></span>'
      +'<button id="customPanelClose" title="Close (Esc)" style="margin-left:auto;background:#13203a;color:#cfe0ff;border:1px solid #2a3350;border-radius:8px;padding:6px 15px;font-weight:700;font-size:13px;cursor:pointer">✕ Close</button>';
    var fr=document.createElement('iframe'); fr.id='customPanelFrame';
    fr.style.cssText='flex:1;width:100%;border:0;background:#0a0e18';
    o.appendChild(bar); o.appendChild(fr); document.body.appendChild(o);
    bar.querySelector('#customPanelClose').addEventListener('click',window.closeCustomPanel);
    return o;
  }
  window.openCustomPanel=function(url,title){
    var o=ensureOverlay();
    o.querySelector('#customPanelTitle').textContent=title||'';
    o.querySelector('#customPanelFrame').src=url;
    o.style.display='flex';
  };
  window.closeCustomPanel=function(){
    var o=document.getElementById('customPanelOverlay');
    if(o){o.style.display='none';o.querySelector('#customPanelFrame').src='about:blank';}
  };
  // Intercept clicks on the custom rail links (capture phase, before Hermes + browser default).
  document.addEventListener('click',function(e){
    var a=e.target&&e.target.closest?e.target.closest('a[href]'):null;
    if(!a)return;
    var href=a.getAttribute('href')||'';
    if(CUSTOM.test(href)){
      e.preventDefault(); e.stopPropagation();
      window.openCustomPanel(href, a.getAttribute('data-tooltip')||a.getAttribute('aria-label')||'');
    }
  },true);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')window.closeCustomPanel();});
})();
