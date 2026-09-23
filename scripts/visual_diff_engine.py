"""
RDSO Track Drawing Automated Visual Diff & Comparison Engine
Author: Antigravity AI - Advanced Agentic Coding for Indian Railways
"""

import os
import sys
import pymupdf
from PIL import Image, ImageDraw

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def extract_crops():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    drawings_dir = os.path.join(repo_root, "drawings")
    crops_dir = os.path.join(repo_root, "crops")
    ensure_dir(crops_dir)

    drawings = {
        "alt10": os.path.join(drawings_dir, "RDSO_T_6155_ALT_10.pdf"),
        "alt12": os.path.join(drawings_dir, "RDSO_T_6155_ALT_12.pdf"),
        "alt13": os.path.join(drawings_dir, "2025-01-28-RDSO_T_6155_ALT_13.pdf"),
        "layout_6154": os.path.join(drawings_dir, "RDSO_T_6154_ALT_6.pdf"),
        "crossing_6280": os.path.join(drawings_dir, "RDSO_T_6280_ALT_4.pdf"),
        "switch_7075": os.path.join(drawings_dir, "RDSO_T_7075_ALT_1.pdf")
    }

    # Region coordinates (x0, y0, x1, y1) in relative coordinates [0..1]
    regions = {
        "alteration_table": (0.74, 0.70, 0.99, 0.98),
        "detail_b_area": (0.50, 0.55, 0.85, 0.80),
        "notes": (0.02, 0.70, 0.50, 0.98),
        "spares_list": (0.87, 0.02, 1.0, 0.45)
    }

    print("[*] Extracting high-resolution crops from drawings...")
    extracted_paths = {}

    for key in ["alt10", "alt12", "alt13"]:
        pdf_path = drawings.get(key)
        if not pdf_path or not os.path.exists(pdf_path):
            continue
        
        doc = pymupdf.open(pdf_path)
        page = doc[0]
        w, h = page.rect.width, page.rect.height

        for reg_name, (x0, y0, x1, y1) in regions.items():
            rect = pymupdf.Rect(x0 * w, y0 * h, x1 * w, y1 * h)
            pix = page.get_pixmap(clip=rect, dpi=200)
            out_name = f"{key}_{reg_name}.png"
            out_path = os.path.join(crops_dir, out_name)
            pix.save(out_path)
            extracted_paths[f"{key}_{reg_name}"] = out_path
            print(f"    Saved: {out_name} ({pix.width}x{pix.height})")

    # Extra crops for new drawings if available
    if os.path.exists(drawings["layout_6154"]):
        doc = pymupdf.open(drawings["layout_6154"])
        p = doc[0]
        rect = pymupdf.Rect(0.05 * p.rect.width, 0.15 * p.rect.height, 0.95 * p.rect.width, 0.65 * p.rect.height)
        pix = p.get_pixmap(clip=rect, dpi=150)
        out_path = os.path.join(crops_dir, "layout_6154_plan.png")
        pix.save(out_path)
        extracted_paths["layout_6154_plan"] = out_path

    if os.path.exists(drawings["crossing_6280"]):
        doc = pymupdf.open(drawings["crossing_6280"])
        p = doc[0]
        rect = pymupdf.Rect(0.20 * p.rect.width, 0.20 * p.rect.height, 0.80 * p.rect.width, 0.70 * p.rect.height)
        pix = p.get_pixmap(clip=rect, dpi=150)
        out_path = os.path.join(crops_dir, "crossing_6280_plan.png")
        pix.save(out_path)
        extracted_paths["crossing_6280_plan"] = out_path

    # Generate Visual Side-by-Side Comparison Panels
    print("[*] Generating Side-by-Side Visual Comparison Panels...")

    # 1. Detail B Comparison (Alt 10 flat vs Alt 12/13 bent profile)
    create_side_by_side(
        crops_dir,
        "comparison_detail_b.png",
        extracted_paths.get("alt10_detail_b_area"),
        extracted_paths.get("alt13_detail_b_area"),
        "ALT 10 (Oct 2023): Flat Tie Bar (Fouling Risk)",
        "ALT 13 (Jan 2025): Detail 'B' 222mm Drop Bend (Full Clearance)"
    )

    # 2. Alteration History Comparison
    create_side_by_side(
        crops_dir,
        "comparison_alteration_table.png",
        extracted_paths.get("alt10_alteration_table"),
        extracted_paths.get("alt13_alteration_table"),
        "ALT 10 Revision Block (Oct 2023)",
        "ALT 13 Revision Block (Jan 2025 - Alt 11, 12, 13)"
    )

    # 3. Spares Schedule Comparison
    create_side_by_side(
        crops_dir,
        "comparison_spares_schedule.png",
        extracted_paths.get("alt10_spares_list"),
        extracted_paths.get("alt13_spares_list"),
        "ALT 10/12: No Dedicated Spares Schedule",
        "ALT 13: LIST - A Mandating 10% Spares Buffer"
    )

    print("[+] Visual comparison generation completed successfully.")

def create_side_by_side(crops_dir, out_filename, img_path1, img_path2, label1, label2):
    if not img_path1 or not img_path2 or not os.path.exists(img_path1) or not os.path.exists(img_path2):
        return

    im1 = Image.open(img_path1)
    im2 = Image.open(img_path2)

    # Target height
    target_h = 600
    w1 = int(im1.width * (target_h / im1.height))
    w2 = int(im2.width * (target_h / im2.height))

    im1_resized = im1.resize((w1, target_h), Image.Resampling.LANCZOS)
    im2_resized = im2.resize((w2, target_h), Image.Resampling.LANCZOS)

    banner_h = 45
    total_w = w1 + w2 + 30
    total_h = target_h + banner_h + 20

    combined = Image.new("RGB", (total_w, total_h), (18, 24, 36))
    draw = ImageDraw.Draw(combined)

    # Paste images
    combined.paste(im1_resized, (10, banner_h + 10))
    combined.paste(im2_resized, (w1 + 20, banner_h + 10))

    # Draw divider line
    draw.line([(w1 + 15, 10), (w1 + 15, total_h - 10)], fill=(0, 210, 255), width=2)

    # Labels
    draw.rectangle([(10, 10), (w1 + 10, banner_h)], fill=(30, 40, 60))
    draw.text((20, 18), label1, fill=(255, 157, 0))

    draw.rectangle([(w1 + 20, 10), (total_w - 10, banner_h)], fill=(30, 40, 60))
    draw.text((w1 + 30, 18), label2, fill=(0, 255, 136))

    out_path = os.path.join(crops_dir, out_filename)
    combined.save(out_path)
    print(f"    Generated Visual Diff Panel: {out_filename}")

if __name__ == "__main__":
    extract_crops()
