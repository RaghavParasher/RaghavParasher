"""
Prepare a portrait photo for clean ASCII conversion:
  1. crop the image to isolate the head, cap, and shoulders
  2. boost contrast using PIL's histogram equalization and contrast enhance
  3. apply a vignette mask to fade edges to white so the subject is isolated
  4. composite onto pure white so the background reads as blank
     (white -> spaces in the ascii ramp)

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
"""
import os
import sys

from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

# 1. Load image
try:
    img = Image.open(INP)
except Exception as e:
    print(f"Error: Could not load image from {INP}: {e}", file=sys.stderr)
    sys.exit(1)

# Rotate based on EXIF tag if present
img = ImageOps.exif_transpose(img)
w, h = img.size

# 2. Crop to isolate face/cap (removes the 20% sky at the top)
y_start = int(0.205 * h)
y_end = int(0.755 * h)
img = img.crop((0, y_start, w, y_end)).convert("L")

# 3. Boost local contrast (histogram equalization + global contrast boost)
img = ImageOps.equalize(img)
img = ImageEnhance.Contrast(img).enhance(1.45)
img = ImageEnhance.Brightness(img).enhance(1.15)

# 4. Create a vignette mask (fade sides and bottom only to keep the cap fully visible)
w_crop, h_crop = img.size
x = np.linspace(-1.0, 1.0, w_crop)
y = np.linspace(-1.0, 1.0, h_crop)
xx, yy = np.meshgrid(x, y)

# Fade left/right sides: keep central 44% visible, fade outer 28% on each side
fade_x = np.clip((1.0 - np.abs(xx)) * 1.8, 0, 1)

# Fade bottom only: keep top 60% visible, fade bottom 40%
fade_y = np.clip((1.0 - yy) * 1.4, 0, 1)

# Combine fades
vignette = fade_x * fade_y
vignette = np.clip(vignette, 0, 1)

# Convert vignette numpy array back to PIL image and apply Gaussian blur to smooth it
vignette_img = Image.fromarray((vignette * 255.0).astype(np.uint8), mode="L")
vignette_img = vignette_img.filter(ImageFilter.GaussianBlur(radius=w_crop / 20))

# 5. Composite onto white using the vignette image as mask
bg = Image.new("L", (w_crop, h_crop), 255)
out = Image.composite(img, bg, vignette_img)

out.save(OUT)
print("wrote prepped image to", OUT, out.size)
