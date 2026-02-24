import os
from PIL import Image

gallery_path = "static/gallery"

print("Scanning images...")

for filename in os.listdir(gallery_path):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        filepath = os.path.join(gallery_path, filename)

        img = Image.open(filepath)

        # Convert PNG to JPEG for better compression
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(filepath, optimize=True, quality=70)

        print(f"✓ Compressed {filename}")

print("Done!")
