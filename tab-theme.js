// Make a custom dashboard page follow Hermes's theme. Hermes uses class="dark" on <html>.
// The page is opened in an iframe with ?ht=dark|light (set by custom-tabs.js); fall back to
// reading the parent's .dark class (same origin), else default dark. Runs early to avoid a flash.
(function(){
  try{
    var p=new URLSearchParams(location.search).get('ht');
    var dark = p ? (p!=='light') : true;
    if(!p){ try{ if(window.parent && window.parent!==window) dark=window.parent.document.documentElement.classList.contains('dark'); }catch(e){} }
    document.documentElement.classList.toggle('dark', dark);
  }catch(e){ try{document.documentElement.classList.add('dark');}catch(_){} }
})();
