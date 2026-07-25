"""
Prepare a portrait photo for clean ASCII conversion:
  1. boost contrast using PIL's histogram equalization and contrast enhance
  2. apply a vignette mask to fade edges to white so the subject is isolated
  3. composite onto pure white so the background reads as blank
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

# 1. Load image and convert to grayscale
try:
    img = Image.open(INP).convert("L")
except Exception as e:
    print(f"Error: Could not load image from {INP}: {e}", file=sys.stderr)
    sys.exit(1)

# 2. Boost local contrast (histogram equalization + global contrast boost)
img = ImageOps.equalize(img)
img = ImageEnhance.Contrast(img).enhance(1.45)
img = ImageEnhance.Brightness(img).enhance(1.15)

# 3. Create a vignette mask using numpy
w, h = img.size
x = np.linspace(-1.0, 1.0, w)
y = np.linspace(-1.0, 1.0, h)
xx, yy = np.meshgrid(x, y)
dist = np.sqrt(xx**2 + yy**2)

# Vignette: 1.0 in center, drops off to 0.0 at edges
vignette = 1.0 - dist
vignette = np.clip(vignette * 1.5 + 0.1, 0, 1)

# Convert vignette numpy array back to PIL image and apply Gaussian blur to smooth it
vignette_img = Image.fromarray((vignette * 255.0).astype(np.uint8), mode="L")
vignette_img = vignette_img.filter(ImageFilter.GaussianBlur(radius=max(w, h) / 10))

# 4. Composite onto white using the vignette image as mask
bg = Image.new("L", (w, h), 255)
out = Image.composite(img, bg, vignette_img)

out.save(OUT)
print("wrote prepped image to", OUT, out.size)
