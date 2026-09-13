"""
Font to Single-Stroke Plotter Toolpath Converter
Demonstrates how to convert downloaded TTF handwriting fonts into 1D single-line
trajectories for a CNC Pen Plotter (solving the "hollow outline" problem).
"""

import numpy as np
from PIL import Image, ImageFont, ImageDraw

def zhang_suen_thinning(binary_image: np.ndarray) -> np.ndarray:
    """
    Standard Zhang-Suen morphological thinning algorithm to extract 
    1-pixel wide central skeleton lines from any thick raster font outline.
    """
    skeleton = binary_image.copy().astype(np.uint8)
    h, w = skeleton.shape

    def get_neighbors(x, y):
        # 8-neighbors of (x, y) arranged clockwise starting from P2 (north)
        p2 = skeleton[x-1, y]
        p3 = skeleton[x-1, y+1]
        p4 = skeleton[x, y+1]
        p5 = skeleton[x+1, y+1]
        p6 = skeleton[x+1, y]
        p7 = skeleton[x+1, y-1]
        p8 = skeleton[x, y-1]
        p9 = skeleton[x-1, y-1]
        return [p2, p3, p4, p5, p6, p7, p8, p9]

    changed = True
    while changed:
        changed = False
        # Sub-iteration 1
        to_delete_1 = []
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                if skeleton[r, c] == 1:
                    n = get_neighbors(r, c)
                    B = sum(n) # Number of non-zero neighbors
                    # Number of 0-1 transitions
                    A = sum((n[i] == 0 and n[(i + 1) % 8] == 1) for i in range(8))
                    if 2 <= B <= 6 and A == 1 and (n[0] * n[2] * n[4] == 0) and (n[2] * n[4] * n[6] == 0):
                        to_delete_1.append((r, c))

        if to_delete_1:
            for r, c in to_delete_1:
                skeleton[r, c] = 0
            changed = True

        # Sub-iteration 2
        to_delete_2 = []
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                if skeleton[r, c] == 1:
                    n = get_neighbors(r, c)
                    B = sum(n)
                    A = sum((n[i] == 0 and n[(i + 1) % 8] == 1) for i in range(8))
                    if 2 <= B <= 6 and A == 1 and (n[0] * n[2] * n[6] == 0) and (n[0] * n[4] * n[6] == 0):
                        to_delete_2.append((r, c))

        if to_delete_2:
            for r, c in to_delete_2:
                skeleton[r, c] = 0
            changed = True

    return skeleton

def extract_single_stroke_paths(text: str, font_path: str = "C:/Windows/Fonts/Inkfree.ttf", font_size: int = 64):
    """
    Takes any TTF font, extracts the centerline skeleton, and returns 
    pen-plotter-ready 1-line coordinate paths.
    """
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(text)
    w = max(10, bbox[2] - bbox[0] + 40)
    h = max(10, bbox[3] - bbox[1] + 40)

    # Render thick font glyph
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    draw.text((20 - bbox[0], 20 - bbox[1]), text, font=font, fill=255)

    # Convert to binary numpy array
    arr = (np.array(img) > 128).astype(np.uint8)

    # Extract 1D centerline
    skeleton = zhang_suen_thinning(arr)
    return skeleton

if __name__ == "__main__":
    print("Extracting single-stroke skeleton from TTF handwriting font...")
    skel = extract_single_stroke_paths("Rs 20 lakhs")
    print(f"Extracted skeleton shape: {skel.shape}, total 1-line ink points: {np.sum(skel)}")
    # Save preview image of the skeleton
    skel_img = Image.fromarray((skel * 255).astype(np.uint8))
    skel_img.save("extracted_single_stroke_preview.png")
    print("Saved 'extracted_single_stroke_preview.png' for plotter verification!")
