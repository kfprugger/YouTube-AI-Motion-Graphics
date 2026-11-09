#!/usr/bin/env python3
"""Property-aware retheming tool for Explainer Board System.
Converts boards to Direction C "Broadcast Placard" (Joey).
Driven by tools/retheme_map.json. Idempotent.
"""

import argparse
import glob
import json
import os
import re
import sys

def load_role_map(map_path):
    with open(map_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_brand_css(brand_css_path):
    with open(brand_css_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def normalize_hex(color_str):
    s = color_str.strip().upper()
    if s.startswith("#") and len(s) == 4:
        return f"#{s[1]*2}{s[2]*2}{s[3]*2}"
    return s

TARGET_COLORS = {
    "#1F1D1A", "#262320", "#2D2A26", "#3A3020", "#2A3220", "#362C22", "#3A2520", "#332E28", "#45403A",
    "#151515", "#1C1A17",
    "#F4F1EA", "#C9C3B8", "#968E82",
    "#FFB900", "#7FBA00", "#F25022", "#F45828", "#E08A1E",
    "RGBA(244,241,234,.16)", "RGBA(244,241,234,.08)", "RGBA(244,241,234,.22)",
    "RGBA(31,29,26,.88)", "RGBA(31,29,26,.45)"
}

def is_target_color(color_str, role=""):
    norm = normalize_hex(color_str).upper()
    if role == "text" and norm == "#F25022":
        return False
    if norm in TARGET_COLORS:
        return True
    if any(norm.lower().startswith(prefix) for prefix in [
        "rgba(244,241,234", "rgba(244, 241, 234",
        "rgba(31,29,26", "rgba(31, 29, 26",
        "rgba(255,185,0", "rgba(255, 185, 0",
        "rgba(242,80,34", "rgba(242, 80, 34",
        "rgba(127,186,0", "rgba(127, 186, 0",
        "rgba(224,138,30", "rgba(224, 138, 30",
    ]):
        return True
    return False

def map_color(color_val, role, role_map, unclassified=None):
    if is_target_color(color_val, role):
        return color_val
    norm = normalize_hex(color_val)
    role_dict = role_map.get("roles", {}).get(role, {})
    if norm in role_dict:
        return role_dict[norm]
    if color_val in role_dict:
        return role_dict[color_val]
    for k, v in role_dict.items():
        if k.upper() == norm.upper():
            return v
            
    if unclassified is not None:
        unclassified.add((role, color_val))
    return color_val

def transform_declaration(prop, val, element_classes, has_yellow_bg, role_map, unclassified, is_highlighter=False):
    prop_clean = prop.strip().lower()
    val_clean = val.strip()
    
    # Check font-family
    if prop_clean in ("font-family", "font"):
        for old_f, new_f in role_map.get("fonts", {}).items():
            if old_f in val_clean:
                val_clean = val_clean.replace(old_f, new_f)
    
    # Determine role
    if prop_clean in ("color", "-webkit-text-fill-color"):
        # If element is sticker, or inside yellow background, text is dark ink #1F1D1A
        if has_yellow_bg or any(c in element_classes for c in ["sticker", "feedtag", "cav"]):
            return prop_clean, "#1F1D1A"
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "text", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
        
    elif prop_clean in ("background", "background-color"):
        # Sticker or accent dot/pin background is always #FFB900
        if "sticker" in element_classes or any(c in element_classes for c in ["pin", "marker"]):
            return prop_clean, "#FFB900"
        
        # Highlighter sweeps: 35% opacity glowing tint
        if is_highlighter:
            val_up = val_clean.upper()
            if any(c in val_up for c in ["#DBEAFE", "#EFF6FF", "#FFF6C2", "#BFDBFE", "#FFE24A"]):
                return prop_clean, "rgba(255,185,0,.35)"
            if any(c in val_up for c in ["#FFE4E6", "#FFF5F2", "#FECDD3", "#F6D2B4"]):
                return prop_clean, "rgba(242,80,34,.35)"
            if any(c in val_up for c in ["#D1FAE5", "#ECFDF5", "#A7F3D0", "#F2FAF7"]):
                return prop_clean, "rgba(127,186,0,.35)"
        
        # Flatten repeating gradient / slot gradient
        if "repeating-linear-gradient" in val_clean:
            return prop_clean, "#262320"
        if "radial-gradient" in val_clean:
            val_clean = re.sub(r",?\s*radial-gradient\([^)]+\)", "", val_clean).strip()
            if not val_clean or val_clean.lower() in ("#fff", "#ffffff", "white"):
                return prop_clean, "#1F1D1A"
        if "linear-gradient(178deg" in val_clean:
            return prop_clean, "transparent"
            
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "background", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
    elif prop_clean.startswith("--sh-") or prop_clean.endswith("-shadow") or prop_clean == "--b" or prop_clean == "box-shadow":
        val_no_space = re.sub(r"\s+", " ", val_clean)
        bs_map = role_map.get("roles", {}).get("box-shadow", {})
        if val_no_space in bs_map:
            return prop_clean, bs_map[val_no_space]
        if "rgba(17,24,39," in val_no_space or "rgba(30,32,34," in val_no_space:
            return prop_clean, "0 0 0 1px rgba(244,241,234,.16)"
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "border", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
        
    elif any(prop_clean.startswith(b) for b in ["border", "outline"]):
        # Focus frame borders (3px-6px #DBEAFE) -> accent #FFB900
        if "#DBEAFE" in val_clean.upper() and any(w in val_clean for w in ["3px", "4px", "5px", "6px"]):
            new_val = re.sub(r"#DBEAFE\b", "#FFB900", val_clean, flags=re.IGNORECASE)
            return prop_clean, new_val
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "border", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
    elif prop_clean == "box-shadow":
        val_no_space = re.sub(r"\s+", " ", val_clean)
        bs_map = role_map.get("roles", {}).get("box-shadow", {})
        if val_no_space in bs_map:
            return prop_clean, bs_map[val_no_space]
        if "rgba(17,24,39," in val_no_space or "rgba(30,32,34," in val_no_space:
            return prop_clean, "0 0 0 1px rgba(244,241,234,.16)"
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "border", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
        
    elif prop_clean == "fill":
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "svg-fill", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
        
    elif prop_clean == "stroke":
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "svg-stroke", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val
        
    else:
        new_val = re.sub(
            r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)",
            lambda m: map_color(m.group(0), "text", role_map, unclassified),
            val_clean
        )
        return prop_clean, new_val

def transform_style_str(style_str, element_classes, parent_is_yellow, role_map, unclassified):
    decls = style_str.split(";")
    is_highlighter = "/" in style_str or any(c in element_classes for c in ["highlighter", "hl", "sweep"])
    
    has_bright_bg = parent_is_yellow or any(c in element_classes for c in ["sticker", "cav", "feedtag"])
    has_color_prop = False
    for d in decls:
        if ":" in d:
            p, v = d.split(":", 1)
            p = p.strip().lower()
            v_upper = v.strip().upper()
            if p in ("color", "-webkit-text-fill-color"):
                has_color_prop = True
            if p in ("background", "background-color"):
                if any(c in v_upper for c in [
                    "#2563EB", "#3B82F6", "#BFDBFE", "#FFB900",
                    "#7FBA00", "#10B981", "#059669",
                    "#E08A1E", "#D97706",
                    "VAR(--INDIGO)", "VAR(--HI)", "VAR(--STICKER)", "VAR(--MINT)"
                ]):
                    has_bright_bg = True

    new_decls = []
    for d in decls:
        if not d.strip():
            continue
        if ":" in d:
            prop, val = d.split(":", 1)
            new_prop, new_val = transform_declaration(prop, val, element_classes, has_bright_bg, role_map, unclassified, is_highlighter)
            new_decls.append(f"{new_prop}: {new_val}")
        else:
            new_decls.append(d)
            
    if has_bright_bg and not has_color_prop:
        new_decls.append("color: #1F1D1A")
        
    return "; ".join(new_decls)
def transform_css_block(css_text, role_map, unclassified):
    def replace_rule(match):
        selector = match.group(1)
        body = match.group(2)
        classes = re.findall(r"\.([a-zA-Z0-9_-]+)", selector)
        is_yellow = any(c in classes for c in ["sticker", "feedtag", "cav"])
        transformed_body = transform_style_str(body, classes, is_yellow, role_map, unclassified)
        return f"{selector}{{{transformed_body}}}"

    return re.sub(r"([^{}]+)\{([^{}]+)\}", replace_rule, css_text)

def retheme_html(content, role_map, brand_css_content, unclassified):
    replacements_count = 0
    orig = content

    # 1. Update Google Fonts link (remove Inter, keep Mono and Serif)
    fonts_pat = r'<link\s+href="https://fonts\.googleapis\.com/css2\?[^"]*family=Inter[^"]*"\s+rel="stylesheet">'
    new_fonts_link = '<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet">'
    if re.search(fonts_pat, content):
        content = re.sub(fonts_pat, new_fonts_link, content)
        replacements_count += 1

    # 2. Update preamble and inlined brand.css block
    # Standard head/body backgrounds
    content = re.sub(r"html,body\{margin:0;background:#1a1a1a\}", r"html,body{margin:0;background:#1F1D1A}", content)
    content = re.sub(r"body\{margin:0;background:#FFFFFF\}", r"body{margin:0;background:#1F1D1A}", content)
    content = re.sub(r"a\{color:#2563EB\}a:hover\{color:#2A37A8\}", r"a{color:#FFB900}a:hover{color:#FFB900}", content)

    brand_pat = r"/\* =+\s+EXPLAINER BOARD SYSTEM · brand\.css.*?.ebs \.tbl \.r>div\.sp\{[^}]+\}"
    if re.search(brand_pat, content, re.DOTALL):
        content = re.sub(brand_pat, brand_css_content, content, count=1, flags=re.DOTALL)
        replacements_count += 1

    # 3. Transform board-specific CSS (anything after brand.css inside <style>)
    def style_block_repl(sm):
        attrs = sm.group(1)
        full_style = sm.group(2)
        # Find where brand.css ends
        end_marker = ".ebs .tbl .r>div.sp{font:700 24px var(--space);color:var(--ink)}"
        if end_marker in full_style:
            idx = full_style.find(end_marker) + len(end_marker)
            before = full_style[:idx]
            after = full_style[idx:]
            transformed_after = transform_css_block(after, role_map, unclassified)
            return f"<style{attrs}>{before}{transformed_after}</style>"
        else:
            # If no brand.css in this style block (e.g. head style), transform directly
            return f"<style{attrs}>{transform_css_block(full_style, role_map, unclassified)}</style>"

    content = re.sub(r"<style([^>]*)>(.*?)</style>", style_block_repl, content, flags=re.DOTALL)

    # 4. Transform inline style attributes and SVG presentation attributes
    def tag_repl(match):
        tag_str = match.group(0)
        class_m = re.search(r'\bclass=["\']([^"\']+)["\']', tag_str)
        classes = class_m.group(1).split() if class_m else []
        is_yellow = any(c in classes for c in ["sticker", "feedtag", "cav"])
        
        # Transform style attribute
        def style_attr_repl(sm):
            quote = sm.group(1)
            style_content = sm.group(2)
            transformed = transform_style_str(style_content, classes, is_yellow, role_map, unclassified)
            return f'style={quote}{transformed}{quote}'
            
        tag_str = re.sub(r'\bstyle=(["\'])(.*?)\1', style_attr_repl, tag_str)
        
        # Transform SVG attributes
        def attr_repl(am):
            attr_name = am.group(1).lower()
            quote = am.group(2)
            attr_val = am.group(3)
            if attr_val.lower() == "none" or attr_val.startswith("url("):
                return am.group(0)
            tag_name_m = re.match(r"<([a-zA-Z0-9_-]+)", tag_str)
            tname = tag_name_m.group(1).lower() if tag_name_m else ""
            if attr_name == "fill":
                if tname in ("text", "tspan"):
                    new_c = map_color(attr_val, "text", role_map, unclassified)
                else:
                    new_c = map_color(attr_val, "svg-fill", role_map, unclassified)
            elif attr_name == "stroke":
                new_c = map_color(attr_val, "svg-stroke", role_map, unclassified)
            elif attr_name == "stop-color":
                new_c = map_color(attr_val, "svg-fill", role_map, unclassified)
            else:
                new_c = attr_val
            return f'{attr_name}={quote}{new_c}{quote}'
        tag_str = re.sub(r'\b(fill|stroke|stop-color)=(["\'])(.*?)\2', attr_repl, tag_str, flags=re.IGNORECASE)
        
        def font_attr_repl(fm):
            quote = fm.group(1)
            fval = fm.group(2)
            for old_f, new_f in role_map.get("fonts", {}).items():
                if old_f in fval:
                    fval = fval.replace(old_f, new_f)
            return f'font-family={quote}{fval}{quote}'
        tag_str = re.sub(r'\bfont-family=(["\'])(.*?)\1', font_attr_repl, tag_str, flags=re.IGNORECASE)
        return tag_str
    content = re.sub(r'<[a-zA-Z0-9_-]+(?:\s+[^>]+)?>', tag_repl, content)

    # 5. Transform GSAP scripts / script blocks
    def script_repl(match):
        script_body = match.group(1)
        def gsap_prop_repl(gm):
            key = gm.group(1)
            quote = gm.group(2)
            val = gm.group(3)
            role = "text"
            if key == "backgroundColor":
                role = "background"
            elif key == "borderColor":
                role = "border"
            elif key == "fill":
                role = "svg-fill"
            elif key == "stroke":
                role = "svg-stroke"
            elif key == "boxShadow":
                role = "box-shadow"
            new_v = map_color(val, role, role_map, unclassified)
            return f'{key}: {quote}{new_v}{quote}'
            
        transformed_script = re.sub(
            r'\b(color|backgroundColor|borderColor|fill|stroke|boxShadow)\s*:\s*(["\'])(.*?)\2',
            gsap_prop_repl,
            script_body
        )
        return f'<script>{transformed_script}</script>'

    content = re.sub(r'<script>(.*?)</script>', script_repl, content, flags=re.DOTALL)

    if content != orig:
        replacements_count += 1

    return content, replacements_count

def main():
    parser = argparse.ArgumentParser(description="Retheme boards to Direction C")
    parser.add_argument("boards", nargs="*", help="Board HTML files to process")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing")
    parser.add_argument("--map", default="tools/retheme_map.json", help="Path to role map JSON")
    parser.add_argument("--brand-css", default="skills/explainer-board-system/assets/brand.css", help="Path to brand.css")
    args = parser.parse_args()

    role_map = load_role_map(args.map)
    brand_css_content = load_brand_css(args.brand_css)

    files = args.boards
    if not files:
        files = sorted([f for f in glob.glob("boards/*.html") if not f.endswith("index.html")])

    total_changed = 0
    unclassified_all = set()

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        unclassified = set()
        new_content, count = retheme_html(content, role_map, brand_css_content, unclassified)

        if unclassified:
            unclassified_all.update(unclassified)

        if new_content != content:
            total_changed += 1
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Updated {fpath} ({count} passes)")
            if not args.dry_run:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
        else:
            print(f"No change {fpath}")

    print(f"\nSummary: {total_changed} files changed out of {len(files)}")
    if unclassified_all:
        print("\nUnclassified colors encountered:")
        for role, col in sorted(unclassified_all):
            print(f"  Role '{role}': {col}")

if __name__ == "__main__":
    main()
