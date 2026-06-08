// Open the custom rail tabs (Model Routing / Instruction Claude / Agent Reports / Creatives / AI Floor)
// INSIDE the Hermes page as a themed iframe overlay — instead of a new browser tab.
// The overlay + the dashboard pages follow Hermes's current theme (Hermes sets class="dark" on <html>).
(function(){
  var CUSTOM=/\/static\/(model-config|instruction|reports|creatives|pixel|whatsnew)\.html/;
  function isDark(){try{return document.documentElement.classList.contains('dark');}catch(e){return true;}}
  function paint(o){
    var d=isDark();
    o.style.background=d?'#0a0e18':'#f6f7fb';
    var bar=o.querySelector('#customPanelBar');
    if(bar){bar.style.background=d?'#0e1322':'#ffffff';bar.style.borderBottom='1px solid '+(d?'#20283f':'#e4e7f0');bar.style.color=d?'#dfe9ff':'#1a2138';}
    var btn=o.querySelector('#customPanelClose');
    if(btn){btn.style.background=d?'#13203a':'#eef0f6';btn.style.color=d?'#cfe0ff':'#1a2138';btn.style.border='1px solid '+(d?'#2a3350':'#d7dbe8');}
    var fr=o.querySelector('#customPanelFrame'); if(fr)fr.style.background=d?'#0a0e18':'#f6f7fb';
  }
  function ensureOverlay(){
    var o=document.getElementById('customPanelOverlay');
    if(o)return o;
    o=document.createElement('div'); o.id='customPanelOverlay';
    o.style.cssText='position:fixed;inset:0;z-index:99998;display:none;flex-direction:column';
    var bar=document.createElement('div'); bar.id='customPanelBar';
    bar.style.cssText='display:flex;align-items:center;gap:10px;padding:9px 14px;font-family:-apple-system,Segoe UI,Roboto,sans-serif;flex:none';
    bar.innerHTML='<span id="customPanelTitle" style="font-weight:700;font-size:14px"></span>'
      +'<button id="customPanelClose" title="Close (Esc)" style="margin-left:auto;border-radius:8px;padding:6px 15px;font-weight:700;font-size:13px;cursor:pointer">✕ Close</button>';
    var fr=document.createElement('iframe'); fr.id='customPanelFrame'; fr.style.cssText='flex:1;width:100%;border:0';
    o.appendChild(bar); o.appendChild(fr); document.body.appendChild(o);
    bar.querySelector('#customPanelClose').addEventListener('click',window.closeCustomPanel);
    return o;
  }
  window.openCustomPanel=function(url,title){
    var o=ensureOverlay(); paint(o);
    o.querySelector('#customPanelTitle').textContent=title||'';
    var sep=url.indexOf('?')<0?'?':'&';
    o.querySelector('#customPanelFrame').src=url+sep+'ht='+(isDark()?'dark':'light');   // tell the page which theme to use
    o.style.display='flex';
  };
  window.closeCustomPanel=function(){
    var o=document.getElementById('customPanelOverlay');
    if(o){o.style.display='none';o.querySelector('#customPanelFrame').src='about:blank';}
  };
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
