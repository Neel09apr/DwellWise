---
name: DwellWise
description: The public planning record for every Irish town, posted the way the law posts a planning notice.
colors:
  ground: "#e2e3df"
  notice: "#ffffff"
  board: "#f2cf1d"
  board-ink: "#121212"
  board-muted: "#3a3300"
  ink: "#121212"
  prose: "#2c2d2e"
  muted: "#55595d"
  rule: "#cdd0d2"
  wash: "#f6f2d2"
  failure: "#9c1c12"
  tie: "#2d2f31"
  brand-green: "#0e4a2f"
  brand-gold: "#c99a2e"
typography:
  board-title:
    fontFamily: "Archivo Variable, Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.6rem, 8vw, 5.75rem)"
    fontWeight: 800
    lineHeight: 0.92
    letterSpacing: "-0.02em"
  notice-heading:
    fontFamily: "Archivo Variable, Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1.5rem, 3vw, 2.1rem)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "-0.01em"
  board-line:
    fontFamily: "Archivo Variable, Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1.05rem, 1.6vw, 1.25rem)"
    fontWeight: 500
    lineHeight: 1.35
  body:
    fontFamily: "Archivo Variable, Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Archivo Variable, Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 600
rounded:
  control: "2px"
spacing:
  notice-gap: "1.5rem"
  notice-pad: "clamp(1.5rem, 3.5vw, 2.5rem)"
  board-pad: "clamp(2.25rem, 5vw, 3.5rem)"
  page: "72rem"
  measure: "46rem"
components:
  board:
    backgroundColor: "{colors.board}"
    textColor: "{colors.board-ink}"
    padding: "{spacing.board-pad}"
  notice:
    backgroundColor: "{colors.notice}"
    textColor: "{colors.ink}"
    padding: "{spacing.notice-pad}"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.notice}"
    rounded: "{rounded.control}"
    padding: "0.75rem 1.5rem"
  input:
    backgroundColor: "{colors.notice}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "44px"
---

# DwellWise design

Recorded on 27 November 2026 from the built site (M15b to M15e), not from intentions. Product truth is in
[`PRODUCT.md`](PRODUCT.md); the system design (architecture, data, milestones) is in
[`docs/DESIGN.md`](docs/DESIGN.md). The tokens live in `app/web/src/styles.css`.

## Overview

**The Site Notice.** Every place (Ireland, a county, a town) and the cost estimate opens on one
statutory-yellow board: the place in very large heavy condensed capitals, a place line, the record written as
the notice's prescribed lines, and the "describes places, never a particular site, not planning advice" line.
The evidence follows on white notices pinned in order to a grey hoarding. The reader reads the record in the
notice's own words, then each notice with its source and date at its foot. Light only: the scene is a desk in
daylight, and briefs get printed.

## Colors

Restrained. Grey ground, white notices, ink text and marks. **Yellow belongs to the board alone**: no figure,
state, alert or control is ever yellow or red, so nothing reads as a warning. Links are ink, underlined (1px,
2px on hover); there is no blue. Text on the board that is quieter than ink uses `board-muted`, tinted from the
yellow, never grey. The logo's green and gold appear only in the logo and wordmark. `failure` is for error
text only.

## Typography

One face, Archivo (variable, OFL), self-hosted from `@fontsource-variable/archivo`; nothing loads from a third
party. Two registers: heavy (800) condensed capitals (`font-stretch` 72 to 85%) for the board title and notice
headings, and plain weights for everything else. Fixed sizes come from a short scale, 0.8, 0.9, 1 and 1.25rem;
only display type (the board title, notice headings, headline figures) uses larger or fluid sizes. Figures are
tabular everywhere. Labels on data (table heads, fact names) are sentence case at 0.8rem, weight 600, muted, with
normal tracking; capitals belong to the board and notice headings only. There are no eyebrow labels above
headings and no section numbers.

## Layout

Spacing sits on a 4px grid (0.25rem steps; a 2px nudge only inside small controls). Pages are 72rem wide;
prose keeps a 46rem measure. Under the board, a column of notices 1.5rem apart; on
screens 64rem or wider a sticky side list of the notices sits to its left (plain links). The notices column is
`minmax(0, 1fr)` so a wide table never stretches it: wide tables scroll inside a named, focusable region with a
sticky first column. Sections far below the fold use `content-visibility: auto` with a size placeholder.

Wide pages use their width through container queries, not media queries. When the page container (`.with-rail`)
is 66rem or wider, short notices (`.notice-half`) pair up two to a row at equal height, and long ones span both
columns; a short notice with no short neighbour spans the row again. Pairs follow reading order (no
`grid-auto-flow: dense`), so the brief runs constraints (wastewater, protected sites), then activity (planning
precedents, construction started), then the market (sale prices) beside the question box. When the board is 50rem
or wider its prescribed lines go two by two. On phones everything is one column, the board's lines stay one per
row and its border insets to 12px. Long lists show their first five rows and the rest behind "Show all".

## Elevation & Depth

One elevation, for physical objects only: the board and every notice carry `0 1px 1px` plus a soft
`0 6px 18px -6px` lift, as paper pinned to a hoarding. Nothing else casts a shadow. No borders around notices;
a notice's heading carries a 3px ink rule beneath it.

## Shapes

Boards and notices are square-cornered. Each is held by four cable-tie points (2.5px dots, inset 9px) at its
corners; the board adds the statutory notice's printed 2px ink border, inset 20px. Controls take a 2px radius.

## Components

- **Board** (`Board.tsx`): title, place line, prescribed lines (a ruled list; each line is the figure in heavy
  type inline in a full statement, its detail in brackets, linking to its notice), foot line. `disclaimer={false}`
  on boards showing the user's own figures (the cost estimate).
- **Notice**: any `section` in a `.notices` column. Heading in heavy capitals with the 3px rule; an "about" line
  in muted text; its source and capture date at its foot.
- **Controls**: inputs, selects, the search and question boxes are ruled boxes (1.5px ink) on white; buttons are
  black plates in heavy capitals with a 3px yellow ring on hover. Focus is a 3px ink outline with a yellow halo.
- **Side list** (`PageRail.tsx`): marks the notice in view in bold with a 2px underline (never colour alone) and
  `aria-current`; natively with `scroll-target-group` where supported, otherwise an IntersectionObserver on the
  line across the middle of the screen.
- **Sortable tables** (`SortHeader.tsx`, `sortText.ts`): a button inside each column heading, `aria-sort` on the
  sorted heading only, small up and down marks, numbers compared as numbers and text by locale ignoring case; one
  visually hidden status line says what was sorted. The first press sorts ascending, a repeat flips it. A table
  that shows its first five rows sorts all of them, then shows the first five.
- **Charts**: bars in ink; the month still filling in is hatched (a mark), never paler. Every chart has a table
  behind "Show as a table".
- **Logo**: two hollow half-roof bands, green left and gold right, meeting at the ridge (coded SVG,
  `app/web/public/mark-small.svg`), with the wordmark "DwellWise" in mixed case in the green.

## Do's and Don'ts

- Do keep yellow on the board only, and state as a mark (hatch, dash, rule), never a hue.
- Do write the record as statements a notice would print, with the figure inline.
- Do put each notice's source and capture date at its foot.
- Don't use a big-number, small-label stat grid; it reads as a dashboard, not a notice.
- Don't add eyebrow labels, section numbers, card grids, gradients or extra shadows.
- Don't use typed characters (›, →, •) as icons; a row that is a link needs no arrow.
- Don't load fonts or styles from a third party (the CSP forbids it).
- Don't add dark mode without a design for content on a dark ground; the notices stay white either way.
