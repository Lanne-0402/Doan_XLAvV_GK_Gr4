"""
module_denoise.py - Xử lý làm mịn và khử nhiễu ảnh
Hỗ trợ: Bộ lọc Trung bình (Mean), Gaussian, Trung vị (Median), Song phương (Bilateral),
và hàm kết hợp làm mịn da khử khuyết điểm (Median + Bilateral).
"""

from numbers import Integral, Real
import cv2
import numpy as np

__all__ = [
    "apply_mean_filter",
    "apply_gaussian_filter",
    "apply_median_filter",
    "apply_bilateral_filter",
    "smooth_and_clean_skin",
]


def _validate_image(img: np.ndarray) -> np.ndarray:
    """Kiểm tra tính hợp lệ của mảng ảnh đầu vào."""
    if not isinstance(img, np.ndarray):
        raise TypeError("Ảnh phải là mảng numpy.ndarray.")
    if img.dtype != np.uint8:
        raise TypeError("Ảnh phải có kiểu dữ liệu uint8 [0..255].")
    if img.ndim not in (2, 3) or (img.ndim == 3 and img.shape[2] != 3):
        raise ValueError("Chỉ hỗ trợ ảnh mức xám (H, W) hoặc ảnh màu BGR (H, W, 3).")
    if img.size == 0:
        raise ValueError("Dữ liệu ảnh rỗng.")
    return np.ascontiguousarray(img)


def _ensure_odd_ksize(ksize: int) -> int:
    """Đảm bảo kích thước mặt nạ là số nguyên lẻ >= 3."""
    if isinstance(ksize, (bool, np.bool_)) or not isinstance(ksize, Integral):
        raise TypeError("Kích thước mặt nạ phải là số nguyên.")
    k = max(3, int(ksize))
    return k if k % 2 else k + 1


def _validate_sigma(value: float, name: str, allow_zero: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} phải là số thực.")
    val = float(value)
    if not np.isfinite(val) or val < 0 or (val == 0 and not allow_zero):
        cond = ">= 0" if allow_zero else "> 0"
        raise ValueError(f"{name} phải hữu hạn và {cond}.")
    return val


def apply_mean_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Lọc trung bình (Mean filter): làm mờ đều trong cửa sổ ksize x ksize."""
    if img is None:
        return None
    src = _validate_image(img)
    k = _ensure_odd_ksize(ksize)
    return cv2.blur(src, (k, k), borderType=cv2.BORDER_REFLECT_101)


def apply_gaussian_filter(img: np.ndarray, ksize: int = 5, sigma: float = 0.0) -> np.ndarray:
    """Lọc Gaussian: làm mịn với trọng số phân bố Gauss theo khoảng cách tâm."""
    if img is None:
        return None
    src = _validate_image(img)
    k = _ensure_odd_ksize(ksize)
    sigma = _validate_sigma(sigma, "sigma", allow_zero=True)
    return cv2.GaussianBlur(
        src, (k, k), sigmaX=sigma, sigmaY=sigma, borderType=cv2.BORDER_REFLECT_101
    )


def apply_median_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Lọc trung vị (Median filter): khử nhiễu muối tiêu và đốm hạt nhỏ."""
    if img is None:
        return None
    src = _validate_image(img)
    return cv2.medianBlur(src, _ensure_odd_ksize(ksize))


def apply_bilateral_filter(
    img: np.ndarray,
    d: int = 9,
    sigma_color: float = 75.0,
    sigma_space: float = 75.0,
) -> np.ndarray:
    """Lọc song phương (Bilateral filter): làm mịn da/nền và bảo toàn sắc nét đường biên."""
    if img is None:
        return None
    src = _validate_image(img)
    diameter = _ensure_odd_ksize(d)
    color = _validate_sigma(sigma_color, "sigma_color")
    space = _validate_sigma(sigma_space, "sigma_space")
    return cv2.bilateralFilter(
        src, d=diameter, sigmaColor=color, sigmaSpace=space, borderType=cv2.BORDER_REFLECT_101
    )


def smooth_and_clean_skin(img: np.ndarray, d: int = 9) -> np.ndarray:
    """
    Kết hợp làm mịn da và khử khuyết điểm chuyên dụng:
    Bước 1: Lọc Median ksize=3 khử sạch đốm mụn nhỏ và nhiễu hạt.
    Bước 2: Lọc Bilateral làm mịn kết cấu da mà vẫn bảo toàn sắc nét đường nét mắt, mũi, miệng.
    """
    if img is None:
        return None
    cleaned = apply_median_filter(img, ksize=3)
    smoothed = apply_bilateral_filter(cleaned, d=d, sigma_color=75.0, sigma_space=75.0)
    return smoothed
