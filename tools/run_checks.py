#!/usr/bin/env python3
"""Render and check all starter boards before and after retheme.
Produces:
  /tmp/retheme/before/<name>.png
  /tmp/retheme/after/<name>.png
  /tmp/retheme/sheet-01.png .. sheet-07.png
  Prints table of contrast fails, light-pixel share, cyan pixels, min font, camera.
"""

import asyncio
import glob
import json
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

SEEK = """t => {
  for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
  if (window.seek) window.seek(t);
  if (window.gsap) { gsap.globalTimeline.pause(); gsap.globalTimeline.seek(t, false); }
  document.querySelectorAll('video').forEach(v => { v.pause(); if (v.duration) v.currentTime = t % v.duration; });
}"""

DOM_CHECK_JS = """() => {
  function parseRgb(colorStr) {
    const m = colorStr.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
    if (!m) return null;
    return { r: parseInt(m[1]), g: parseInt(m[2]), b: parseInt(m[3]), a: m[4] !== undefined ? parseFloat(m[4]) : 1 };
  }

  function getLuminance(rgb) {
    const a = [rgb.r, rgb.g, rgb.b].map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }

  function getContrast(rgb1, rgb2) {
    const l1 = getLuminance(rgb1);
    const l2 = getLuminance(rgb2);
    const bright = Math.max(l1, l2);
    const dark = Math.min(l1, l2);
    return (bright + 0.05) / (dark + 0.05);
  }

  function getEffectiveBg(el) {
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    if (cx >= 0 && cy >= 0 && cx < window.innerWidth && cy < window.innerHeight) {
      const under = document.elementFromPoint(cx, cy);
      if (under && under !== el && !el.contains(under)) {
        const sh = under.closest('polygon, rect, path, circle');
        if (sh) {
          const shStyle = window.getComputedStyle(sh);
          const shFill = parseRgb(shStyle.fill);
          if (shFill && shFill.a > 0.5) return shFill;
        }
      }
    }
    let cur = el;
    while (cur && cur !== document.documentElement) {
      const style = window.getComputedStyle(cur);
      const bg = parseRgb(style.backgroundColor);
      if (bg && bg.a > 0.5) {
        return bg;
      }
      cur = cur.parentElement;
    }
    return { r: 31, g: 29, b: 26, a: 1 };
  }

  const elements = Array.from(document.querySelectorAll('*'));
  let contrastFails = [];
  let minFont = 999;

  for (const el of elements) {
    const textNodes = Array.from(el.childNodes).filter(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 0);
    if (textNodes.length === 0) continue;

    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;

    // Inside camera box? (x1400 y704 480x336)
    const isCamera = el.closest('.camera') || (rect.left >= 1390 && rect.top >= 694);
    if (isCamera) continue;

    const isCredit = el.closest('.credit');
    const isPrompt = el.closest('.prompt') || el.closest('.spec');

    const fontSize = parseFloat(style.fontSize);
    if (!isCredit && !isPrompt && fontSize < minFont) {
      minFont = fontSize;
    }

    const textColor = parseRgb(style.color);
    if (!textColor) continue;

    const bgColor = getEffectiveBg(el);
    const contrast = getContrast(textColor, bgColor);
    const isBold = parseInt(style.fontWeight) >= 600 || style.fontWeight === 'bold';
    const isLarge = fontSize >= 36 || (fontSize >= 28 && isBold);
    const required = isLarge ? 3.0 : 4.5;

    if (contrast < required) {
      contrastFails.push({
        text: textNodes.map(n => n.textContent.trim()).join(' ').slice(0, 30),
        fontSize,
        isLarge,
        contrast: contrast.toFixed(2),
        required,
        color: style.color,
        bg: `rgb(${bgColor.r},${bgColor.g},${bgColor.b})`
      });
    }
  }
  // Check SVG text elements
  document.querySelectorAll('svg text, svg tspan').forEach(el => {
    const text = el.textContent.trim();
    if (!text) return;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) return;
    const fill = parseRgb(style.fill || style.color);
    if (!fill) return;
    let bg = { r: 38, g: 35, b: 32 };
    const svg = el.closest('svg');
    if (svg) {
      const shape = svg.querySelector('rect, polygon, path, circle');
      if (shape) {
        const shStyle = window.getComputedStyle(shape);
        const shBg = parseRgb(shStyle.fill);
        if (shBg && shBg.a > 0.5) bg = shBg;
      }
    }
    const contrast = getContrast(fill, bg);
    if (contrast < 3.0) {
      contrastFails.push({
        text: text.slice(0, 30),
        fontSize: parseFloat(style.fontSize) || 28,
        isLarge: true,
        contrast: contrast.toFixed(2),
        required: 3.0,
        color: `rgb(${fill.r},${fill.g},${fill.b})`,
        bg: `rgb(${bg.r},${bg.g},${bg.b}) (svg-shape)`
      });
    }
  });

  const mediaBoxes = [];
  document.querySelectorAll('img, video, .camera, .film, .image').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      mediaBoxes.push({
        left: Math.round(rect.left),
        top: Math.round(rect.top),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom)
      });
    }
  });

  return { contrastFails, minFont: minFont === 999 ? 28 : minFont, mediaBoxes };
}"""

