---
name: new-project
description: Scaffold a new developer project — create its workspace folder, bind it to a GitHub repo + Supabase project + Vercel project via an AGENTS.md, optionally creating those resources. Use whenever starting a new app/project.
---
# New Project Scaffold

Each project is self-contained: one workspace folder + one GitHub repo + one Supabase project + one Vercel project, recorded in the project's `AGENTS.md`.

Steps (confirm before creating any PAID resource):
1. Ask for: project name, and whether to create new or reuse existing GitHub/Supabase/Vercel resources.
2. Workspace: ensure `/workspace/<name>` exists (Add Space, or mkdir).
3. GitHub: `create_repository` (or use existing). Record `owner/repo`.
4. Supabase: `list_projects`; if new, `get_cost` -> `confirm_cost` -> `create_project`. Record the project **ref**.
5. Vercel (CLI, not MCP): from the project workspace run `vercel link --yes --token=$VERCEL_TOKEN` (creates/links the project), or `vercel projects ls --token=$VERCEL_TOKEN` to reuse. Record its name. Later deploys: `vercel deploy --prod --token=$VERCEL_TOKEN`.
6. Write `/workspace/<name>/AGENTS.md`:
   ```
   # Project: <name>
   github_repo: <owner/repo>
   supabase_project_ref: <ref>
   vercel_project: <vercel-name>
   # The developer agent must use ONLY these resources for this project.
   ```
7. Summarize what was created + the bindings.

Never touch resources belonging to another project.
