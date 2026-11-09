# Tokens: colour, type, shape

The "Broadcast placard" (Joey) theme (Direction C). Solid warm charcoal ground, off-white typography, hairline borders, and accent yellow (#FFB900). Zero blur shadows: elevation by surface shift and hairline borders. No glass, glow, or cyan.

## Colour: warm charcoal, off-white ink, accent yellow

### Ink and paper
| Token | Hex / RGB | Use | Contrast vs Ground |
|---|---|---|---|
| Ink | `#F4F1EA` | Headline, primary values, body text | 13.8:1 (AAA) |
| Secondary ink | `#C9C3B8` | Secondary labels, descriptions | 8.9:1 (AAA) |
| Muted ink | `#968E82` | Eyebrows, axis ticks, timestamps, credit line | 4.6:1 (AA) |
| Ground (paper) | `rgb(31 29 26)` (`#1F1D1A`) | Master canvas ground (solid, no dot grid) | 1.0:1 (base) |
| Card (wash/chrome) | `rgb(38 35 32)` (`#262320`) | Elevated module & container panel | 1.1:1 |
| Tag pill | `#45403A` | Status pill surface (10px radius) | 1.5:1 |
| Hairline rule | `rgba(244, 241, 234, 0.16)` | 1px card borders & dividers | 1.3:1 |
| Subtle rule | `rgba(244, 241, 234, 0.08)` | Subtle grid & background rails | 1.1:1 |
| Accent yellow | `#FFB900` | The one accent: active state, focal point, links | 9.4:1 (AAA) |
| Accent tint | `#3A3020` | Dark warm accent panel fill (~15% on charcoal) | - |

The paper ground is solid `#1F1D1A`. One accent per idea.

### Card tints (fill / text)
| Card | Fill | Text | Meaning |
|---|---|---|---|
| Plain | `#262320` | `#F4F1EA` | Neutral module |
| Blue / Accent | `#3A3020` | `#F4F1EA` | A tool, model, or highlighted item |
| Green | `#2A3220` | `#F4F1EA` | Good, what we keep |
| Violet | `#362C22` | `#F4F1EA` | Identity, warm contrast |
| Rose | `#3A2520` | `#F4F1EA` | Problems, misses |
| Solid accent | `#FFB900` | `#1F1D1A` | The answer / focal pill (dark text on yellow) |
| Code | `#262320` | `#7FBA00` | Code / telemetry panel |

### Signals
| Signal | Hex | Role | Contrast vs Ground |
|---|---|---|---|
| Positive / ✓ works | `#7FBA00` | Green micro-indicator | 7.2:1 (AAA) |
| Negative / ✕ wrong | `#F25022` | Red micro-indicator | 4.8:1 (AA) |
| Example tag | `#F25022` | Mandatory "EXAMPLE / SYNTHETIC" border | 4.8:1 (AA) |

Never dark text on a dark fill. Text sitting on an accent yellow fill `#FFB900` must become dark ink `#1F1D1A`.

## Type: Segoe UI, JetBrains Mono, one serif aside

Font stack:
`'Segoe UI', system-ui, sans-serif` for body, titles, cards.
`'JetBrains Mono', ui-monospace, monospace` for code, tags, eyebrows.
`'Instrument Serif', serif` for handwritten aside notes.

Every readable word at 28 px or more. Only the credit line and full-screen prompt syntax go smaller.

| Role | Face | Size / line-height | Tracking |
|---|---|---|---|
| Title / Claim | `Segoe UI`, system-ui | 70–76 / 1.08 | −.035em (underline marker with #FFB900) |
| Card heading | `Segoe UI`, system-ui | 42–48 / 1.08 | 0 |
| Hero metric number | `Segoe UI`, system-ui | 112 / 1.0 | −.03em tabular |
| Body / Explanation | `Segoe UI`, system-ui | 30 / 1.35 | 0 |
| Sticker / Pill | `Segoe UI`, system-ui | 54 / 1 | −.02em (#1F1D1A on #FFB900) |
| Tag | `JetBrains Mono` | 28–36 / 1.08 | 0 |
| Eyebrow | `JetBrains Mono` | 24–28 | .08em caps |
| Prompt | `JetBrains Mono` | 21 / 1.38 | only inside full panel |
| Credit | `Segoe UI`, system-ui | 18 / 30 | `#968E82`, bottom-left |

## Shape and elevation: hairline borders, zero blur shadows

| Element | Spec |
|---|---|
| Card | border 1px `rgba(244, 241, 234, 0.16)` · radius 6px · shadow none/hairline |
| Tag pill | border 1px `rgba(244, 241, 234, 0.22)` · radius 10px · background `#45403A` |
| Footage tile | radius 6px · border 1px `rgba(244, 241, 234, 0.16)` · never cropped |
| Focus ring | `0 0 0 3px #FFB900` |
| Elevation | Solid opaque surface shifts (`#262320` over `#1F1D1A`). Zero blur shadows. |

## Easing

GSAP eases, with CSS equivalents:
- `power2.out` ≈ broadcast placard reveal
- `power1.inOut` ≈ data flow pulse
- `power3.out` ≈ number ticker count-up