async def render_board(browser, html_path, out_png, check_dom=False):
    page = await browser.new_page(viewport={"width": 1920, "height": 1080})
    await page.goto(f"file://{os.path.abspath(html_path)}")
    await page.wait_for_load_state("networkidle")
    await page.evaluate("document.fonts.ready")
    await page.evaluate(SEEK, 6.0)
    await page.wait_for_timeout(100)
    await page.screenshot(path=out_png)
    
    dom_res = None
    if check_dom:
        dom_res = await page.evaluate(DOM_CHECK_JS)
        
    await page.close()
    return dom_res

def check_image_pixels(png_path, media_boxes):
    im = Image.open(png_path).convert("RGB")
    arr = np.array(im, dtype=np.float32) / 255.0
    h, w, _ = arr.shape
    
    # Mask out media boxes (footage, images, camera box)
    mask = np.ones((h, w), dtype=bool)
    # Default camera box at x1400 y704 480x336
    mask[704:1040, 1400:1880] = False
    
    for mb in media_boxes:
        l = max(0, mb["left"])
        t = max(0, mb["top"])
        r = min(w, mb["right"])
        b = min(h, mb["bottom"])
        mask[t:b, l:r] = False
        
    # Luminance: 0.2126 R + 0.7152 G + 0.0722 B
    lum = 0.2126 * arr[:,:,0] + 0.7152 * arr[:,:,1] + 0.0722 * arr[:,:,2]
    outside_lum = lum[mask]
    light_share = float((outside_lum > 0.85).mean()) if len(outside_lum) > 0 else 0.0
    
    # Cyan pixels check: Hue in [190, 210] degrees, Saturation > 0.4, Value > 0.2
    # RGB to HSV calculation
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    deltac = maxc - minc
    
    s = np.zeros_like(v)
    nonzero_v = v > 0.001
    s[nonzero_v] = deltac[nonzero_v] / v[nonzero_v]
    
    # Hue in degrees
    h_deg = np.zeros_like(v)
    nonzero_d = deltac > 0.001
    
    rc = (maxc - r) / (deltac + 1e-7)
    gc = (maxc - g) / (deltac + 1e-7)
    bc = (maxc - b) / (deltac + 1e-7)
    
    m_r = (r == maxc) & nonzero_d
    m_g = (g == maxc) & nonzero_d
    m_b = (b == maxc) & nonzero_d
    
    h_deg[m_r] = (bc[m_r] - gc[m_r]) * 60.0
    h_deg[m_g] = (2.0 + rc[m_g] - bc[m_g]) * 60.0
    h_deg[m_b] = (4.0 + gc[m_b] - rc[m_b]) * 60.0
    h_deg = h_deg % 360.0
    
    cyan_mask = mask & (h_deg >= 185.0) & (h_deg <= 215.0) & (s > 0.4) & (v > 0.2)
    cyan_count = int(np.sum(cyan_mask))
    
    # Camera box check: verify no high-contrast readable text in camera box
    cam_crop = arr[704:1040, 1400:1880]
    cam_mean = cam_crop.mean()
    cam_ok = cam_mean < 0.25 # Dark placeholder
    
    return {
        "light_pixel_share": light_share,
        "light_pixel_fail": bool(light_share > 0.06),
        "cyan_pixel_count": cyan_count,
        "camera_box_ok": bool(cam_ok)
    }

