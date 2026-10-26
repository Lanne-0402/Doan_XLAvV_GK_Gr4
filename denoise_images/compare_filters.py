"""So sánh bốn bộ lọc với ảnh tham chiếu; không mở GUI.

Từ thư mục chứa main_app.py: python denoise_images/compare_filters.py
Thử nhiều mặt nạ: python denoise_images/compare_filters.py --sizes 3 5 9
Thêm --save-images để xuất từng ảnh kết quả (mặc định chỉ CSV và ảnh so sánh).
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import module_denoise as mod


def read(path):
    # Giữ ảnh xám/BGR; hỗ trợ đường dẫn tiếng Việt trên Windows.
    img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f'Không đọc được ảnh: {path}')
    return img


def metrics(reference, image):
    mse = float(np.mean((reference.astype(np.float64) - image.astype(np.float64))**2))
    psnr = float('inf') if mse == 0 else 10*np.log10(255**2/mse)
    return mse, psnr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', nargs='+', type=int, default=[5])
    parser.add_argument('--save-images', action='store_true')
    args = parser.parse_args()
    if any(k < 3 or k % 2 == 0 for k in args.sizes):
        parser.error('Các kích thước phải lẻ và >=3.')
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    rows = []
    for rec in manifest['images']:
        if rec['reference'] is None:
            continue
        src, ref = read(ROOT/rec['path']), read(ROOT/rec['reference'])
        base_mse, base_psnr = metrics(ref, src)
        name = Path(rec['path']).stem
        for k in args.sizes:
            variants = [('reference', ref), ('input', src)]
            filters = {
                'mean': lambda: mod.apply_mean_filter(src, ksize=k),
                'gaussian': lambda: mod.apply_gaussian_filter(src, ksize=k),
                'median': lambda: mod.apply_median_filter(src, ksize=k),
                'bilateral': lambda: mod.apply_bilateral_filter(src, d=k, sigma_color=75, sigma_space=75),
            }
            for method, function in filters.items():
                # Warm-up rồi lấy trung vị 3 lần; chỉ đo xử lý, không tính I/O.
                function()
                times = []
                for _ in range(3):
                    start = perf_counter()
                    result = function()
                    times.append((perf_counter()-start)*1000)
                mse, psnr = metrics(ref, result)
                rows.append(dict(image=rec['path'], reference=rec['reference'], category=rec['category'], method=method, ksize=k, sigma_color=75 if method=='bilateral' else '', sigma_space=75 if method=='bilateral' else '', input_mse=base_mse, input_psnr_db=base_psnr, output_mse=mse, output_psnr_db=psnr, psnr_gain_db=psnr-base_psnr, median_ms=float(np.median(times))))
                variants.append((method, result))
                if args.save_images:
                    success, encoded = cv2.imencode('.png', result)
                    if not success:
                        raise RuntimeError('Mã hóa PNG thất bại')
                    encoded.tofile(output/f'{name}_{method}_k{k}.png')
            # Hai ảnh đối chiếu đại diện: chân dung và nhiễu muối tiêu.
            if name in ['portrait_gaussian20', 'camera_salt_pepper04']:
                sheet = Image.new('RGB', (960, 720), 'white')
                for i, (label, arr) in enumerate(variants):
                    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB) if arr.ndim==3 else arr
                    tile = ImageOps.contain(Image.fromarray(rgb).convert('RGB'), (310, 320))
                    x, y = (i%3)*320, (i//3)*360
                    sheet.paste(tile, (x, y+30))
                    ImageDraw.Draw(sheet).text((x+5, y+8), f'{label} | k={k}', fill='black')
                sheet.save(output/f'{name}_comparison_k{k}.jpg', quality=95)
    with (output/'metrics.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output/'environment.json').write_text(json.dumps({'opencv': cv2.__version__, 'numpy': np.__version__, 'sizes': args.sizes, 'timing': 'median of 3 runs after warmup, I/O excluded'}, indent=2), encoding='utf-8')
    print(f'Exported {len(rows)} measurements to {output / "metrics.csv"}')


if __name__ == '__main__':
    main()
