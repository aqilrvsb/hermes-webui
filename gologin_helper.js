#!/usr/bin/env node
/*
 * gologin_helper.js — the ONE GoLogin cloud-browser driver for all of Hermes.
 *
 * 100% GoLogin: 1 client = 1 GoLogin profile = 1 real logged-in Chrome in the cloud. This helper
 * connects to that profile's cloud session over CDP (documented connect URL) and does everything the
 * app needs — the SAME engine for chat (instant) and agents (scheduled) and floor (detect):
 *
 *   node gologin_helper.js login-status            -> which platforms are logged in {facebook:bool,...}
 *   node gologin_helper.js scrape <url> [selector] -> innerText of the page / a selector (logged-in view)
 *   node gologin_helper.js screenshot <url> <out>  -> PNG of a page
 *   node gologin_helper.js post <platform> <captionFile> [mediaPath]  -> publish a post, log it, print {url}
 *   node gologin_helper.js stop                    -> stop the cloud session
 *
 * Token + profile come from env (GOLOGIN_API_TOKEN + GOLOGIN_PROFILE_ID) or the app's gologin.json.
 * Every post is appended to $HERMES_HOME/gologin_posts.jsonl so the Reporting tab can read it.
 * Prints a single JSON object to stdout. Non-zero exit on hard failure.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

// puppeteer-core is installed globally; make it resolvable from any cwd.
const GLOBAL_MODS = process.env.NODE_PATH || '/opt/node/lib/node_modules';
let puppeteer;
try { puppeteer = require(path.join(GLOBAL_MODS, 'puppeteer-core')); }
catch (e) { try { puppeteer = require('puppeteer-core'); } catch (e2) { fail('puppeteer-core not found: ' + e2.message); } }

const HERMES_HOME = process.env.HERMES_HOME || path.join(os.homedir(), '.hermes');
const CONFIG_PATH = path.join(HERMES_HOME, 'gologin.json');
const POSTS_LOG = path.join(HERMES_HOME, 'gologin_posts.jsonl');

// Supabase (for the Storage image library) — service key + client id from env/profile .env.
const SUPA_URL = (process.env.SUPABASE_URL || '').trim().replace(/\/$/, '');
const SUPA_KEY = (process.env.SUPABASE_SERVICE_KEY || '').trim();
const CLIENT_ID = (process.env.CLIENT_ID || '').trim();
// Each agent has its OWN independent execution memory, keyed by this identity (set per agent via
// GOLOGIN_AGENT). Empty (e.g. instant Chat posts) = the client's default execution memory.
const AGENT = (process.env.GOLOGIN_AGENT || '').trim();

async function supa(method, pathq, payload, extraHeaders) {
  const headers = Object.assign({
    apikey: SUPA_KEY, Authorization: 'Bearer ' + SUPA_KEY, 'Content-Type': 'application/json',
  }, extraHeaders || {});
  const resp = await fetch(SUPA_URL + pathq, {
    method, headers, body: payload != null ? JSON.stringify(payload) : undefined,
  });
  const text = await resp.text();
  let data = null; try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
  return { ok: resp.ok, status: resp.status, data };
}

// List this client's profiles (identities) so the chat/agent knows which to post through.
async function cmdListProfiles() {
  if (!SUPA_URL || !SUPA_KEY || !CLIENT_ID) return { error: 'storage/profiles not configured' };
  const r = await supa('GET', '/rest/v1/client_profiles?select=name,gologin_profile_id&client_id=eq.'
    + encodeURIComponent(CLIENT_ID) + '&order=created_at');
  return { profiles: (r.ok && Array.isArray(r.data)) ? r.data : [] };
}

// Pull the next Storage image NOT yet posted to this platform; download it locally.
async function cmdNextImage(platform) {
  if (!SUPA_URL || !SUPA_KEY || !CLIENT_ID) return { error: 'storage not configured (SUPABASE_*/CLIENT_ID)' };
  const r = await supa('GET', '/rest/v1/media?select=id,url,filename,posted&client_id=eq.'
    + encodeURIComponent(CLIENT_ID) + '&order=created_at.asc&limit=100');
  if (!r.ok) return { error: 'media query failed: ' + r.status };
  const rows = Array.isArray(r.data) ? r.data : [];
  const next = rows.find((m) => !(Array.isArray(m.posted) ? m.posted : [])
    .some((p) => String(p.platform || '').toLowerCase() === platform));
  if (!next) return { image: null, note: 'no unused image for ' + platform };
  // download
  const resp = await fetch(next.url);
  if (!resp.ok) return { error: 'image download failed: ' + resp.status };
  const buf = Buffer.from(await resp.arrayBuffer());
  const ext = (next.filename.match(/\.[A-Za-z0-9]+$/) || ['.jpg'])[0];
  const out = path.join(os.tmpdir(), 'media_' + next.id + ext);
  fs.writeFileSync(out, buf);
  return { image: { mediaId: next.id, path: out, url: next.url, filename: next.filename } };
}

