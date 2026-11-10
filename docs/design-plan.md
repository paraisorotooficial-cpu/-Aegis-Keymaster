# F0 Design plan — Aegis Keymaster

Reviewed against brief §6 before any UI code. One deliberate idea: **the typing line is the only glowing object in the app.** Everything else is deep navy glass with hairline borders; neon is rationed to the cursor, the active key and milestone moments.

## 1. Color (Neon theme, 9 tokens — the 6 core + 3 states)

| Token | Hex | Use |
|---|---|---|
| `void` | `#060914` | App background (deep space) |
| `panel` | `#0D1326` | Panels, sidebars, cards (used sparingly, not everything is a card) |
| `line` | `#1E2A4A` | Hairline borders, dividers |
| `cyan` | `#19E3FF` | The single glow: cursor, active key, primary action, live WPM |
| `magenta` | `#FF3DCB` | Milestones only: lesson approved, stars, new record |
| `amber` | `#FFB547` | Weak keys (heatmap + review mode) |
| `error` | `#FF4D6D` | Wrong char + underline (never color alone) |
| `text` | `#E6ECFF` | Primary text |
| `text-dim` | `#8FA0C8` | Pending text, secondary labels |

Light: `#F5F7FC` base, `#121936` text, darkened accents `#007C95` / `#B0188A`, amber `#B26A00`, error `#C81E4A`, panel `#FFFFFF`, line `#D8DEEC`.
Dark: neutral `#0B0E16` / `#141926` / `#232B44`, same hues at reduced saturation, glow reduced.
Contrast: all text tokens verified ≥ 4.5:1 vs their background by `scripts/check_contrast.py` (F6).

## 2. Typography

| Family | License | Role |
|---|---|---|
| **Inter** | OFL (bundled in `assets/fonts/` with `OFL.txt`) | All UI: labels, buttons, stats, reports. Neutral, excellent small-size legibility, full Spanish coverage (á é í ó ú ü ñ Á Ñ ¿ ¡). |
| **JetBrains Mono** | OFL (bundled) | Practice text, typing area, live counters. Distinct rhythm, tall x-height, unambiguous `l/1/I`, `0/O`, full Spanish coverage. |

Loaded via `QFontDatabase.addApplicationFont`; fallbacks: `Ubuntu`, `DejaVu Sans` (UI) and `DejaVu Sans Mono`, `Liberation Mono` (mono) — real fonts present on Lubuntu. No "futuristic" display font anywhere; personality comes from color and motion, not a gimmick typeface. Two families, clearly separated roles.

## 3. Layout (ASCII sketches)

Course / practice screen (default landing):

```
+--------------------------------------------------------------+
| * AEGIS   [ Curso ]  Test  Progreso  Ajustes      Neon v     |  <- 48px top bar, hairline bottom
+--------------------------------------------------------------+
|  LECCIÓN 03 · Fila superior                     ***  2/15    |  <- breadcrumb row, text-dim
|                                                              |
|        t e  y t  e y t  r y t u  t y u r  ...                |  <- TYPING LINE (the only neon:
|        ----- cursor slides here -----                        |     cyan cursor + active char glow)
|                                                              |
|  42 WPM · 97 % · 0 errores         [ Reiniciar ] [ Siguiente ] |
+--------------------------------------------------------------+
| [ virtual keyboard, 90 % opacity, active key cyan ]          |  <- collapsible
+--------------------------------------------------------------+
```

Live test:

```
+--------------------------------------------------------------+
|  TEST 3 MIN      02:41        58 WPM   96 %                  |  <- countdown cyan >30 s, amber <10 s
|                                                              |
|              (same typing line as course)                    |
+--------------------------------------------------------------+
```

Report:

```
+--------------------------------------------------------------+
|  RESULTADO DEL TEST · 3 min            nuevo record          |  <- magenta only if record
|                                                              |
|   58          96 %        91 %        87 %                   |
|  WPM neto   precision     consistencia  vs mejor marca       |  <- 4 big numbers, mono
|  +--------------------------------------+                   |
|  |  speed per 5 s (QPainter line chart) |                   |
|  +--------------------------------------+                   |
|  teclas debiles: e - r - n   (heatmap strip)                 |
|                                                              |
|        [ Repasar teclas débiles ]  [ Repetir test ]          |
+--------------------------------------------------------------+
```

Progress panel: left rail = summary numbers + streak; right = WPM trend line, accuracy line, per-duration records, then full-width keyboard heatmap (toggle error/latency), history table with filters at the bottom.
Settings: single column, grouped (Apariencia / Sonido / Mecanografía / Datos), no tabs; every control keyboard-reachable.

Alignment: 12-column grid, 24 px outer margin, 8 px spacing rhythm; typing area max-width 72 chars centered.

## 4. Principles (what makes this design its own)

1. **One glowing object.** Neon budget is spent exclusively on the typing line + active key. If a mockup glows anywhere else, it is wrong.
2. **Data as texture, not cards.** Stats are typographic (big mono numbers on the void background, hairline separators) — no grid of identical rounded cards.
3. **Motion is a reply, not a performance.** The only autonomous motion is the boot sequence; everything else answers an action (keystroke ripple, lesson-approved pulse, countdown).
4. **Honest errors.** Wrong char = red + underline + (optional) the key you actually pressed, shown small below the line.
