# Graph Report - Workspace  (2026-08-29)

## Corpus Check
- Corpus is ~13,109 words - fits in a single context window. You may not need a graph.

## Summary
- 233 nodes · 312 edges · 16 communities (15 shown, 1 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.87)
- Token cost: 184,337 input · 0 output

## Community Hubs (Navigation)
- App UI Components
- AI Brief Content Corpus
- Kakao Send Pipeline
- GitHub Actions Content Triggers
- Design System and Content Contract
- App Package Manifest
- Model Compression Research
- App Runtime Dependencies
- AI Agent Ecosystem
- Content Check Assertions
- Brand Icon Set
- TypeScript Config
- New Content Type Procedure

## God Nodes (most connected - your core abstractions)
1. `getReports()` - 9 edges
2. `reports/YYYY-MM-DD.md contract` - 8 edges
3. `Daily Design System (Quiet Morning Briefing)` - 8 edges
4. `send_concert_alert()` - 7 edges
5. `getConcerts()` - 7 edges
6. `Content Flow (_source -> content.ts -> dist)` - 7 edges
7. `update_github_secret()` - 6 edges
8. `send_kakao()` - 6 edges
9. `scripts` - 6 edges
10. `notify-app dispatch job` - 6 edges

## Surprising Connections (you probably didn't know these)
- `getPapers() loader` --shares_data_with--> `ParetoQ: Scaling Laws in Extremely Low-bit LLM Quantization`  [INFERRED]
  Daily_Report_App/AGENTS.md → Daily_Report/reports/2026-08-10.md
- `MR-GPTQ (Micro-Rotated-GPTQ)` --semantically_similar_to--> `InfiniPot-V: Memory-Constrained KV Cache Compression for Streaming Video Understanding`  [INFERRED] [semantically similar]
  Daily_Report/reports/2026-07-22.md → Daily_Report/reports/2026-07-18.md
- `getReports() loader` --shares_data_with--> `Prune-then-Quantize or Quantize-then-Prune?`  [INFERRED]
  Daily_Report_App/AGENTS.md → Daily_Report/reports/2026-08-03.md
- `getTools() loader` --shares_data_with--> `OpenClaw (ex Clawdbot/Moltbot)`  [INFERRED]
  Daily_Report_App/AGENTS.md → Daily_Report/reports/2026-08-17.md
- `Find latest changed concert alert step` --semantically_similar_to--> `Find latest changed report step`  [INFERRED] [semantically similar]
  Daily_Report/.github/workflows/send-concert-alert.yml → Daily_Report/.github/workflows/send-kakao-report.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Kakao send pipeline (find changed markdown then push to Kakao)** — _github_workflows_send_kakao_report_find_report, _github_workflows_send_kakao_report_send_kakao_message, _github_workflows_send_concert_alert_find_alert, _github_workflows_send_concert_alert_send_kakao_concert_alert, daily_report_agents_kakao_refresh_token [EXTRACTED 1.00]
- **Content repo to App contract surface** — daily_report_agents_reports_markdown_contract, daily_report_agents_concerts_markdown_contract, daily_report_agents_state_seen_json_contract, daily_report_agents_deploy_chain, daily_report_agents_daily_report_app, _github_workflows_notify_app_content_updated_event [EXTRACTED 1.00]
- **On-device memory reduction without retraining** — daily_report_reports_2026_07_10_sim_llm, daily_report_reports_2026_07_18_infinipot_v, daily_report_reports_2026_07_22_microscaling_fp4_quantization, daily_report_reports_2026_07_27_slimlm [INFERRED 0.85]
- **On-device LLM quantization design axes (order, bit-width, transform)** — daily_report_reports_2026_08_03_prune_then_quantize, daily_report_reports_2026_08_10_paretoq, daily_report_reports_2026_08_12_fptquant [INFERRED 0.85]
- **Local-first agent harnesses with messenger/MCP surfaces** — daily_report_reports_2026_08_03_goose, daily_report_reports_2026_08_12_hermes_agent, daily_report_reports_2026_08_17_openclaw, daily_report_reports_2026_08_03_prompt_injection_risk [INFERRED 0.85]
- **Daily Archive content pipeline (source repo to GitHub Pages)** — daily_report_app_agents_content_contract, daily_report_app_agents_content_flow, daily_report_app_agents_reports_source_dir, daily_report_app_github_workflows_deploy_build, daily_report_app_github_workflows_deploy_deploy, daily_report_app_product_static_no_runtime_api [EXTRACTED 1.00]
- **Daily Archive PWA / home-screen icon set** — daily_report_app_public_icon, daily_report_app_public_icon_192, daily_report_app_public_icon_512, daily_report_app_public_apple_touch_icon [INFERRED 0.85]

