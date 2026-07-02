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
      await new Promise((r) => setTimeout(r, 1500));
      result[plat] = await isLoggedIn(page, def);
    } catch (e) { result[plat] = false; }
  }
  return { connected: result };
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

// Facebook text (+ optional single image) post — best-effort selectors, iterate against live DOM.
async function postFacebook(page, caption, mediaPath) {
  await page.goto('https://www.facebook.com/', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise((r) => setTimeout(r, 2000));
  // Open the composer ("What's on your mind?")
  const opener = await page.evaluateHandle(() => {
    const els = Array.from(document.querySelectorAll('[role="button"], div, span'));
    return els.find((e) => /what's on your mind|apa yang anda fikirkan/i.test(e.textContent || '')) || null;
  });
  if (opener) { try { await opener.asElement().click(); } catch (e) {} }
  await new Promise((r) => setTimeout(r, 2500));
  // Type into the composer textbox
  const box = await page.$('[role="dialog"] [contenteditable="true"], [contenteditable="true"][role="textbox"]');
  if (!box) throw new Error('composer textbox not found');
  await box.click();
  await page.keyboard.type(caption, { delay: 15 });
  await new Promise((r) => setTimeout(r, 800));
  if (mediaPath) {
    const fileInput = await page.$('input[type="file"][accept*="image"], input[type="file"]');
    if (fileInput) { await fileInput.uploadFile(mediaPath); await new Promise((r) => setTimeout(r, 4000)); }
  }
  // Click the Post button
  const posted = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('[role="dialog"] [role="button"]'))
      .find((b) => /^post$|^kongsi$|^siar/i.test((b.textContent || '').trim()));
    if (btn) { btn.click(); return true; }
    return false;
  });
  if (!posted) throw new Error('post button not found');
  await new Promise((r) => setTimeout(r, 5000));
  return { url: page.url() };
}

async function cmdPost(browser, platform, caption, mediaPath, agent, mediaId, nowIso) {
  const page = await newPage(browser);
  let res;
  if (platform === 'facebook') res = await postFacebook(page, caption, mediaPath);
  else throw new Error('posting for "' + platform + '" not wired yet (build against live DOM with the token)');
  const rec = {
    platform, agent: agent || 'chat', caption,
    media: mediaPath ? [mediaPath] : [],
    link: res.url || '', status: 'published', date: nowIso,
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
  // Storage commands need NO browser (pure Supabase):
  if (cmd === 'next-image') { out(await cmdNextImage(String(a1 || '').toLowerCase())); return; }
  if (cmd === 'mark-posted') { await markPosted(a1, String(a2 || '').toLowerCase(), a3 || 'agent', a4 || '', new Date().toISOString()); out({ ok: true }); return; }
  if (!profileId && cmd !== 'scrape' && cmd !== 'screenshot') fail('GoLogin profile not configured (set GOLOGIN_PROFILE_ID or gologin.json)');

  let browser;
  try {
    browser = await connect(token, profileId);
    let result;
    if (cmd === 'login-status') result = await cmdLoginStatus(browser, (a1 ? a1.split(',') : []).map((s) => s.trim()).filter(Boolean));
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
