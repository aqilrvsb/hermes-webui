// AI Agents Floor: left sidebar (#panelFloor) = 4 platform filter buttons + the agent list.
// Click a platform (Facebook / Threads / TikTok / Instagram) -> shows only that platform's agents.
(function () {
  var PLATFORMS = [
    { id: 'facebook',  label: 'Facebook'  },
    { id: 'threads',   label: 'Threads'   },
    { id: 'tiktok',    label: 'TikTok'    },
    { id: 'instagram', label: 'Instagram' }
  ];
  var current = 'facebook';
  var agents = [];
  function esc(s){ return String(s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

  function agentRow(a){
    var times = (a.times || []).join(', ');
    return '<div class="floor-agent">' +
      '<img src="/static/office/ch/' + esc(a.icon || 'Claude-1') + '-front-left.png" alt="">' +
      '<div class="fa-meta"><div class="fa-name">' + esc(a.name) + '</div>' +
      '<div class="fa-sub">' + (times ? esc(times) : 'no schedule') +
        (a.model ? ' &middot; ' + esc(a.model) : '') + '</div></div>' +
    '</div>';
  }

  function paint(){
    var panel = document.getElementById('panelFloor');
    if (!panel) return;
    var tabs = PLATFORMS.map(function(p){
      var n = agents.filter(function(a){ return String(a.platform).toLowerCase() === p.id; }).length;
      return '<button class="floor-plat' + (p.id === current ? ' active' : '') + '" data-plat="' + p.id + '">' +
             esc(p.label) + (n ? ' <span class="fp-count">' + n + '</span>' : '') + '</button>';
    }).join('');
    var list = agents.filter(function(a){ return String(a.platform).toLowerCase() === current; });
    var rows = list.length ? list.map(agentRow).join('')
             : '<div class="floor-empty">No ' + current + ' agents yet.<br>Create one in the Agents tab.</div>';
    panel.innerHTML =
      '<div class="panel-head"><span>AI Agents Floor</span></div>' +
      '<div class="floor-plats">' + tabs + '</div>' +
      '<div class="floor-agents-list">' + rows + '</div>';
    panel.querySelectorAll('.floor-plat').forEach(function(b){
      b.onclick = function(){ current = b.getAttribute('data-plat'); paint(); };
    });
  }

  async function refresh(){
    try { var r = await fetch('/api/agents/list', { credentials: 'same-origin' }); var d = await r.json(); agents = d.agents || []; }
    catch (e) { agents = []; }
    paint();
  }

  var wasActive = false;
  setInterval(function () {
    var active = !!document.querySelector('main.main.showing-floor');
    if (active && !wasActive) refresh();
    wasActive = active;
  }, 800);
  if (document.readyState !== 'loading') { if (document.querySelector('main.main.showing-floor')) refresh(); }
  else document.addEventListener('DOMContentLoaded', function(){ if (document.querySelector('main.main.showing-floor')) refresh(); });
})();
