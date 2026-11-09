# checks.md

Every time you correct a board, the fix goes here as a DO or a DON'T. The AI reads this file before it builds a board and checks every frame against it before export. Start with an empty file; these examples show the format. Delete the ones that are not yours.

Format: `- DO / DON'T: the rule (the board that taught it)`

## Canvas
- DO: keep the 480 × 336 camera box bottom-right empty. Nothing readable inside it, ever. (every board)
- DO: keep 60 px padding on every side. Nothing readable outside it.
- DO: make every readable word 28 px or bigger. If it doesn't fit, cut words, don't shrink them.

## Content
- DON'T: put a paragraph on a board. Draw it instead and show one central idea. (too-much-text board)
- DO: one claim per board, written as the title.
- DON'T: invent numbers, logos, quotes or footage. A missing asset is a dashed "pending" card.
- DO: keep footage at its real aspect ratio. Never crop it to fill a box.

## Motion
- DON'T: open a board empty. Something real is on screen from the first frame.
- DO: make everything appear on the word that names it.
- DON'T: let anything sit still for more than 5 seconds while I talk.
- DON'T: slide or zoom the whole board like a camera. Move the elements instead.

## Colour
- DON'T: put dark text on a dark background. On dark panels, text is white.
- DO: one accent colour per idea.

## Your fixes
<!-- Add new rules below this line. Newest at the bottom. -->
- DO: in app-focus boards, place real UI screenshots at true 16:9 or native aspect ratio inside a crisp 1.5px border card with subtle shadow (ticket 011)
- DON'T: show dark glow navy backgrounds (#080d1a) or equal card rows for narrative clinical explainers; use Clean minimal paper (#FFFFFF / #F8F9FA) with one clinical accent (ticket 011)
- DO: use the Broadcast placard theme (C) for all explainer boards: warm charcoal ground (#1F1D1A), card (#262320), warm off-white ink (#F4F1EA), and one accent yellow (#FFB900); no glass, no glowing borders, no cyan/purple gradients (Joey 2026-11-08)
- DON'T: put the Microsoft logo (.ms-stripe) or a location tag (.location-tag) on a board; keep the camera box empty at x1400 y704 480x336 with hairline border and dark placeholder (Joey 2026-11-08)