// ── Self-learning memory (per client + platform): remember the selectors/quirks that worked so
// the agent takes the FAST PATH next run and only re-discovers (then re-saves) when something changed.
async function loadMemory(platform) {
  const empty = { selectors: {}, notes: '', runs: 0, _dirty: false };
  if (!SUPA_URL || !SUPA_KEY || !CLIENT_ID) return empty;
  const r = await supa('GET', '/rest/v1/agent_memory?select=selectors,notes,runs&client_id=eq.'
    + encodeURIComponent(CLIENT_ID) + '&agent=eq.' + encodeURIComponent(AGENT)
    + '&platform=eq.' + encodeURIComponent(platform));
  if (r.ok && Array.isArray(r.data) && r.data[0]) {
    return { selectors: r.data[0].selectors || {}, notes: r.data[0].notes || '',
             runs: r.data[0].runs || 0, _dirty: false };
  }
  return empty;
}
async function saveMemory(platform, mem) {
  if (!SUPA_URL || !SUPA_KEY || !CLIENT_ID) return;
  await supa('POST', '/rest/v1/agent_memory',
    { client_id: CLIENT_ID, agent: AGENT, platform, selectors: mem.selectors || {},
      notes: mem.notes || '', runs: (mem.runs || 0) + 1, updated_at: new Date().toISOString() },
    { Prefer: 'resolution=merge-duplicates,return=minimal' });
}
// Resolve a step's element: try the LEARNED selector first (fast), else walk candidate selectors
// (discovery); when a candidate works, LEARN it. Throws if nothing matches.
async function resolveStep(page, mem, stepKey, candidates) {
  const learned = mem.selectors[stepKey];
  if (learned) {
    const el = await page.$(learned).catch(() => null);
    if (el) return el;                       // fast path — the remembered selector still works
  }
  for (const sel of candidates) {
    const el = await page.$(sel).catch(() => null);
    if (el) {
      if (mem.selectors[stepKey] !== sel) { mem.selectors[stepKey] = sel; mem._dirty = true; }
      return el;                             // discovered + learned for next time
    }
  }
  throw new Error('step "' + stepKey + '" not found (no learned or candidate selector matched)');
}

// Stamp a media row as posted to a platform (by an agent), with the post link.
async function markPosted(mediaId, platform, agent, link, at) {
  if (!SUPA_URL || !SUPA_KEY || !mediaId) return;
  const r = await supa('GET', '/rest/v1/media?select=posted&id=eq.' + encodeURIComponent(mediaId));
  const cur = (r.ok && Array.isArray(r.data) && r.data[0] && Array.isArray(r.data[0].posted)) ? r.data[0].posted : [];
  if (cur.some((p) => String(p.platform || '').toLowerCase() === platform)) return;
  cur.push({ platform, agent: agent || 'agent', link: link || '', at });
  await supa('PATCH', '/rest/v1/media?id=eq.' + encodeURIComponent(mediaId), { posted: cur },
    { Prefer: 'return=minimal' });
}

const PLATFORMS = {
  facebook:  { home: 'https://www.facebook.com/', login: /\/login|login\.php/i },
  instagram: { home: 'https://www.instagram.com/', login: /\/accounts\/login|\/accounts\/emailsignup/i },
  tiktok:    { home: 'https://www.tiktok.com/', login: /\/login|\/signup/i },
  threads:   { home: 'https://www.threads.net/', login: /\/login/i },
};

function out(obj) { process.stdout.write(JSON.stringify(obj)); process.exit(0); }
function fail(msg, extra) { process.stdout.write(JSON.stringify(Object.assign({ error: String(msg) }, extra || {}))); process.exit(1); }

