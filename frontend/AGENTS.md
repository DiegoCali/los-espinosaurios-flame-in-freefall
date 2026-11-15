# Frontend execution notes

The approved master plan is in ../PLAN.md. Only the Home vertical slice is implemented.

- Keep scientific investigations read-only; never train or invent results.
- Use app/ for route adapters and src/_app, _pages, widgets, features, entities and shared for FSD layers. Create entities when scientific integration begins.
- Keep English and Spanish dictionaries complete. Internal Next links omit basePath; public assets use shared/config.ts.
- Home references: Figma 215:2 desktop, 385:3 mobile, 385:137 tablet. Compact screens have different content from desktop.
- Preserve original local SVG assets and local fonts. Motion owns UI animation; respect reduced motion.
- Run npm run check and npm run build at milestones. Do not run broad browser suites during hackathon iteration.
- Other routes are honest delivery placeholders. Next task: Research catalog, after manual Home approval.
- No Git writes, deployment or changes to remote settings without explicit instruction.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
