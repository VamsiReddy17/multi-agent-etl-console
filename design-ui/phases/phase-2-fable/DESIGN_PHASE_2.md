# Phase 2 — The Fable: Cinematic Development Chronicle

> **Status:** ✅ Active (Current)  
> **Timeline:** June 13, 2026 – Present  
> **Design System:** Custom Fable Design System (Dark Cinematic Narrative)

---

## Overview

Phase 2 completely redesigned the dashboard from a standard monitoring tool into a **cinematic, narrative-driven development chronicle** called "The Fable." Every development session becomes a chapter, every bug becomes a bestiary entry, and the entire pipeline journey is told as an interactive story.

## Design Philosophy

| Principle | Implementation |
|-----------|---------------|
| **Narrative-Driven** | Development history presented as story chapters, not flat lists |
| **Dark Cinematic** | Deep void blacks (#0a0a0f) with amber/gold accent lighting |
| **Glass-Morphism** | Frosted glass cards with `backdrop-filter: blur(16px)` |
| **Custom Typography** | Playfair Display (serif headings), JetBrains Mono (code), Inter (body) |
| **Progressive Disclosure** | Expandable chapter cards, filtered bug views, tab isolation |
| **Micro-Animations** | Orb pulse, timeline reveal, particle flow, fade transitions |

## Color Palette

```
Void:           #0a0a0f (primary background)
Abyss:          #0f0f14 (secondary background)
Obsidian:       #14141a (card surfaces)
Amber:          #f59e0b (primary accent, navigation highlights)
Amber Glow:     #fbbf24 (emphasis, timeline dots)
Emerald:        #10b981 (success, valid records)
Emerald Glow:   #34d399 (success emphasis)
Crimson:        #ef4444 (errors, quarantine)
Crimson Glow:   #f87171 (error emphasis)
Sapphire:       #3b82f6 (informational)
Violet:         #8b5cf6 (secondary accent)
```

## Typography System

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Display | Playfair Display | 700–800 | Chapter titles, hero headings |
| Display Italic | Playfair Display Italic | 400–500 | Pull quotes, codex entries |
| Mono | JetBrains Mono | 300–600 | Terminal logs, metrics, code blocks |
| Body | Inter | 300–700 | Paragraphs, labels, descriptions |

## The 7 Tabs (Views)

### 1. The Chronicle
**Purpose:** Session timeline — development history as expandable chapter cards  
**Pattern:** Vertical timeline with glowing amber dots, scroll-reveal chapter cards  
**Interaction:** Click to expand/collapse chapter details (activities, issues, fixes)  
**Data:** 7 sessions with tags (feature, bug, fix, perf), aggregate stats at top

### 2. The Bestiary
**Purpose:** Bug tracker — every bug encountered, diagnosed, and conquered  
**Pattern:** Filterable grid of severity-tagged bug cards with progressive disclosure  
**Interaction:** Filter by severity (CRITICAL/HIGH/MEDIUM/LOW), click to expand root cause analysis  
**Data:** 9 bugs with error output, root cause, fix, and lesson learned

### 3. The Codex
**Purpose:** Development narrative — the full story told as a scrollable book  
**Pattern:** Vertical scroll with chapter titles, body text, pull quotes, and milestone badges  
**Interaction:** Read-only narrative flow  
**Data:** 7 narrative entries + prologue with pull quotes and milestone markers

### 4. The Forge
**Purpose:** Live pipeline metrics — real-time throughput, rates, and stage durations  
**Pattern:** Metric tiles (bento grid), horizontal stage duration bars, simulation controls  
**Interaction:** Adjust stream velocity and anomaly rate sliders, pause/resume generator  
**Components:** Metric tiles, stage bars, terminal log feed, DB inspector table

### 5. The Constellation
**Purpose:** Animated data-flow canvas — watch data particles flow through 4 agents  
**Pattern:** Horizontal pipeline of 5 glowing orbs with CSS-animated particle transit  
**Interaction:** Particles auto-generate based on simulation settings (green = valid, red = quarantined)  
**Data:** Real-time counters for valid, quarantined, total processed, and Kafka lag

### 6. The Watchtower
**Purpose:** System topology — monitor all 13 services with interactive failure simulation  
**Pattern:** Service card grid with toggle switches and detail panel  
**Interaction:** Toggle services UP/DOWN to simulate cascading failures, view detail panel  
**Data:** 13 services (infra, orchestrator, agent, monitor) with port, memory, latency  
**Extra:** Pre-deploy safety checklist with interactive checkboxes

### 7. The Quarantine
**Purpose:** Human-in-the-loop anomaly review — review, edit, approve/reject bad records  
**Pattern:** Record cards with JSON payload viewer and inline editor  
**Interaction:** Edit & Fix (opens JSON editor with live parse validation), Approve, Reject  
**Data:** Rolling window of quarantined records from simulation

## Mockup

![The Fable Dashboard](fable_dashboard_mockup.png)

## Key CSS Techniques

| Technique | Implementation |
|-----------|---------------|
| Glass-morphism | `backdrop-filter: blur(16px); background: rgba(20,20,26,0.7)` |
| Custom scrollbar | Thin 4px amber-tinted scrollbar with rounded thumb |
| Timeline dots | `::before` pseudo-elements with `box-shadow` glow |
| Orb pulse | `@keyframes` with scale + opacity cycling |
| Particle flow | Absolute-positioned divs with CSS transitions between 5 step positions |
| Severity badges | Color-coded borders with matching background opacity |
| Toggle switches | Custom checkbox with CSS-only slider track |

## Accessibility Considerations

- High contrast amber text (#f59e0b) on void background (#0a0a0f) = 8.2:1 ratio ✓
- All interactive elements have visible focus states
- Keyboard navigation supported via native HTML semantics
- `prefers-reduced-motion` should be added in Phase 3 for users who disable animations
