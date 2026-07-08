#!/usr/bin/env python3
"""Optimize all images in content/ directory for web."""

import os
import sys
from pathlib import Path
from PIL import Image

CONTENT_DIR = Path(__file__).parent.parent / "content"
MAX_DIMENSION = 1920
QUALITY = 82
THRESHOLD = 500 * 1024  # 500KB

extensions = (".jpg", ".jpeg", ".png")
total_saved = 0
total_files = 0
converted_webp = 0

def optimize_image(filepath: Path) -> int:
    """Optimize a single image. Returns bytes saved."""
    global total_files, converted_webp
    total_files += 1
    
    original_size = filepath.stat().st_size
    if original_size < THRESHOLD:
        return 0
    
    try:
        img = Image.open(filepath)
        img = img.convert("RGB") if img.mode in ("RGBA", "P") else img
        
        # Resize if larger than MAX_DIMENSION
        w, h = img.size
        if max(w, h) > MAX_DIMENSION:
            ratio = MAX_DIMENSION / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save as optimized JPEG
        if filepath.suffix.lower() in (".jpg", ".jpeg"):
            img.save(filepath, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        elif filepath.suffix.lower() == ".png":
            # Convert PNG to JPEG if it has no transparency
            if img.mode == "RGB":
                filepath = filepath.with_suffix(".jpg")
                img.save(filepath, "JPEG", quality=QUALITY, optimize=True, progressive=True)
            else:
                img.save(filepath, "PNG", optimize=True)
        
        # Also create WebP version
        webp_path = filepath.with_suffix(".webp")
        img.save(webp_path, "WEBP", quality=QUALITY)
        
        new_size = filepath.stat().st_size
        saved = original_size - new_size
        converted_webp += 1
        
        if saved > 0:
            print(f"  ✅ {filepath.name}: {original_size//1024}KB → {new_size//1024}KB (webp: {webp_path.exists()})")
        
        return max(saved, 0)
    
    except Exception as e:
        print(f"  ❌ {filepath.name}: {e}")
        return 0

def main():
    global total_saved
    
    print("🔍 Scanning for images...")
    image_files = []
    for ext in extensions:
        image_files.extend(CONTENT_DIR.rglob(f"*{ext}"))
    
    print(f"📸 Found {len(image_files)} images to check")
    print(f"⚙️  Resizing to max {MAX_DIMENSION}px, quality {QUALITY}%\n")
    
    large_files = [f for f in image_files if f.stat().st_size >= THRESHOLD]
    print(f"📦 {len(large_files)} images over {THRESHOLD//1024}KB need optimization\n")
    
    for i, fp in enumerate(large_files, 1):
        rel = fp.relative_to(CONTENT_DIR.parent)
        print(f"[{i}/{len(large_files)}] {rel}")
        saved = optimize_image(fp)
        total_saved += saved
    
    # Summary
    mb_saved = total_saved / (1024 * 1024)
    print(f"\n{'='*50}")
    print(f"✅ Optimization complete!")
    print(f"   Files processed: {total_files}")
    print(f"   WebP versions created: {converted_webp}")
    print(f"   Space saved: {mb_saved:.1f} MB")
    print(f"{'='*50}")
    print(f"\n⚠️  Note: Two very large PNGs (21.9MB each) require special handling:")
    print(f"   - content/services/landscape/featured.png")
    print(f"   - content/project/cultural/cheshme/featured.png")
    print(f"   If they weren't optimized, run: cwebp -q 80 <file> -o <file>.webp")

if __name__ == "__main__":
    main()
