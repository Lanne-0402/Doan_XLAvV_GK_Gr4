"""Mô-đun 2: Làm mịn và khử nhiễu cho Photo Enhancer & Sketch Tool.

Tương thích trực tiếp với main_app.py: apply_mean_filter,
apply_gaussian_filter, apply_median_filter và apply_bilateral_filter.
Ảnh đầu vào: numpy.ndarray uint8, dạng (H, W) hoặc (H, W, 3) BGR.
Kết quả giữ nguyên kích thước, số kênh và kiểu dữ liệu; không sửa ảnh gốc.
Không đọc/ghi ảnh hay mở giao diện khi import. None được trả lại là None
để tương thích với _get_source_image() của giao diện hiện tại.

Cài thư viện để chạy cùng giao diện: pip install numpy opencv-python pillow
"""

from numbers import Integral, Real

import cv2
import numpy as np

__all__ = [
    "apply_mean_filter", "apply_gaussian_filter",
    "apply_median_filter", "apply_bilateral_filter",
]


def _validate_image(img: np.ndarray) -> np.ndarray:
    """Kiểm tra ảnh, giữ nguyên dữ liệu và chuẩn hóa bố trí bộ nhớ."""
    if not isinstance(img, np.ndarray):
        raise TypeError("Ảnh phải là numpy.ndarray hoặc None.")
    if img.dtype != np.uint8:
        raise TypeError("Ảnh phải có kiểu uint8, mức sáng từ 0 đến 255.")
    if img.ndim not in (2, 3) or (img.ndim == 3 and img.shape[2] != 3):
        raise ValueError("Chỉ hỗ trợ ảnh xám (H, W) hoặc ảnh màu BGR (H, W, 3).")
    if img.size == 0:
        raise ValueError("Ảnh đầu vào không được rỗng.")
    return np.ascontiguousarray(img)


def _ensure_odd_ksize(ksize: int) -> int:
    """Giữ quy ước cũ: tối thiểu 3; số chẵn được tăng lên số lẻ kế tiếp.

    Chấp nhận số nguyên Python/NumPy; từ chối bool, chuỗi và số thực
    để tránh âm thầm cắt phần thập phân. Giao diện dùng 3, 5, ..., 15.
    """
    if isinstance(ksize, (bool, np.bool_)) or not isinstance(ksize, Integral):
        raise TypeError("Kích thước mặt nạ phải là số nguyên.")
    k = max(3, int(ksize))
    return k if k % 2 else k + 1


def _validate_sigma(value: float, name: str, allow_zero: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} phải là số thực hữu hạn.")
    value = float(value)
    if not np.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        condition = ">= 0" if allow_zero else "> 0"
        raise ValueError(f"{name} phải hữu hạn và {condition}.")
    return value


def apply_mean_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Lọc trung bình: mỗi pixel là trung bình trong cửa sổ ksize x ksize.

    Giảm nhiễu nhưng làm mờ cả biên. Biên ảnh dùng BORDER_REFLECT_101.
    """
    if img is None:
        return None
    src = _validate_image(img)
    k = _ensure_odd_ksize(ksize)
    return cv2.blur(src, (k, k), borderType=cv2.BORDER_REFLECT_101)


def apply_gaussian_filter(
    img: np.ndarray, ksize: int = 5, sigma: float = 0.0
) -> np.ndarray:
    """Lọc Gaussian: trung bình có trọng số, trọng số lớn gần tâm.

    sigma=0: OpenCV suy ra độ lệch chuẩn từ ksize. sigma>0: tự điều
    chỉnh độ trải Gaussian theo cả hai trục. Có thể dùng lại cho sketch.
    Biên ảnh dùng BORDER_REFLECT_101; cửa sổ lớn dễ mất chi tiết.
    """
    if img is None:
        return None
    src = _validate_image(img)
    k = _ensure_odd_ksize(ksize)
    sigma = _validate_sigma(sigma, "sigma", allow_zero=True)
    return cv2.GaussianBlur(
        src, (k, k), sigmaX=sigma, sigmaY=sigma,
        borderType=cv2.BORDER_REFLECT_101,
    )


def apply_median_filter(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Lọc trung vị, phù hợp nhiễu muối tiêu và các đốm nhỏ.

    Thực hiện riêng trên từng kênh. Không tự phát hiện mụn hoặc vùng da.
    OpenCV lặp pixel ngoài biên (BORDER_REPLICATE) cho bộ lọc này.
    """
    if img is None:
        return None
    src = _validate_image(img)
    return cv2.medianBlur(src, _ensure_odd_ksize(ksize))


def apply_bilateral_filter(
    img: np.ndarray, d: int = 9,
    sigma_color: float = 75.0, sigma_space: float = 75.0,
) -> np.ndarray:
    """Làm mịn bằng trọng số không gian và độ giống nhau về màu/mức xám.

    d: đường kính vùng lân cận, chuẩn hóa thành số lẻ >=3 như thanh trượt.
    sigma_color: mức chấp nhận chênh lệch màu, theo thang pixel 0..255;
    tăng giá trị này làm các màu khác nhau bị hòa trộn nhiều hơn.
    sigma_space: độ trải trọng số không gian, đơn vị pixel; phạm vi thực
    tế vẫn bị giới hạn bởi d. Cả hai sigma phải hữu hạn và >0.

    Giữ biên tốt hơn các bộ lọc trung bình nhưng không đảm bảo giữ mọi
    chi tiết. Lọc toàn ảnh, không chỉ vùng da. Không tối ưu cho muối tiêu.
    """
    if img is None:
        return None
    src = _validate_image(img)
    diameter = _ensure_odd_ksize(d)
    color = _validate_sigma(sigma_color, "sigma_color")
    space = _validate_sigma(sigma_space, "sigma_space")
    return cv2.bilateralFilter(
        src, d=diameter, sigmaColor=color, sigmaSpace=space,
        borderType=cv2.BORDER_REFLECT_101,
    )