function loadConfig() {
  let cfg = {};
  try { cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8')) || {}; } catch (e) { cfg = {}; }
  const token = (process.env.GOLOGIN_API_TOKEN || process.env.GOLOGIN_TOKEN || cfg.token || '').trim();
  const profileId = (process.env.GOLOGIN_PROFILE_ID || cfg.profileId || cfg.profile || '').trim();
  return { token, profileId };
}

function connectUrl(token, profileId) {
  let u = 'https://cloudbrowser.gologin.com/connect?token=' + encodeURIComponent(token);
  if (profileId) u += '&profile=' + encodeURIComponent(profileId);
  return u;
}

async function stopProfile(token, profileId) {
  if (!profileId) return;
  try {
    await fetch('https://api.gologin.com/browser/' + profileId + '/web', {
      method: 'DELETE', headers: { Authorization: 'Bearer ' + token },
    });
  } catch (e) { /* best-effort */ }
}

async function connect(token, profileId) {
  const url = connectUrl(token, profileId);
  // GET first to start the session and surface a clear error reason.
  const resp = await fetch(url).catch((e) => { throw new Error('connect fetch failed: ' + e.message); });
  if (!resp.ok) {
    const reason = resp.headers.get('X-Error-Reason') || resp.statusText;
    throw new Error('cloud browser did not start: ' + reason);
  }
  const browser = await puppeteer.connect({ browserWSEndpoint: url, ignoreHTTPSErrors: true, defaultViewport: null });
  return browser;
}

async function newPage(browser) {
  const pages = await browser.pages();
  const p = pages && pages.length ? pages[0] : await browser.newPage();
  try { await p.setViewport({ width: 1280, height: 800 }); } catch (e) {}
  return p;
}

// Logged-in heuristic (first pass — refine per platform against the live DOM once connected):
// logged OUT if the final URL is a login/signup page OR the page shows a password field.
async function isLoggedIn(page, def) {
  const url = page.url();
  if (def.login.test(url)) return false;
  try {
    const hasPassword = await page.evaluate(() => !!document.querySelector('input[type="password"]'));
    if (hasPassword) return false;
  } catch (e) {}
  return true;
}

async function cmdLoginStatus(browser, wanted) {
  const result = {};
  const list = (wanted && wanted.length) ? wanted : Object.keys(PLATFORMS);
  for (const plat of list) {
    const def = PLATFORMS[plat];
    if (!def) { result[plat] = false; continue; }
    try {
      const page = await newPage(browser);
      await page.goto(def.home, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await new Promise((r) => setTimeout(r, 3000));   // let redirects + the proxy interstitial settle
      result[plat] = await isLoggedIn(page, def);
    } catch (e) { result[plat] = false; }
  }
  return { connected: result };
}

// Navigate the running cloud browser to a URL (used when "Connect <platform>" is clicked so the
// live-view lands on that platform's login page). Reuses the existing first tab.
async function cmdOpenUrl(browser, url) {
  const page = await newPage(browser);
  try { await page.bringToFront(); } catch (e) {}
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
  return { url, title: await page.title().catch(() => '') };
}

async function cmdScrape(browser, url, selector) {
  const page = await newPage(browser);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise((r) => setTimeout(r, 1200));
  let text = '';
  if (selector) {
    text = await page.$eval(selector, (el) => (el.innerText || '').trim()).catch(() => '');
  } else {
    text = await page.evaluate(() => (document.body.innerText || '').trim());
  }
  return { url, text: (text || '').slice(0, 20000) };
}

async function cmdScreenshot(browser, url, outPath) {
  const page = await newPage(browser);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.screenshot({ path: outPath, fullPage: false });
  return { url, path: outPath };
}

function logPost(rec) {
  try {
    fs.mkdirSync(HERMES_HOME, { recursive: true });
    fs.appendFileSync(POSTS_LOG, JSON.stringify(rec) + '\n', 'utf8');
  } catch (e) {}
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Facebook text (+ optional single image) post. Selectors verified against the live DOM:
// opener = [role="button"] "What's on your mind"; textbox = [contenteditable][role=textbox];
// the Post button only appears AFTER text is typed.
async function postFacebook(page, caption, mediaPath, mem) {
  await page.goto('https://www.facebook.com/', { waitUntil: 'networkidle2', timeout: 60000 });
  await sleep(2500);
  try { await page.keyboard.press('Escape'); } catch (e) {}   // close any notifications flyout
  await sleep(600);
  // Open the composer — click the ROLE=BUTTON opener (not a container div).
  const opened = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('[role="button"]'))
      .find((e) => /^what's on your mind|^apa yang anda fikir|^buat siaran/i.test((e.textContent || '').trim()));
    if (b) { b.click(); return true; } return false;
  });
  if (!opened) { mem.notes = (mem.notes + '\n[composer opener [role=button] not found]').trim(); mem._dirty = true; throw new Error('composer opener not found'); }
  await sleep(3500);
  // Composer textbox.
  const box = await resolveStep(page, mem, 'fb_textbox', [
    '[contenteditable="true"][role="textbox"]',
    '[role="dialog"] [contenteditable="true"]',
  ]);
  await box.click();
  await sleep(400);
  await page.keyboard.type(caption, { delay: 12 });
  await sleep(1000);
  if (mediaPath) {
    const fileInput = await resolveStep(page, mem, 'fb_file', [
      'input[type="file"][accept*="image"]', 'input[type="file"]',
    ]).catch(() => null);
    if (fileInput) { await fileInput.uploadFile(mediaPath); await sleep(5000); }
  }
  // Submit — the composer may be multi-step (type → Next → Post) or single (Post). Loop: click Post
  // if present, else Next, until posted.
  let done = false;
  for (let i = 0; i < 4 && !done; i++) {
    const act = await page.evaluate(() => {
      const on = (b) => b && b.getAttribute('aria-disabled') !== 'true';
      const all = Array.from(document.querySelectorAll('[role="button"]'));
      const txt = (b) => (b.textContent || '').trim();
      const al = (b) => b.getAttribute('aria-label') || '';
      let post = all.find((b) => (/^(post|share|kongsi|siar|hantar)$/i.test(txt(b)) || /^post$/i.test(al(b))) && on(b));
      if (post) { post.click(); return 'post'; }
      let next = all.find((b) => /^(next|seterusnya)$/i.test(txt(b)) && on(b));
      if (next) { next.click(); return 'next'; }
      return 'none';
    });
    if (act === 'post') done = true;
    else if (act === 'next') await sleep(2800);
    else break;
  }
  if (!done) { mem.notes = (mem.notes + '\n[submit: no Post/Next button found after typing]').trim(); mem._dirty = true; throw new Error('post button not found'); }
  await sleep(6000);
  // success signal: the composer textbox is gone
  const stillOpen = await page.$('[contenteditable="true"][role="textbox"]').catch(() => null);
  return { url: page.url(), verified: !stillOpen };
}

// Threads text post. Malay/English UI: opener "Apakah yang baharu?/What's new?"; button "Siaran/Post".
async function postThreads(page, caption, mediaPath, mem) {
  await page.goto('https://www.threads.net/', { waitUntil: 'networkidle2', timeout: 60000 });
  await sleep(3500);
  // open composer: click the exact "what's new" placeholder element + its ancestors (proven method)
  const openComposer = () => page.evaluate(() => {
    const PH = ['apakah yang baharu?', "what's new?", 'apa yang baharu?'];
    const el = Array.from(document.querySelectorAll('*'))
      .find((e) => e.childElementCount < 3 && PH.includes((e.textContent || '').trim().toLowerCase()));
    if (el) { let c = el; for (let i = 0; i < 4; i++) { if (c) { c.click(); c = c.parentElement; } } return true; }
    // fallback: the "Create/New thread" nav button (aria-label, multi-locale)
    const b = Array.from(document.querySelectorAll('[aria-label]'))
      .find((e) => /cipta|create|bebenang baharu|new thread|karang/i.test(e.getAttribute('aria-label') || ''));
    if (b) { (b.closest('[role="button"],a,div') || b).click(); return true; }
    return false;
  });
  await openComposer();
  await sleep(2800);
  let box = await page.$('[contenteditable="true"][role="textbox"], [role="dialog"] textarea').catch(() => null);
  if (!box) { await openComposer(); await sleep(2500); box = await page.$('[contenteditable="true"][role="textbox"], [role="dialog"] textarea').catch(() => null); }
  if (!box) { mem.notes = (mem.notes + '\n[threads composer not found]').trim(); mem._dirty = true; throw new Error('threads composer not found'); }
  await box.click(); await sleep(400);
  await page.keyboard.type(caption, { delay: 12 });
  await sleep(1000);
  const posted = await page.evaluate(() => {
    const on = (b) => b && b.getAttribute('aria-disabled') !== 'true';
    const btn = Array.from(document.querySelectorAll('[role="dialog"] [role="button"], [role="button"]'))
      .find((b) => /^(siaran|post|hantar)$/i.test((b.textContent || '').trim()) && on(b));
    if (btn) { btn.click(); return true; } return false;
  });
  if (!posted) { mem.notes = (mem.notes + '\n[threads Siaran/Post button not found]').trim(); mem._dirty = true; throw new Error('threads post button not found'); }
  await sleep(5000);
  return { url: page.url() };
}

async function cmdPost(browser, platform, caption, mediaPath, agent, mediaId, nowIso) {
  const page = await newPage(browser);
  const mem = await loadMemory(platform);   // self-learning: recall what worked last time
  let res;
  if (platform === 'facebook') res = await postFacebook(page, caption, mediaPath, mem);
  else if (platform === 'threads') res = await postThreads(page, caption, mediaPath, mem);
  else throw new Error('posting for "' + platform + '" not wired yet (build against live DOM with the token)');
  try { await saveMemory(platform, mem); } catch (e) {}  // persist learned selectors/notes + bump runs
  const rec = {
    platform, agent: agent || 'chat', caption,
    media: mediaPath ? [mediaPath] : [],
    link: res.url || '', status: 'published', date: nowIso,
    gologin_profile_id: (process.env.GOLOGIN_PROFILE_ID || '').trim(),
  };
  logPost(rec);
  if (mediaId) { try { await markPosted(mediaId, platform, rec.agent, rec.link, nowIso); } catch (e) {} }
  return Object.assign({ ok: true }, rec);
}

async function main() {
  const [cmd, a1, a2, a3, a4] = process.argv.slice(2);
  if (!cmd) fail('usage: gologin_helper.js <login-status|scrape|screenshot|next-image|post|stop> ...');
  const { token, profileId } = loadConfig();
  if (!token) fail('GoLogin token not configured (set GOLOGIN_API_TOKEN or gologin.json)');
  if (cmd === 'stop') { await stopProfile(token, profileId); out({ ok: true }); return; }
  // Storage + self-learning commands need NO browser (pure Supabase):
  if (cmd === 'list-profiles') { out(await cmdListProfiles()); return; }
  if (cmd === 'next-image') { out(await cmdNextImage(String(a1 || '').toLowerCase())); return; }
  if (cmd === 'mark-posted') { await markPosted(a1, String(a2 || '').toLowerCase(), a3 || 'agent', a4 || '', new Date().toISOString()); out({ ok: true }); return; }
  if (cmd === 'get-notes') { const m = await loadMemory(String(a1 || '').toLowerCase()); out({ platform: a1, notes: m.notes, runs: m.runs, learned: Object.keys(m.selectors || {}) }); return; }
  if (cmd === 'add-note') {
    const plat = String(a1 || '').toLowerCase(); const m = await loadMemory(plat);
    const note = (a2 || '').trim(); if (note && !(m.notes || '').includes(note)) m.notes = ((m.notes || '') + '\n' + note).trim();
    await saveMemory(plat, m); out({ ok: true, notes: m.notes }); return;
  }
  if (!profileId && cmd !== 'scrape' && cmd !== 'screenshot') fail('GoLogin profile not configured (set GOLOGIN_PROFILE_ID or gologin.json)');

  let browser;
  try {
    browser = await connect(token, profileId);
    let result;
    if (cmd === 'login-status') result = await cmdLoginStatus(browser, (a1 ? a1.split(',') : []).map((s) => s.trim()).filter(Boolean));
    else if (cmd === 'open-url') result = await cmdOpenUrl(browser, a1);
    else if (cmd === 'scrape') result = await cmdScrape(browser, a1, a2);
    else if (cmd === 'screenshot') result = await cmdScreenshot(browser, a1, a2);
    else if (cmd === 'post') {
      // post <platform> <captionFile|text> [mediaPath] [mediaId]
      const caption = fs.existsSync(a2) ? fs.readFileSync(a2, 'utf8') : String(a2 || '');
      result = await cmdPost(browser, a1, caption, a3 || '', process.env.GOLOGIN_AGENT || '', a4 || '', new Date().toISOString());
    } else fail('unknown command: ' + cmd);
    try { await browser.disconnect(); } catch (e) {}
    out(result);
  } catch (e) {
    try { if (browser) await browser.disconnect(); } catch (e2) {}
    fail(e.message || String(e));
  }
}
main();
