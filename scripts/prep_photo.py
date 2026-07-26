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
from rembg import remove

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

# 2. Remove background using rembg
print("removing background...")
cutout = remove(img)

# 3. Crop to isolate face/cap (removes the 20.5% sky at the top)
w, h = cutout.size
y_start = int(0.205 * h)
y_end = int(0.755 * h)
cutout = cutout.crop((0, y_start, w, y_end))

# 4. Extract RGB and Alpha
rgb = np.array(cutout.convert("RGB"))
alpha = np.array(cutout.split()[-1]).astype(np.float32) / 255.0

# 5. Apply soft vertical fade to the bottom 30% of the alpha mask
h_crop, w_crop = alpha.shape
y_indices = np.arange(h_crop)
bottom_fade = np.ones(h_crop, dtype=np.float32)
fade_start = int(h_crop * 0.70)
bottom_fade[fade_start:] = np.clip((h_crop - y_indices[fade_start:]) / (h_crop - fade_start), 0, 1)

# Multiply alpha by the bottom fade
alpha = alpha * bottom_fade[:, np.newaxis]

# Smooth the alpha mask slightly to avoid jagged edges
alpha_img = Image.fromarray((alpha * 255.0).astype(np.uint8), mode="L")
alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(radius=1.5))
alpha = np.array(alpha_img).astype(np.float32) / 255.0

# 6. Convert RGB to grayscale and boost contrast/brightness
gray = Image.fromarray(rgb).convert("L")
gray = ImageOps.equalize(gray)
gray = ImageEnhance.Contrast(gray).enhance(1.5)
gray = ImageEnhance.Brightness(gray).enhance(1.15)
gray_arr = np.array(gray).astype(np.float32)

# 7. Composite onto pure white: out = gray * alpha + 255 * (1 - alpha)
out = gray_arr * alpha + 255.0 * (1.0 - alpha)
out = np.clip(out, 0, 255).astype(np.uint8)

Image.fromarray(out, mode="L").save(OUT)
print("wrote prepped image to", OUT, out.shape)
