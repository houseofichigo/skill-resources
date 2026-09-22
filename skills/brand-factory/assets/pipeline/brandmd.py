#!/usr/bin/env python3
"""out/tokens.json -> out/BRAND.md — the file an AI actually reads."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))
C, R, M, D = T["color"], T["ramp"], T["measured_contrast"], T["density"]
TY, A, V = T["type"], T["a11y"], T["voice"]
NL = chr(10)


def core_rows():
    out = []
    for k, v in C.items():
        if isinstance(v, dict) and "hex" in v:
            out.append(f"| **{k}** | `{v['hex']}` | {v.get('role','')} |")
    for k, v in C.get("accents", {}).items():
        if isinstance(v, dict):
            out.append(f"| {v.get('label',k)} | `{v['hex']}` | "
                       f"wayfinding only — never a button, never body copy |")
    for k, v in C.get("semantic", {}).items():
        if isinstance(v, dict):
            out.append(f"| {k} | `{v['hex']}` | {v.get('use','')}; "
                       f"text is {v.get('text','ink')} |")
    return NL.join(out)


BODY = f"""# {T['brand']} — brand rules

Version {T['version']} · {T['date']}. Supersedes {T['supersedes']}.

{T['positioning']}

**This file is generated from `tokens.json`.** When prose and tokens
disagree, the tokens win — but they cannot disagree, because this was
written from them.

---

## Colour

| Token | Hex | Role |
|---|---|---|
{core_rows()}

### Interaction, derived from the brand colour

Hover and pressed are **fixed values, never `opacity`**. Opacity lets the
surface behind show through, so the same button changes colour depending on
what is under it.

{NL.join(f"- `--{k}` `{v}`" for k, v in R.items())}

### Measured, all of it

{NL.join(f"- {k} — **{v['ratio']}:1** (floor {v['floor']}:1)" for k, v in M.items())}

### Retired — their presence identifies old material

{NL.join(f"- `{v}`" for k, v in C.get('retired',{}).items() if not k.startswith('$'))}

---

## Type

{NL.join(f"- **{TY[k]['family']}** — {TY[k].get('use','')}. Weights {TY[k].get('weights','')}." + ("" if TY[k].get('has_italic', True) else " **No italic exists; never synthesise one.**") for k in ('display','text','mono'))}

Fonts are **self-hosted**. Never link a font service: a page that does
renders in a fallback face without failing loudly — it looks right to
whoever made it and wrong to everyone else.

Tracking: {" · ".join(f"`{k}` {v}" for k, v in TY['tracking'].items() if not k.startswith('$'))}

`font-synthesis-weight:none; font-synthesis-style:none` on `body`, always.

---

## Shape

`{T['shape']['surface']}` holds content · `{T['shape']['control']}px` you
press · `{T['shape']['floating']}px` floats. Nothing above
{T['shape']['floating']}px.

**No `box-shadow`, at any elevation.** Separation comes from surface,
border weight and a scrim.

---

## Density

A row is exactly `2 × pad + one line box`. These numbers were derived, not
chosen, and the build fails if they stop adding up.

{NL.join(f"- **{k}** — row {v['row']}px, padding {v['pad_y']}/{v['pad_x']}px, text {v['text']}px. {v.get('use','')}" for k, v in D.items())}

---

## Accessibility

Target: **{A['target']}**. Hit area **{A['target_min_px']}×{A['target_min_px']}px**
minimum. Focus is `:focus-visible`, never `:focus`; `outline:none` without a
replacement ring is a defect, not a style choice.

---

## Voice

Banned: {" · ".join(f"*{w}*" for w in V['banned'] if not w.startswith('$'))}

---

## The rules that break most often

- A retired colour reappears.
- A font service is linked instead of self-hosting.
- `opacity` is used as a hover state.
- A logo image has no `align-self` guard and stretches into an oval.
- A bare `@media (max-width:…)` fires during PDF export.
- Print type sizes are carried into the product, or product density into print.
- A control has an undefined state, so it ships the browser default.
"""

(ROOT / "out" / "BRAND.md").write_text(BODY, encoding="utf-8")
print(f"out/BRAND.md written · {len(BODY)} bytes · ~{len(BODY.split())} words")
