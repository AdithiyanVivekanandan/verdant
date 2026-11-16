# Verdant Design System

**Working name:** Verdant
**Product:** AI-Powered Smart Irrigation System for Predictive Water Management and Crop Optimization
**Primary user:** Farmers in India
**Status:** Authoritative design specification

---

## 1. Visual identity

**Design direction:** Botanical / Earth / Instrument

The application should feel:
- Calm
- Professional
- Trustworthy
- Minimal
- Contemporary
- Agriculture-specific
- Easy to understand

**Avoid:**
- AI-generated generic SaaS appearance
- Excessive gradients
- Glassmorphism
- Random illustrations
- Oversized hero sections
- Excessive rounded cards
- Decorative charts
- Unnecessary animations
- Fake AI badges
- Repetitive content blocks
- Excessive dashboard metrics

---

## 2. Colour tokens

### Light theme (Botanical / Earth)

| Token | Name | Hex | Usage |
|-------|------|-----|-------|
| `--color-primary` | Primary forest | #183D32 | Primary buttons, active nav, links, brand |
| `--color-primary-fg` | Primary foreground | #FFFFFF | Text on primary |
| `--color-canopy` | Canopy | #285C45 | Active navigation background, secondary actions |
| `--color-sage` | Sage | #739477 | Secondary accents, muted actions |
| `--color-leaf` | Leaf | #B8C9A8 | Light accents, borders, dividers |
| `--color-canvas` | Canvas | #F6F5EF | Page background |
| `--color-surface` | Surface | #FFFFFF | Card backgrounds, elevated surfaces |
| `--color-border` | Border | #E9EAE1 | Input borders, card borders |
| `--color-text-primary` | Primary text | #333D36 | Headings, labels |
| `--color-text-secondary` | Secondary text | #778078 | Helper text, captions |
| `--color-critical` | Critical | #B64B40 | Errors, destructive actions, critical alerts |
| `--color-caution` | Caution | #C18A36 | Warnings, low moisture |
| `--color-healthy` | Healthy | #3D805B | Success, healthy moisture |
| `--color-info` | Information | #497DA0 | Info messages, stale data |

### Dark theme (deliberately designed — not inverted)

| Token | Name | Hex |
|-------|------|-----|
| `--color-background-dark` | Background | #151D19 |
| `--color-surface-elevated-dark` | Elevated surface | #1E2923 |
| `--color-surface-secondary-dark` | Secondary surface | #26342C |
| `--color-text-primary-dark` | Primary text | #E8EEE8 |
| `--color-text-secondary-dark` | Secondary text | #A5B1A7 |
| `--color-border-dark` | Border | #35443A |
| `--color-primary-dark` | Primary green | #8EAE91 |
| `--color-secondary-dark` | Secondary green | #B8C9A8 |
| `--color-critical-dark` | Critical | #D67A6E |
| `--color-caution-dark` | Caution | #E0A55A |
| `--color-healthy-dark` | Healthy | #6FB083 |
| `--color-info-dark` | Information | #7FA3C0 |

Functional colours are adjusted for readability in dark mode. Dark theme is tested on charts, tables, inputs, dropdowns, modals, sidebar, notifications, and moisture indicators.

---

## 3. Typography

| Language | Font | Usage |
|----------|------|-------|
| English | Manrope or Inter | UI, headings, body |
| Hindi | Noto Sans Devanagari | UI, headings, body |
| Kannada | Noto Sans Kannada | UI, headings, body |
| Tamil (prepared, not selectable) | Noto Sans Tamil | Future |

- Use tabular numerals for measurements (moisture %, temperature °C).
- Font sizes follow a consistent scale; line height 1.4–1.6 for body.
- Font weight: 400 regular, 500 medium, 600 semibold, 700 bold.

---

## 4. Design tokens

### Spacing (4px scale)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight internal padding |
| `--space-2` | 8px | Component gaps |
| `--space-3` | 12px | Section internal spacing |
| `--space-4` | 16px | Default section gap |
| `--space-5` | 20px | Larger section gap |
| `--space-6` | 24px | Page section spacing |
| `--space-8` | 32px | Page horizontal padding (desktop) |
| `--space-10` | 40px | Major page sections |

### Border radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Small elements, badges |
| `--radius-md` | 8px | Inputs, buttons, cards |
| `--radius-lg` | 12px | Large cards, containers |
| `--radius-full` | 9999px | Pills, avatars |

### Shadows

Restrained shadows only:
- `--shadow-sm`: 0 1px 2px rgba(0,0,0,0.04)
- `--shadow-md`: 0 4px 6px rgba(0,0,0,0.06)
- `--shadow-lg`: 0 10px 15px rgba(0,0,0,0.08)

### Breakpoints

