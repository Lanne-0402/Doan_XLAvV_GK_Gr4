"""Tạo lại bộ ảnh thử từ clean/{astronaut,camera,coffee}.png, không cần mạng.

Chạy: python denoise_images/prepare_dataset.py
Phụ thuộc: numpy, Pillow. Seed=42; kết quả lưu PNG không mất dữ liệu.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent


def main():
    rng = np.random.default_rng(42)
    records = []
    for folder in ("clean", "noisy", "exposure"):
        (ROOT / folder).mkdir(exist_ok=True)

    def read(name):
        return np.asarray(Image.open(ROOT / "clean" / name)).copy()

    def save(relative, arr):
        Image.fromarray(arr).save(ROOT / relative)

    def gaussian(arr, sigma=20):
        return np.rint(np.clip(arr.astype(float) + rng.normal(0, sigma, arr.shape), 0, 255)).astype(np.uint8)

    def impulse(arr, amount=.04):
        out = arr.copy()
        mask = rng.random(arr.shape[:2])
        out[mask < amount / 2] = 0
        out[mask >= 1 - amount / 2] = 255
        return out

    def record(path, reference, category, parameters):
        records.append(dict(path=path, reference=reference, category=category, parameters=parameters))

    portrait = np.asarray(Image.fromarray(read('astronaut.png')).crop((165, 55, 285, 180)).resize((480, 500), Image.Resampling.LANCZOS))
    save('clean/portrait.png', portrait)
    edges = np.full((480, 640, 3), 180, np.uint8)
    edges[:, :320] = 50
    edge_image = Image.fromarray(edges)
    draw = ImageDraw.Draw(edge_image)
    draw.rectangle((50, 60, 220, 200), fill=(230, 150, 70))
    draw.ellipse((390, 70, 570, 250), fill=(30, 80, 210))
    draw.text((40, 320), 'EDGE TEST 0123456789', fill='white', stroke_width=1)
    for x in range(40, 600, 12):
        draw.line((x, 380, x, 440), fill='white', width=2)
    save('clean/edges.png', np.asarray(edge_image))

    for name in ['astronaut', 'camera', 'coffee', 'portrait', 'edges']:
        arr = read(name + '.png')
        record(f'clean/{name}.png', None, 'clean', {})
        save(f'noisy/{name}_gaussian20.png', gaussian(arr))
        record(f'noisy/{name}_gaussian20.png', f'clean/{name}.png', 'gaussian', {'sigma': 20})
        save(f'noisy/{name}_salt_pepper04.png', impulse(arr))
        record(f'noisy/{name}_salt_pepper04.png', f'clean/{name}.png', 'salt_pepper', {'probability': .04})

    save('noisy/portrait_mixed.png', impulse(gaussian(portrait, 12), .02))
    record('noisy/portrait_mixed.png', 'clean/portrait.png', 'mixed', {'sigma': 12, 'probability': .02})
    # Các đốm nhân tạo chỉ minh họa mất chi tiết nhỏ, không phải ảnh bệnh da.
    marked = Image.fromarray(portrait)
    draw = ImageDraw.Draw(marked)
    for x, y, r in [(140, 290, 3), (160, 310, 4), (320, 295, 3), (300, 330, 4), (245, 120, 3)]:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(150, 65, 65))
    save('noisy/portrait_simulated_spots.png', np.asarray(marked))
    record('noisy/portrait_simulated_spots.png', 'clean/portrait.png', 'simulated_spots', {'note': 'Artificial red dots; not real acne'})

    scene = read('coffee.png')
    night = np.rint((scene.astype(float) / 255) ** 2.2 * 255).astype(np.uint8)
    save('exposure/night.png', night)
    record('exposure/night.png', None, 'simulated_low_light', {'gamma': 2.2})
    save('exposure/night_gaussian12.png', gaussian(night, 12))
    record('exposure/night_gaussian12.png', 'exposure/night.png', 'gaussian_low_light', {'sigma': 12})

    scene = read('astronaut.png')
    yy, xx = np.mgrid[:scene.shape[0], :scene.shape[1]]
    shadow = np.exp(-(((xx-225)/105)**2 + ((yy-170)/160)**2) / 2)
    factor = 1.15 - .95 * shadow[..., None]
    backlit = np.rint(np.clip(scene.astype(float) * factor, 0, 255)).astype(np.uint8)
    save('exposure/backlit.png', backlit)
    record('exposure/backlit.png', None, 'simulated_backlit', {'note': 'Spatial brightness mask; not a real backlit capture'})
    save('exposure/backlit_gaussian12.png', gaussian(backlit, 12))
    record('exposure/backlit_gaussian12.png', 'exposure/backlit.png', 'gaussian_backlit', {'sigma': 12})

    for rec in records:
        path = ROOT / rec['path']
        rec['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        rec['shape'] = list(np.asarray(Image.open(path)).shape)
    (ROOT / 'manifest.json').write_text(json.dumps({'seed': 42, 'images': records}, indent=2, ensure_ascii=False), encoding='utf-8')
    tiles = []
    for rec in records:
        im = Image.open(ROOT / rec['path']).convert('RGB')
        tile = Image.new('RGB', (270, 235), '#eef2f6')
        tile.paste(ImageOps.contain(im, (260, 195)), (5, 5))
        ImageDraw.Draw(tile).text((5, 205), rec['path'], fill='black')
        tiles.append(tile)
    sheet = Image.new('RGB', (270*4, 235*((len(tiles)+3)//4)), 'white')
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i%4)*270, (i//4)*235))
    sheet.save(ROOT / 'dataset_overview.jpg', quality=90)
    print(f'Prepared {len(records)} images, seed=42.')


if __name__ == '__main__':
    main()