def build_contact_sheets(board_names, out_dir="/tmp/retheme"):
    # 12 boards per sheet in 3 rows x 4 cols
    # Canvas 3840 x 2160 (or scaled down)
    sheet_w, sheet_h = 3840, 2160
    cols, rows = 4, 3
    thumb_w = sheet_w // cols # 960
    thumb_h = sheet_h // rows # 720
    # Inside each thumb cell, 16:9 board is 960 x 540
    board_scaled_w = 960
    board_scaled_h = 540
    
    num_sheets = math.ceil(len(board_names) / 12)
    sheet_paths = []
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 32)
    except:
        font = ImageFont.load_default()

    for s_idx in range(num_sheets):
        sheet = Image.new("RGB", (sheet_w, sheet_h), (25, 23, 21))
        draw = ImageDraw.Draw(sheet)
        batch = board_names[s_idx * 12 : (s_idx + 1) * 12]
        
        for idx, bname in enumerate(batch):
            r = idx // cols
            c = idx % cols
            cell_x = c * thumb_w
            cell_y = r * thumb_h
            png_path = os.path.join(out_dir, "after", f"{bname}.png")
            if os.path.exists(png_path):
                b_im = Image.open(png_path).resize((board_scaled_w, board_scaled_h), Image.Resampling.LANCZOS)
                sheet.paste(b_im, (cell_x, cell_y + 40))
                
            # Draw label
            draw.text((cell_x + 20, cell_y + 10), f"{bname}", fill=(244, 241, 234), font=font)
            
        sheet_path = os.path.join(out_dir, f"sheet-{s_idx+1:02d}.png")
        sheet.save(sheet_path)
        sheet_paths.append(sheet_path)
        print(f"Saved contact sheet: {sheet_path}")
        
    return sheet_paths

async def main():
    os.makedirs("/tmp/retheme/before", exist_ok=True)
    os.makedirs("/tmp/retheme/after", exist_ok=True)
    
    board_files = sorted([f for f in glob.glob("boards/*.html") if not f.endswith("index.html")])
    board_names = [os.path.splitext(os.path.basename(f))[0] for f in board_files]
    
    print(f"Starting render and checks for {len(board_names)} boards...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        
        results = {}
        
        # We can process in chunks
        chunk_size = 4
        for i in range(0, len(board_names), chunk_size):
            chunk = board_names[i : i + chunk_size]
            tasks = []
            for bname in chunk:
                before_html = f"/tmp/retheme/before/boards/{bname}.html"
                before_png = f"/tmp/retheme/before/{bname}.png"
                after_html = f"boards/{bname}.html"
                after_png = f"/tmp/retheme/after/{bname}.png"
                
                # Render before if not exists
                if not os.path.exists(before_png):
                    tasks.append(render_board(browser, before_html, before_png, check_dom=False))
                else:
                    tasks.append(asyncio.sleep(0))
                    
                # Render after with check
                tasks.append(render_board(browser, after_html, after_png, check_dom=True))
                
            chunk_results = await asyncio.gather(*tasks)
            
            # Map after results
            for idx, bname in enumerate(chunk):
                after_res = chunk_results[idx * 2 + 1]
                after_png = f"/tmp/retheme/after/{bname}.png"
                pixel_res = check_image_pixels(after_png, after_res["mediaBoxes"])
                
                results[bname] = {
                    "contrast_fails": len(after_res["contrastFails"]),
                    "contrast_fail_details": after_res["contrastFails"],
                    "min_font": after_res["minFont"],
                    "light_pixel_share": pixel_res["light_pixel_share"],
                    "light_pixel_fail": pixel_res["light_pixel_fail"],
                    "cyan_pixel_count": pixel_res["cyan_pixel_count"],
                    "camera_box_ok": pixel_res["camera_box_ok"]
                }
                fail_marker = " (LIGHT FAIL)" if pixel_res["light_pixel_fail"] else ""
                print(f"[{i + idx + 1}/{len(board_names)}] {bname}: contrast fails={results[bname]['contrast_fails']}, light={results[bname]['light_pixel_share']:.4f}{fail_marker}, cyan={results[bname]['cyan_pixel_count']}, min_font={results[bname]['min_font']}, cam={'OK' if results[bname]['camera_box_ok'] else 'FAIL'}")
                
        await browser.close()
        
    # Build contact sheets
    sheet_paths = build_contact_sheets(board_names)
    
    # Save results JSON
    with open("/tmp/retheme/results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nRender and verification complete.")

if __name__ == "__main__":
    asyncio.run(main())