## Communities (16 total, 1 thin omitted)

### Community 0 - "App UI Components"
Cohesion: 0.08
Nodes (31): { concert }, date, { report, featured = false }, empty, items, bySelectedDateDesc(), Concert, field() (+23 more)

### Community 1 - "AI Brief Content Corpus"
Cohesion: 0.09
Nodes (31): reports/YYYY-MM-DD.md contract, Distilling LLM Agent into Small Models with Retrieval and Code Tools, First-thought prefix prompting, OpenClaw (formerly Clawdbot/Moltbot), AI Morning Brief 2026-08-17 (latest sent message), Self-consistent action generation, Skill marketplace malicious-skill risk, Inter-Task KV Reuse (+23 more)

### Community 2 - "Kakao Send Pipeline"
Cohesion: 0.11
Nodes (22): GitHub Secrets API로 시크릿 업데이트, update_github_secret(), build_github_file_url(), build_message(), clean_markdown(), mask_in_logs(), concerts/YYYY-MM-DD.md 의 공연 알림을 카카오톡 '나에게 보내기'로 발송한다., refresh_access_token() (+14 more)

### Community 3 - "GitHub Actions Content Triggers"
Cohesion: 0.11
Nodes (26): repository_dispatch content-updated, notify-app dispatch job, Soft-fail when GH_PAT missing (fall back to daily cron), Find latest changed concert alert step, send-concert-alert job, Send Kakao concert alert step, Find latest changed report step, git diff + sort|tail latest-file selection (+18 more)

### Community 4 - "Design System and Content Contract"
Cohesion: 0.10
Nodes (26): Content Format Contract (canonical in Daily_Report AGENTS.md), Content Flow (_source -> content.ts -> dist), getConcerts() loader, REPORTS_SOURCE_DIR, The Ambient-Only Rule (shadows), The Briefing-Then-Detail Rule, Concert Card component, Daily Design System (Quiet Morning Briefing) (+18 more)

### Community 5 - "App Package Manifest"
Cohesion: 0.12
Nodes (15): devDependencies, @types/markdown-it, @types/node, name, private, scripts, build, check (+7 more)

### Community 6 - "Model Compression Research"
Cohesion: 0.15
Nodes (14): getPapers() loader, getReports() loader, Compression Order as Design Variable, Progressive Intensity Hypothesis, Prune-then-Quantize or Quantize-then-Prune?, 2-to-3-bit Learning Transition, ParetoQ: Scaling Laws in Extremely Low-bit LLM Quantization, Data-free On-device Adapter Merging (+6 more)

### Community 7 - "App Runtime Dependencies"
Cohesion: 0.15
Nodes (13): astro, @astrojs/check, dependencies, astro, @astrojs/check, @fontsource-variable/noto-sans-kr, @fontsource-variable/noto-serif-kr, markdown-it (+5 more)

### Community 8 - "AI Agent Ecosystem"
Cohesion: 0.17
Nodes (13): getTools() loader, Agentic AI Foundation (AAIF), Goose (Block / AAIF agent), MCP Tool Ecosystem, Prompt Injection Risk in Agents, browser-use, Composite Storage (workflow/memory/observability split), Mastra 1.0 (+5 more)

### Community 9 - "Content Check Assertions"
Cohesion: 0.33
Nodes (5): afterLastKnownConcert, concerts, papers, reports, tools

### Community 10 - "Brand Icon Set"
Cohesion: 0.90
Nodes (5): Apple Touch Icon, Daily Archive App Icon (SVG source), PWA Icon 192px (any maskable), PWA Icon 512px (any maskable), Document-and-Dot Brand Mark

### Community 11 - "TypeScript Config"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, extends, astro/tsconfigs/strict

## Knowledge Gaps
- **61 isolated node(s):** `name`, `version`, `private`, `type`, `dev` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Content Flow (_source -> content.ts -> dist)` connect `Design System and Content Contract` to `AI Agent Ecosystem`, `Model Compression Research`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `reports/YYYY-MM-DD.md contract` connect `AI Brief Content Corpus` to `GitHub Actions Content Triggers`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `reports/YYYY-MM-DD.md contract` (e.g. with `Find latest changed report step` and `AI Morning Brief 2026-08-17 (latest sent message)`) actually correct?**
  _`reports/YYYY-MM-DD.md contract` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `version`, `private` to the rest of the system?**
  _61 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.08305647840531562 - nodes in this community are weakly interconnected._
- **Should `AI Brief Content Corpus` be split into smaller, more focused modules?**
  _Cohesion score 0.08602150537634409 - nodes in this community are weakly interconnected._
- **Should `Kakao Send Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.1103448275862069 - nodes in this community are weakly interconnected._