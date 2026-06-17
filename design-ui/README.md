# 🎨 Design UI — Dashboard Design History & System

This directory tracks the complete **UI/UX design evolution** of the Multi-Agent ETL Console dashboard — from the initial Google Material 3 design to the current cinematic Fable system.

---

## 📁 Directory Structure

```
design-ui/
├── README.md .......................... This file — overview and navigation
├── DESIGN_SYSTEM.md ................... Master design system with industry research
├── phases/
│   ├── phase-1-material3/
│   │   ├── DESIGN_PHASE_1.md .......... Phase 1 design doc & retrospective
│   │   └── material3_dashboard_mockup.png
│   ├── phase-2-fable/
│   │   ├── DESIGN_PHASE_2.md .......... Phase 2 design doc (active)
│   │   └── fable_dashboard_mockup.png
│   └── phase-3-observatory/
│       └── DESIGN_PHASE_3.md .......... Phase 3 design doc (intelligence layer)
└── mockups/
    ├── material3_dashboard_mockup.png .. Phase 1 mockup (archived)
    └── fable_dashboard_mockup.png ..... Phase 2 mockup (current)
```

---

## 🔄 Phase Evolution

| Phase | Name | Status | Timeline | Design System |
|-------|------|--------|----------|---------------|
| **1** | [Google Material 3](phases/phase-1-material3/DESIGN_PHASE_1.md) | ~~Superseded~~ | May 20 – Jun 8, 2026 | Light theme, M3 cards, system fonts |
| **2** | [The Fable](phases/phase-2-fable/DESIGN_PHASE_2.md) | **Active** ✅ | Jun 13 – Present | Dark cinematic, glass-morphism, custom typography |
| **3** | [The Observatory](phases/phase-3-observatory/DESIGN_PHASE_3.md) | **Active** ✅ | Jun 17, 2026 | ⌘K palette, toasts, sparklines, keyboard nav, a11y |
| **4** | The Nexus | *Planned* | TBD | AI chat, flame charts, light theme, collaboration |

---

## 📖 Key Documents

| Document | Description |
|----------|-------------|
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Master reference — industry research, 8 design principles, full color/typography/spacing spec, component library, accessibility audit, and future roadmap |
| [DESIGN_PHASE_1.md](phases/phase-1-material3/DESIGN_PHASE_1.md) | Retrospective on the original Material 3 dashboard — what worked, what didn't, and lessons applied to Phase 2 |
| [DESIGN_PHASE_2.md](phases/phase-2-fable/DESIGN_PHASE_2.md) | Active design specification for The Fable — 7 tabs, glass-morphism system, CSS techniques, and accessibility review |
| [DESIGN_PHASE_3.md](phases/phase-3-observatory/DESIGN_PHASE_3.md) | Observatory intelligence layer — ⌘K palette, keyboard shortcuts, toasts, sparklines, search, accessibility |

---

## 🏢 Industry Inspirations

The design system was researched against how these companies build their dashboards:

- **Datadog** — Integrated observability, F-pattern layout, context linking
- **Grafana** — Plugin modularity, dashboard-as-code, real-time WebSocket
- **Linear** — Calm UI, keyboard-first, minimal chrome, high contrast
- **Vercel** — Deployment timelines, instant feedback, progressive reveal
- **Netflix / Spotify (Backstage)** — Service catalogs, golden paths, persona-driven views
- **Uber** — Schema registry UI, pipeline DAG viewer, cost attribution

Full analysis in [DESIGN_SYSTEM.md § Industry Research](DESIGN_SYSTEM.md#industry-research).
