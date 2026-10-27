"""
MÔ-ĐUN 3: TẠO HIỆU ỨNG PHÁC THẢO TRANH VẼ - SKETCH ART (DÀNH CHO THÀNH VIÊN 3)
------------------------------------------------------------------------------
File này định nghĩa sẵn các hàm chuẩn để tự động kết nối vào giao diện chính (main_app.py).
Khi Thành viên 3 hoàn thành code (từ anh_am_ban.py, anh_bo_loc.py, sobel.py),
chỉ cần đặt nội dung xử lý vào đúng các hàm bên dưới.
"""

import cv2
import numpy as np


def apply_negative(img: np.ndarray) -> np.ndarray:
    """
    [THÀNH VIÊN 3] Tạo ảnh âm bản (Negative Image) từ anh_am_ban.py.
    Công thức: s = 255 - r
    """
    if img is None:
        return None
    return 255 - img


def apply_pencil_sketch(img: np.ndarray, blur_ksize: int = 21) -> np.ndarray:
    """
    [THÀNH VIÊN 3] Chuyển ảnh thành tranh vẽ chì (Pencil Sketch) bằng phép hòa trộn Color Dodge:
    Bước 1: Chuyển sang ảnh xám (gray).
    Bước 2: Lấy ảnh âm bản (255 - gray).
    Bước 3: Làm mờ ảnh âm bản bằng bộ lọc Gaussian với kích thước mặt nạ lớn.
    Bước 4: Hòa trộn Color Dodge giữa ảnh xám và ảnh âm bản đã làm mờ.
    """
    if img is None:
        return None

    # Bước 1: Chuyển ảnh xám
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Bước 2: Ảnh âm bản
    inv_gray = 255 - gray

    # Bước 3: Làm mờ Gaussian trên ảnh âm bản (đảm bảo ksize là số lẻ)
    k = max(3, int(blur_ksize))
    if k % 2 == 0:
        k += 1
    blurred_inv = cv2.GaussianBlur(inv_gray, (k, k), 0)

    # Bước 4: Hòa trộn lớp (Color Dodge) trích xuất nét chì
    sketch = cv2.divide(gray, 255 - blurred_inv, scale=256.0)
    return sketch


def apply_sobel_sketch(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """
    [THÀNH VIÊN 3] Tạo tranh vẽ nét viền bằng toán tử đạo hàm Sobel (sobel.py):
    Bước 1: Chuyển sang ảnh xám và làm mịn nhẹ bằng Gaussian để khử nhiễu.
    Bước 2: Tính đạo hàm Sobel theo hướng X (Gx) và hướng Y (Gy).
    Bước 3: Tính biên độ Gradient G = sqrt(Gx^2 + Gy^2).
    Bước 4: Đảo ngược màu (255 - G) để có nét vẽ màu đen trên nền giấy trắng.
    """
    if img is None:
        return None

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Đảm bảo ksize hợp lệ cho cv2.Sobel (1, 3, 5, 7)
    k = max(1, min(7, int(ksize)))
    if k % 2 == 0:
        k += 1

    # Làm mịn nhẹ để tránh nhiễu tạo nét giả
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Tính đạo hàm Sobel theo phương X và Y
    sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=k)
    sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=k)

    # Độ lớn biên
    magnitude = cv2.magnitude(sobel_x, sobel_y)
    edges = cv2.convertScaleAbs(magnitude)

    # Đảo màu: Nền trắng (255) - Nét viền đen (0)
    sobel_sketch = 255 - edges
    return sobel_sketch


def pipeline_enhance_denoise_sketch(
    img: np.ndarray,
    gamma: float = 0.5,
    median_ksize: int = 3,
    sketch_ksize: int = 21,
) -> np.ndarray:
    """
    [THÀNH VIÊN 3 - TOÀN] Luồng kết hợp liên hoàn (Pipeline):
    Ảnh thiếu sáng -> Bù sáng Gamma -> Khử nhiễu Median -> Tạo Sketch Art (Color Dodge).
    """
    if img is None:
        return None

    # Bước 1: Tăng sáng bằng Gamma (Mô-đun 1)
    try:
        import module_enhance as mod1
        bright = mod1.apply_gamma_transform(img, gamma=gamma)
    except Exception:
        img_f = img.astype(np.float32) / 255.0
        bright = np.clip(np.power(img_f, max(0.1, gamma)) * 255.0, 0, 255).astype(np.uint8)

    # Bước 2: Khử nhiễu đốm bằng Median (Mô-đun 2)
    try:
        import module_denoise as mod2
        denoised = mod2.apply_median_filter(bright, ksize=median_ksize)
    except Exception:
        k = max(3, int(median_ksize))
        if k % 2 == 0:
            k += 1
        denoised = cv2.medianBlur(bright, k)

    # Bước 3: Tạo tranh phác thảo chì bằng Color Dodge (Mô-đun 3)
    sketch = apply_pencil_sketch(denoised, blur_ksize=sketch_ksize)
    return sketch
