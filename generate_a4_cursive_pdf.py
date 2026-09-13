"""
A4 Plain Sheet Generator (Segoe Script - Fluid Connected Cursive Notes)
Generates high-resolution (300 DPI) standard A4 PDF and PNG without lines.
"""

import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_a4_cursive_document(
    output_png="A4_handwritten_cursive_assignment.png",
    output_pdf="A4_handwritten_cursive_assignment.pdf",
    font_path="C:/Windows/Fonts/segoesc.ttf"
):
    random.seed(42)

    # Standard A4 Dimensions at 300 DPI (Print-Ready)
    # 210 mm x 297 mm -> 2480 x 3508 pixels
    width = 2480
    height = 3508
    dpi = 300

    # Layout Parameters (Scaled for 300 DPI)
    # Standard 8.5mm line spacing on A4 = 8.5 / 25.4 * 300 ~ 100 pixels
    line_spacing = 100
    margin_top = 280
    margin_left = 320
    font_size = 46  # Scaled for 300 DPI (~12pt physical handwritten look)

    # Clean plain white paper with subtle natural warmth (#fcfbfa)
    img = Image.new("RGBA", (width, height), (252, 251, 248, 255))

    font_main = ImageFont.truetype(font_path, font_size)
    font_header = ImageFont.truetype(font_path, int(font_size * 1.25))
    font_small = ImageFont.truetype(font_path, int(font_size * 0.85))

    # Rich royal blue ballpoint pen ink with realistic depth
    base_ink_blue = (22, 58, 128)

    def render_handwritten_line(text, start_x, baseline_y, font=font_main, ink_color=base_ink_blue):
        """
        Renders cursive text with per-word and per-character micro-adjustments
        to maintain natural baseline drift, spacing variations, and ballpoint pressure.
        """
        cur_x = start_x
        words = text.split(" ")
        for w_idx, word in enumerate(words):
            # Per-word natural baseline wander
            word_jitter_y = random.uniform(-2.5, 2.5)
            
            for c_idx, char in enumerate(word):
                # Subtle micro-jitter per character
                char_jitter_y = word_jitter_y + random.uniform(-1.0, 1.0)
                char_rot = random.uniform(-1.2, 1.2)

                # Micro ink-pressure variation
                alpha_var = random.randint(-15, 15)
                char_color = (
                    max(10, min(255, ink_color[0] + alpha_var)),
                    max(20, min(255, ink_color[1] + alpha_var)),
                    max(60, min(255, ink_color[2] + alpha_var)),
                    245
                )

                bbox = font.getbbox(char)
                cw = bbox[2] - bbox[0]
                ch = bbox[3] - bbox[1]

                pad = 16
                char_img = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
                char_draw = ImageDraw.Draw(char_img)
                char_draw.text((pad - bbox[0], pad - bbox[1]), char, font=font, fill=char_color)

                if abs(char_rot) > 0.1:
                    char_img = char_img.rotate(char_rot, resample=Image.BICUBIC, expand=True)

                target_x = int(cur_x)
                target_y = int(baseline_y - ch + char_jitter_y - bbox[1])

                img.paste(char_img, (target_x, target_y), char_img)
                
                # Advance cursor (Segoe Script has natural cursive connectors)
                cur_x += cw - 1.5 + random.uniform(-0.4, 0.4)

            # Space between words
            cur_x += font_size * random.uniform(0.38, 0.52)

    # 1. Top Header
    header_y = margin_top - line_spacing
    render_handwritten_line("CMSP", 120, header_y + 60, font=font_main, ink_color=(30, 50, 95))
    render_handwritten_line("Optimization  Problem  Set  -  1  .", 620, header_y + 60, font=font_header, ink_color=(20, 55, 125))

    # 2. Sub-headers
    y1 = margin_top
    render_handwritten_line("1st 3 -> LPP formulation", 850, y1 + 35, font=font_small)
    render_handwritten_line("4th - 10th -> Graphical method .", 1480, y1 + 35, font=font_small)

    # 3. Question 1 Heading & Statement
    y2 = margin_top + line_spacing * 2
    render_handwritten_line("Q 1 )", 150, y2 + 65, font=font_main)
    render_handwritten_line("investment  available   =   Rs  20  lakhs  .", margin_left + 80, y2 + 65, font=font_main)

    # 4. Returns :-
    y3 = y2 + line_spacing * 2
    render_handwritten_line("Returns  :  -", margin_left + 40, y3 + 65, font=font_main)

    # 5. Schemes 1, 2, 3
    y4 = y3 + line_spacing
    render_handwritten_line("Scheme  1   =   10  %  .", margin_left + 80, y4 + 65, font=font_main)

    y5 = y4 + line_spacing
    render_handwritten_line("Scheme  2   =   12  %  .", margin_left + 80, y5 + 65, font=font_main)

    y6 = y5 + line_spacing
    render_handwritten_line("Scheme  3   =   15  %  .", margin_left + 80, y6 + 65, font=font_main)

    # 6. Maximum Investment Condition
    y7 = y6 + line_spacing * 2
    render_handwritten_line("Scheme  3   accepts   maximum   Rs  10  lakhs  .", margin_left + 40, y7 + 65, font=font_main)

    # 7. Risk per lakh
    y8 = y7 + line_spacing * 2
    render_handwritten_line("Risk   per   lakh", margin_left + 40, y8 + 65, font=font_main)

    # 8. Risk Values
    y9 = y8 + line_spacing
    render_handwritten_line("Scheme  1   =   0", margin_left + 80, y9 + 65, font=font_main)

    y10 = y9 + line_spacing
    render_handwritten_line("Scheme  2   =   10", margin_left + 80, y10 + 65, font=font_main)

    y11 = y10 + line_spacing
    render_handwritten_line("Scheme  3   =   20", margin_left + 80, y11 + 65, font=font_main)

    # 9. Maximum Risk Limit
    y12 = y11 + line_spacing * 2
    render_handwritten_line("maximum   Risk   =   500   units  .", margin_left + 40, y12 + 65, font=font_main)

    # Convert to RGB and apply subtle microscopic paper smoothing
    rgb_img = Image.new("RGB", (width, height), (252, 251, 248))
    rgb_img.paste(img, (0, 0), img)

    # Save 300 DPI high-resolution PNG
    rgb_img.save(output_png, "PNG", dpi=(dpi, dpi), quality=95)
    
    # Save standard A4 PDF at 300 DPI
    rgb_img.save(output_pdf, "PDF", resolution=float(dpi))
    
    print(f"Generated 300 DPI A4 Image: {output_png} ({width}x{height} px)")
    print(f"Generated Standard A4 PDF: {output_pdf}")

if __name__ == "__main__":
    generate_a4_cursive_document()
