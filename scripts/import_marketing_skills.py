#!/usr/bin/env python3
"""Convert irinabuht12-oss/marketing-skills (flat .md files) into Hermes skill dirs.

Hermes discovers a skill as a DIRECTORY containing SKILL.md with YAML frontmatter
(name + description). This repo ships flat .md files: some already have proper
frontmatter, others (the "Ads Crew") put a '# Title' first and use '---' as a
divider. For the latter we synthesize valid frontmatter from the title + first line.

Usage: import_marketing_skills.py <src_repo_dir> <dest_dir>
"""
import json, os, re, sys

src, dest = sys.argv[1], sys.argv[2]
GROUPS = ["Skills for Claude", "Skills for Clawdbot", "Clawdbot Ads Crew"]
FM = re.compile(r"^﻿?\s*---\s*\n(.*?)\n---\s*\n", re.S)

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

n = 0
for g in GROUPS:
    gd = os.path.join(src, g)
    if not os.path.isdir(gd):
        continue
    for fn in sorted(os.listdir(gd)):
        if not fn.lower().endswith(".md") or fn.lower().startswith("readme"):
            continue
        stem = fn[:-3]
        slug = slugify(stem)
        txt = open(os.path.join(gd, fn), encoding="utf-8").read()
        m = FM.match(txt)
        if m and "name:" in m.group(1):
            out = txt  # already a valid skill
        else:
            title, desc = stem, ""
            for ln in txt.splitlines():
                s = ln.strip()
                if s.startswith("#") and title == stem:
                    title = re.sub(r"^#+\s*", "", s)
                elif s and not s.startswith("#") and s != "---" and not desc:
                    desc = s
                if title != stem and desc:
                    break
            name = slugify(re.sub(r"[^\w\s-]", "", title)) or slug
            desc = (desc or title).replace("\n", " ")[:300]
            out = ("---\nname: %s\ndescription: %s\nmetadata:\n  source: %s\n---\n\n"
                   % (name, json.dumps(desc, ensure_ascii=False), json.dumps(g))) + txt
        d = os.path.join(dest, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(out)
        n += 1

print("== imported %d marketing skills -> %s ==" % (n, dest))
