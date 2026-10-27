"""
Kiểm thử tự động toàn bộ chương trình (Nhiệm vụ của Toàn - Thành viên 3).
Chạy: py -3.10 test_all.py
"""

import sys
import numpy as np
import cv2
import module_enhance as mod1
import module_denoise as mod2
import module_sketch as mod3

# Tranh loi encode console tren Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def run_checks():
    # Tạo dữ liệu test
    dummy_bgr = np.random.randint(0, 256, (100, 120, 3), dtype=np.uint8)
    dummy_gray = np.random.randint(0, 256, (100, 120), dtype=np.uint8)

    print("[1/4] Kiểm tra Mô-đun 1 (Tăng sáng & Tương phản)...")
    assert mod1.to_grayscale(dummy_bgr).ndim == 2, "to_grayscale lỗi kênh"
    assert mod1.to_grayscale(dummy_gray).ndim == 2, "to_grayscale ảnh xám lỗi"
    assert mod1.apply_histogram_eq(dummy_bgr, keep_color=False).ndim == 2
    assert mod1.apply_histogram_eq(dummy_bgr, keep_color=True).shape == dummy_bgr.shape
    assert mod1.apply_log_transform(dummy_bgr).shape == dummy_bgr.shape
    assert mod1.apply_gamma_transform(dummy_bgr, gamma=0.5).shape == dummy_bgr.shape
    assert mod1.apply_contrast_stretching(dummy_bgr).shape == dummy_bgr.shape
    assert mod1.to_grayscale(None) is None, "None input không trả về None"
    print(" -> Mô-đun 1 OK.")

    print("[2/4] Kiểm tra Mô-đun 2 (Làm mịn & Khử nhiễu)...")
    for k in [3, 4, 5]:  # Test cả ksize chẵn và lẻ
        assert mod2.apply_mean_filter(dummy_bgr, ksize=k).shape == dummy_bgr.shape
        assert mod2.apply_gaussian_filter(dummy_bgr, ksize=k).shape == dummy_bgr.shape
        assert mod2.apply_median_filter(dummy_bgr, ksize=k).shape == dummy_bgr.shape
    assert mod2.apply_bilateral_filter(dummy_bgr, d=5).shape == dummy_bgr.shape
    assert mod2.apply_mean_filter(None) is None
    print(" -> Mô-đun 2 OK.")

    print("[3/4] Kiểm tra Mô-đun 3 (Hiệu ứng Sketch Art của Toàn)...")
    # Test âm bản
    assert mod3.apply_negative(dummy_bgr).shape == dummy_bgr.shape
    assert mod3.apply_negative(dummy_gray).shape == dummy_gray.shape
    # Test tranh chì Color Dodge
    res_pencil_bgr = mod3.apply_pencil_sketch(dummy_bgr, blur_ksize=21)
    res_pencil_gray = mod3.apply_pencil_sketch(dummy_gray, blur_ksize=20)  # chẵn test auto-fix
    assert res_pencil_bgr.ndim == 2, "Tranh chì phải là ảnh 1 kênh"
    assert res_pencil_gray.ndim == 2
    # Test tranh nét viền Sobel
    res_sobel_bgr = mod3.apply_sobel_sketch(dummy_bgr, ksize=3)
    res_sobel_even = mod3.apply_sobel_sketch(dummy_bgr, ksize=4)  # chẵn test auto-fix
    assert res_sobel_bgr.ndim == 2
    assert res_sobel_even.ndim == 2
    assert mod3.apply_pencil_sketch(None) is None
    assert mod3.apply_sobel_sketch(None) is None
    print(" -> Mô-đun 3 OK.")

    print("[4/4] Kiểm tra Pipeline liên hoàn & Đè nhiều hiệu ứng...")
    pipeline_res = mod3.pipeline_enhance_denoise_sketch(
        dummy_bgr, gamma=0.5, median_ksize=3, sketch_ksize=21
    )
    assert pipeline_res is not None
    assert pipeline_res.ndim == 2
    assert mod3.pipeline_enhance_denoise_sketch(None) is None

    # Test Custom Stack Pipeline
    custom_res = mod3.pipeline_custom_stack(
        dummy_bgr, gamma=0.5, median_ksize=3, bilateral_d=5, sketch_mode="pencil", sketch_ksize=21
    )
    assert custom_res is not None
    assert custom_res.ndim == 2
    assert mod3.pipeline_custom_stack(None) is None
    print(" -> Pipeline OK.")

    print("\n>>> TẤT CẢ TEST ĐÃ VƯỢT QUA KHÔNG CÓ LỖI (PASS 100%) <<<")


if __name__ == "__main__":
    run_checks()
