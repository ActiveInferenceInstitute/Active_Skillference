# Active_Skillference Design System

## 1. Atmosphere & Identity

Active_Skillference feels like a quiet technical command center for a high-integrity learning system. The signature is evidence-first clarity: dense generated artifacts, dependency graphs, and runtime state are presented with restrained surfaces, tabular numbers, and direct status language rather than decorative flourish.

## 2. Color

### Palette

| Role | Token | Light | Usage |
|------|-------|-------|-------|
| Surface/primary | `--surface-primary` | `#ffffff` | Main panels, cards, controls |
| Surface/secondary | `--surface-secondary` | `#f8fafc` | Page background, quiet nested surfaces |
| Surface/tertiary | `--surface-tertiary` | `#eef4fb` | Graph canvases and low-emphasis panels |
| Surface/warning | `--surface-warning` | `#fff7ed` | Local-development credential notice |
| Text/primary | `--text-primary` | `#152238` | Headings and primary body text |
| Text/secondary | `--text-secondary` | `#64748b` | Captions, labels, muted metadata |
| Text/inverse | `--text-inverse` | `#ffffff` | Text on filled primary controls |
| Text/warning | `--text-warning` | `#7c2d12` | Local-development caution copy |
| Text/evidence | `--text-evidence` | `#134e4a` | Evidence-list copy on validated soft surfaces |
| Border/default | `--border-default` | `#d8dee9` | Panel and control borders |
| Accent/primary | `--accent-primary` | `#2563eb` | Primary controls, links, focus rings |
| Accent/secondary | `--accent-secondary` | `#0f766e` | Evidence and validated-state accents |
| Status/success | `--status-success` | `#15803d` | Online/complete status |
| Status/warning | `--status-warning` | `#b45309` | Local-development and caution states |
| Status/error | `--status-error` | `#b91c1c` | Offline/error states |
| Status/info soft | `--status-info-soft` | `#eff6ff` | Low-emphasis informational wash for mixed-state cards |
| Status/evidence soft | `--status-evidence-soft` | `#ecfdf5` | Low-emphasis evidence-list wash |
| Code/surface | `--code-surface` | `#111827` | Runtime JSON panel |
| Code/text | `--code-text` | `#e5e7eb` | Runtime JSON text |
| Warning/border soft | `--warning-border-soft` | `color-mix(...)` | Derived local-login credential border |
| Warning/surface soft | `--warning-surface-soft` | `color-mix(...)` | Derived local-login credential background |
| Graph/edge | `--graph-edge` | `color-mix(...)` | Derived dependency-edge stroke |
| Graph/lane fill | `--graph-lane-fill` | `color-mix(...)` | Derived dependency-lane fill |

### Rules

- Use only the declared tokens in dashboard CSS. Add a token here before adding a new color role.
- `--accent-primary` is reserved for interactive affordances and focus, not decoration.
- Status colors must describe observable runtime state. Do not use local readiness styling to imply live SkillTree readiness.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| H1 | `clamp(1.6rem, 2vw, 2.2rem)` | 750 | 1.2 | 0 | Dashboard title |
| H2 | `1.1rem` | 750 | 1.3 | 0 | Panel headings |
| H3 | `1rem` | 700 | 1.35 | 0 | Card and table section headings |
| Body | `15px` | 400 | 1.5 | 0 | Default dashboard copy |
| Body/sm | `0.88rem` | 400 | 1.45 | 0 | Tables and secondary content |
| Caption | `0.78rem` | 750 | 1.35 | 0 | Labels, pills, metadata |

### Font Stack

- Primary: `Aptos, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- Mono: `"SFMono-Regular", Consolas, "Liberation Mono", monospace`

### Rules

- Use tabular figures for metrics, counts, graph tables, and runtime numbers.
- Do not use Inter as a dashboard default.
- Use sentence case for visible headings and labels.

## 4. Spacing & Layout

### Base Unit

All spacing derives from a base of 4px.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | `4px` | Tight icon/text and label spacing |
| `--space-2` | `8px` | Compact inline groups |
| `--space-3` | `12px` | Small cards and table cells |
| `--space-4` | `16px` | Default panel padding |
| `--space-5` | `20px` | Comfortable groups |
| `--space-6` | `24px` | Header and major group gaps |
| `--space-8` | `32px` | Major dashboard bands |
| `--space-12` | `48px` | Page bottom padding |

### Grid

- Max content width: `1440px`
- Breakpoints: compact at `780px`, narrow at `480px`
- Prefer CSS grid for dashboard regions and data cards. Avoid complex flex width math.

### Radius & Shadow

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `6px` | Buttons, compact controls, and inner metadata groups |
| `--radius-md` | `8px` | Panels, cards, and stable dashboard containers |
| `--shadow-soft` | `0 12px 40px color-mix(...)` | Low-contrast depth on top-level cards only |

## 5. Components

### App header

- **Structure**: title group plus external navigation.
- **Spacing**: `--space-6` gap and responsive horizontal padding.
- **States**: links use button focus and hover states.
- **Accessibility**: nav has a label and the page includes a skip link.

### Button and tab

- **Structure**: native `button` or `a` with `.button` or `.tab`.
- **Variants**: default, primary, small, active tab.
- **States**: hover border shift, active press, visible focus ring, disabled/aria-disabled where needed.
- **Motion**: color and transform transitions only.

### Metric card

- **Structure**: label plus strong numeric/status value.
- **Typography**: tabular numeric treatment.
- **Accessibility**: status values use direct words such as `online`, `offline`, `checking`, or `error`.

### Artifact card

- **Structure**: optional preview, title/path metadata, file state, figure-contract metadata.
- **States**: missing artifacts are visibly muted but remain readable.
- **Accessibility**: image previews use figure alt text when available.

### Runtime panel

- **Structure**: preformatted JSON in a code surface.
- **Typography**: mono stack, tabular figures.
- **Accessibility**: overflow remains keyboard-scrollable and readable on narrow screens.

## 6. Motion & Interaction

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro | `120ms` | `ease` | Hover and active feedback |
| Standard | `180ms` | `ease` | Panel and state transitions |

- Animate only `transform`, `background`, `border-color`, and `color`.
- Respect `prefers-reduced-motion` by disabling smooth scroll and transforms.
- Every interactive element needs visible hover, active, and focus states.

## 7. Depth & Surface

### Strategy

Use borders plus restrained tonal shifts. Shadows are allowed only for the top-level dashboard cards that need to read as independent status surfaces.

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-soft` | `0 12px 40px rgba(21, 34, 56, 0.08)` | Status cards and top-level panels |
| `--radius-sm` | `6px` | Buttons, small cards, graph nodes |
| `--radius-md` | `8px` | Panels, cards, artifact previews |

Do not add heavy shadows, glow effects, decorative gradients, or one-off radii to the dashboard.
