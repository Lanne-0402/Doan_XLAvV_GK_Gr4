"""
module_sketch.py - Hiệu ứng phác thảo tranh vẽ (Sketch Art) & Pipeline kết hợp
Hỗ trợ: Tranh vẽ chì (Color Dodge), Tranh nét viền (Sobel), Luồng kết hợp tự động (Pipeline).
"""

import cv2
import numpy as np


def apply_negative(img: np.ndarray) -> np.ndarray:
    """Tạo ảnh âm bản: s = 255 - r (bước đệm kỹ thuật cho thuật toán Color Dodge)."""
    if img is None:
        return None
    return 255 - img


def apply_pencil_sketch(img: np.ndarray, blur_ksize: int = 21) -> np.ndarray:
    """
    Tạo tranh phác thảo chì mỹ thuật bằng phép hòa trộn Color Dodge:
    1. Chuyển ảnh xám -> 2. Lấy âm bản -> 3. Làm mờ Gaussian -> 4. Hòa trộn Color Dodge.
    """
    if img is None:
        return None

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    inv_gray = 255 - gray

    k = max(3, int(blur_ksize))
    if k % 2 == 0:
        k += 1
    blurred_inv = cv2.GaussianBlur(inv_gray, (k, k), 0)

    sketch = cv2.divide(gray, 255 - blurred_inv, scale=256.0)
    return sketch


def apply_sobel_sketch(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """
    Tạo tranh vẽ nét viền truyện tranh bằng toán tử đạo hàm Sobel:
    Tính Gradient G = sqrt(Gx^2 + Gy^2), đảo ngược thành nét đen trên nền trắng.
    """
    if img is None:
        return None

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    k = max(1, min(7, int(ksize)))
    if k % 2 == 0:
        k += 1

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=k)
    sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=k)

    magnitude = cv2.magnitude(sobel_x, sobel_y)
    edges = cv2.convertScaleAbs(magnitude)

    return 255 - edges


def pipeline_enhance_denoise_sketch(
    img: np.ndarray,
    gamma: float = 0.5,
    median_ksize: int = 3,
    sketch_ksize: int = 21,
    sketch_style: str = "pencil",
) -> np.ndarray:
    """
    Quy trình 1-Chạm tự động:
    1. Tăng sáng Gamma -> 2. Khử khuyết điểm da (Median) -> 3. Chuyển thành Tranh vẽ đã chọn.
    """
    if img is None:
        return None

    try:
        import module_enhance as mod1
        bright = mod1.apply_gamma_transform(img, gamma=gamma)
    except Exception:
        img_f = img.astype(np.float32) / 255.0
        bright = np.clip(np.power(img_f, max(0.1, gamma)) * 255.0, 0, 255).astype(np.uint8)

    try:
        import module_denoise as mod2
        cleaned = mod2.apply_median_filter(bright, ksize=median_ksize)
        smoothed = mod2.apply_bilateral_filter(cleaned, d=9, sigma_color=75.0, sigma_space=75.0)
    except Exception:
        k = max(3, int(median_ksize))
        if k % 2 == 0:
            k += 1
        smoothed = cv2.medianBlur(bright, k)

    if sketch_style == "sobel":
        return apply_sobel_sketch(smoothed, ksize=3)
    return apply_pencil_sketch(smoothed, blur_ksize=sketch_ksize)


def pipeline_custom_stack(
    img: np.ndarray,
    gamma: float | None = None,
    median_ksize: int | None = None,
    bilateral_d: int | None = None,
    sketch_mode: str | None = None,
    sketch_ksize: int = 21,
) -> np.ndarray:
    """Thực thi chuỗi xử lý tùy chọn: Gamma -> Median -> Bilateral -> Sketch."""
    if img is None:
        return None

    curr = img.copy()

    if gamma is not None:
        try:
            import module_enhance as mod1
            curr = mod1.apply_gamma_transform(curr, gamma=gamma)
        except Exception:
            img_f = curr.astype(np.float32) / 255.0
            curr = np.clip(np.power(img_f, max(0.1, gamma)) * 255.0, 0, 255).astype(np.uint8)

    if median_ksize is not None:
        try:
            import module_denoise as mod2
            curr = mod2.apply_median_filter(curr, ksize=median_ksize)
        except Exception:
            k = max(3, int(median_ksize))
            if k % 2 == 0:
                k += 1
            curr = cv2.medianBlur(curr, k)

    if bilateral_d is not None:
        try:
            import module_denoise as mod2
            curr = mod2.apply_bilateral_filter(curr, d=bilateral_d, sigma_color=75, sigma_space=75)
        except Exception:
            curr = cv2.bilateralFilter(curr, d=int(bilateral_d), sigmaColor=75, sigmaSpace=75)

    if sketch_mode == "pencil":
        curr = apply_pencil_sketch(curr, blur_ksize=sketch_ksize)
    elif sketch_mode == "sobel":
        curr = apply_sobel_sketch(curr, ksize=3)

    return curr