| Name | Min width | Usage |
|------|-----------|-------|
| Mobile | < 640px | Single column, bottom nav |
| Tablet | 640–1023px | Collapsible sidebar, reduced padding |
| Desktop | 1024px+ | 248px persistent sidebar |
| Wide desktop | 1440px+ | Max content width ~1440px |

### Component sizing

| Element | Height | Notes |
|---------|--------|-------|
| Input | 44px | Minimum touch target |
| Button | 44px | Minimum touch target |
| Select | 44px | Minimum touch target |
| Sidebar (desktop) | 100vh | 248px wide |
| Sidebar (collapsed) | 100vh | ~76px wide |
| Top bar | 64px | Sticky |
| Bottom nav (mobile) | 72px | Fixed bottom |

### Focus states

- Visible focus ring: 2px, color `--color-primary` (light) / `--color-primary-dark` (dark)
- Offset: 2px
- Applies to all interactive elements

---

## 5. Component library (Verdant customised)

Each component follows the botanical design language. No generic shadcn/ui defaults.

### Application shell
- `AppSidebar` — Desktop persistent sidebar (248px / collapsed 76px)
- `MobileNavigation` — Fixed bottom navigation bar (4 destinations + More sheet)
- `TopBar` — Breadcrumbs, page title area, notification indicator, language, theme, profile
- `PageContainer` — Max-width constrained content area with 32px desktop padding
- `UserMenu` — Profile dropdown
- `ThemeSelector` — Light / Dark / System
- `LanguageSelector` — en / hi / kn

### Data presentation
- `MetricDisplay` — Label + large value + optional context + small icon
- `FieldCard` — Field summary: name, crop, area, location, moisture %, progress, status, sensor ID, last updated
- `MoistureIndicator` — Large percentage + progress bar + status label + colour
- `StatusLabel` — Text + colour + optional icon, accessible (colour not sole indicator)
- `SensorFreshnessIndicator` — Fresh / Delayed / Stale / Missing
- `WeatherSummary` — Current conditions + 5-day preview + source + retrieval time
- `AlertItem` — Severity, field, reason, timestamp, navigation
- `ActivityTimeline` — Field-specific events

### Data entry
- `FormSection` — Section heading + separator
- `FormField` — Label + input + validation message
- `FieldSelector` — Field dropdown with validation
- `SensorSelector` — Sensor dropdown, read-only when auto-populated
- `DateTimeInput` — Date + time, defaults to now
- `ValidationMessage` — Structured error text
- `SubmitButton` — Primary action with loading state

### Data tables
- `DataTable` — Responsive table with compact mobile rows
- `TableToolbar` — Search, filters, grid/list toggle
- `TablePagination` — Pagination controls
- `ExportAction` — CSV export

### Visualization
- `MoistureHistoryChart` — Line chart, Recharts, threshold bands, gaps for missing data
- `ForecastSummary` — Forecast row (preferred over decorative weather chart)

### Feedback
- `EmptyState` — Explanation + primary action
- `ErrorState` — Error message + retry
- `LoadingState` — Skeleton / spinner
- `ConfirmationDialog` — Destructive action confirmation
- `ToastNotification` — Success / error feedback

---

## 6. Moisture interpretation & alerts

Default demonstration thresholds (configurable, not hardcoded):
- < 30%: Low
- 30–44%: Moderate
- 45–75%: Healthy
- > 75%: High

Freshness states (operational defaults):
- Fresh: within 15 minutes
- Delayed: 15 minutes to 1 hour
- Stale: more than 1 hour
- Missing: no valid reading

Alert types: low moisture, high moisture, stale sensor, missing sensor reading, expected rainfall.

Each alert: type, severity, field ID, trigger value, trigger timestamp, explanation.

---

## 7. Data provenance

Every measurement has a traceable origin:
1. User-entered data
2. Actual IoT sensor data
3. External weather data
4. Backend-calculated data
5. Demonstration data

Sensor readings maintain: recorded timestamp, ingestion timestamp, sensor ID, field ID, data source, validation status, measurement values.

---

## 8. PWA

- Web app manifest
- Icons
- Service worker
- Installability
- Offline indicator
- Cached data labelled with last sync time
- No private data cached on shared devices

---

## 9. Accessibility

- Colour is never the only indicator
- Focus rings on all interactive elements
- Sufficient contrast (WCAG AA)
- Keyboard navigable
- Screen-reader labels
- Respect device safe areas (mobile)
- Large touch targets (44px minimum)
- Support long translations without clipping

---

## 10. File locations

- Design tokens: `frontend/app/globals.css` (CSS variables)
- Tailwind theme: `frontend/tailwind.config.js`
- Fonts: loaded via `next/font/google` (Manrope/Inter) and Noto fonts
- Components: `frontend/components/ui/*` and `frontend/components/layout/*`
- Design tokens documentation: this file
