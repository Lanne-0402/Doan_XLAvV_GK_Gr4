"""
MÔ-ĐUN 2: LÀM MỊN & KHỬ NHIỄU BẢO TOÀN BIÊN (DÀNH CHO THÀNH VIÊN 2)
--------------------------------------------------------------------
File này định nghĩa sẵn các hàm chuẩn để tự động kết nối vào giao diện chính (main_app.py).
Khi Thành viên 2 hoàn thành code (từ anh_bo_loc.py), chỉ cần đặt nội dung xử lý
vào đúng tên các hàm bên dưới là giao diện sẽ tự động chạy.
"""

import cv2
import numpy as np


def _ensure_odd_ksize(ksize: int) -> int:
    """Đảm bảo kích thước mặt nạ lọc luôn là số lẻ >= 3."""
    ksize = max(3, int(ksize))
    if ksize % 2 == 0:
        ksize += 1
    return ksize


def apply_mean_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """
    [THÀNH VIÊN 2] Bộ lọc Trung bình (Average / Mean Filter).
    Đầu vào: img (ảnh numpy array), ksize (kích thước mặt nạ lọc).
    Đầu ra: ảnh sau khi làm mịn trung bình.
    """
    if img is None:
        return None
    k = _ensure_odd_ksize(ksize)
    return cv2.blur(img, (k, k))


def apply_gaussian_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """
    [THÀNH VIÊN 2] Bộ lọc Gaussian (Gaussian Filter).
    Đầu vào: img (ảnh numpy array), ksize (kích thước mặt nạ lọc).
    Đầu ra: ảnh sau khi lọc Gaussian.
    """
    if img is None:
        return None
    k = _ensure_odd_ksize(ksize)
    return cv2.GaussianBlur(img, (k, k), 0)


def apply_median_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """
    [THÀNH VIÊN 2] Bộ lọc Trung vị (Median Filter) - chuyên khử nhiễu muối tiêu/đốm mụn nhỏ.
    Đầu vào: img (ảnh numpy array), ksize (kích thước mặt nạ lọc lẻ).
    Đầu ra: ảnh sau khi lọc trung vị.
    """
    if img is None:
        return None
    k = _ensure_odd_ksize(ksize)
    return cv2.medianBlur(img, k)


def apply_bilateral_filter(
    img: np.ndarray, d: int = 9, sigma_color: float = 75.0, sigma_space: float = 75.0
) -> np.ndarray:
    """
    [THÀNH VIÊN 2] Bộ lọc Song phương (Bilateral Filter) - làm mịn da/nền mà vẫn giữ nét biên.
    Đầu vào: img (ảnh numpy array), d (đường kính lân cận), sigma_color, sigma_space.
    Đầu ra: ảnh đã làm mịn da và giữ sắc nét đường viền.
    """
    if img is None:
        return None
    return cv2.bilateralFilter(img, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
