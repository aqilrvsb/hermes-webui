#!/usr/bin/env node
// Convert irinabuht12-oss/marketing-skills (flat .md files) into Hermes skill dirs.
// Runs at BUILD time with /opt/node/bin/node (the runtime venv python doesn't exist yet).
// Usage: node import_marketing_skills.js <src_repo_dir> <dest_dir>
const fs = require("fs"), path = require("path");
const [, , src, dest] = process.argv;
const GROUPS = ["Skills for Claude", "Skills for Clawdbot", "Clawdbot Ads Crew"];
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
let n = 0;
for (const g of GROUPS) {
  const gd = path.join(src, g);
  let files;
  try { files = fs.readdirSync(gd); } catch (e) { continue; }
  for (const fn of files.sort()) {
    if (!fn.toLowerCase().endsWith(".md") || fn.toLowerCase().startsWith("readme")) continue;
    const stem = fn.slice(0, -3), sl = slug(stem);
    const txt = fs.readFileSync(path.join(gd, fn), "utf8");
    const m = txt.replace(/^﻿/, "").match(/^\s*---\s*\n([\s\S]*?)\n---\s*\n/);
    let out;
    if (m && m[1].includes("name:")) {
      out = txt; // already a valid skill
    } else {
      let title = stem, desc = "";
      for (const ln of txt.split(/\r?\n/)) {
        const s = ln.trim();
        if (s.startsWith("#") && title === stem) title = s.replace(/^#+\s*/, "");
        else if (s && !s.startsWith("#") && s !== "---" && !desc) desc = s;
        if (title !== stem && desc) break;
      }
      const name = slug(title.replace(/[^\w\s-]/g, "")) || sl;
      desc = (desc || title).replace(/\n/g, " ").slice(0, 300);
      out = "---\nname: " + name + "\ndescription: " + JSON.stringify(desc) +
            "\nmetadata:\n  source: " + JSON.stringify(g) + "\n---\n\n" + txt;
    }
    const d = path.join(dest, sl);
    fs.mkdirSync(d, { recursive: true });
    fs.writeFileSync(path.join(d, "SKILL.md"), out);
    n++;
  }
}
console.log("== imported " + n + " marketing skills -> " + dest + " ==");
