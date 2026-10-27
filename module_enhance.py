"""
module_enhance.py - Xử lý tăng sáng và cải thiện tương phản ảnh
Hỗ trợ: Cân bằng Histogram, biến đổi Gamma, biến đổi Logarit, kéo giãn tương phản và trực quan hóa Histogram.
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Chuyển đổi ảnh sang ảnh xám 1 kênh nếu cần."""
    if img is None:
        return None
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.copy()


def apply_histogram_eq(img: np.ndarray, keep_color: bool = False) -> np.ndarray:
    """
    Cân bằng lược đồ xám (Histogram Equalization).
    - keep_color=False: Chuyển về ảnh xám rồi cân bằng.
    - keep_color=True: Cân bằng trên kênh độ sáng Y (không gian YCrCb) để giữ nguyên màu sắc.
    """
    if img is None:
        return None

    if len(img.shape) == 2 or not keep_color:
        gray = to_grayscale(img)
        return cv2.equalizeHist(gray)

    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    y_eq = cv2.equalizeHist(y)
    merged = cv2.merge((y_eq, cr, cb))
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)


def apply_log_transform(img: np.ndarray) -> np.ndarray:
    """Biến đổi Logarit mở rộng mức xám vùng tối: s = c * ln(1 + r)."""
    if img is None:
        return None

    img_float = img.astype(np.float32)
    max_val = np.max(img_float)
    if max_val <= 0:
        return img.copy()

    c = 255.0 / np.log(1.0 + max_val)
    log_image = c * np.log(1.0 + img_float)
    return np.clip(log_image, 0, 255).astype(np.uint8)


def apply_gamma_transform(img: np.ndarray, gamma: float = 0.5) -> np.ndarray:
    """Biến đổi Gamma: s = 255 * (r / 255) ^ gamma (gamma < 1 tăng sáng, gamma > 1 giảm sáng)."""
    if img is None:
        return None
    gamma = max(0.05, float(gamma))

    img_float = img.astype(np.float32) / 255.0
    gamma_corrected = np.power(img_float, gamma)
    return np.clip(gamma_corrected * 255.0, 0, 255).astype(np.uint8)


def apply_contrast_stretching(img: np.ndarray) -> np.ndarray:
    """Kéo giãn tương phản tuyến tính mức xám [r_min, r_max] về [0, 255]."""
    if img is None:
        return None

    r_min = float(np.min(img))
    r_max = float(np.max(img))
    if r_max - r_min == 0:
        return img.copy()

    stretched = (img.astype(np.float32) - r_min) * (255.0 / (r_max - r_min))
    return np.clip(stretched, 0, 255).astype(np.uint8)


def compute_histogram(img: np.ndarray) -> np.ndarray:
    """Tính toán biểu đồ tần suất mức xám 256 mức."""
    gray = to_grayscale(img)
    return cv2.calcHist([gray], [0], None, [256], [0, 256])


def plot_histogram_comparison(
    img_before: np.ndarray,
    img_after: np.ndarray,
    title_after: str = "Ảnh sau xử lý",
) -> None:
    """Hiển thị cửa sổ 2x2 so sánh ảnh và biểu đồ Histogram Trước - Sau."""
    if img_before is None or img_after is None:
        return

    hist_before = compute_histogram(img_before)
    hist_after = compute_histogram(img_after)

    plt.figure("So sánh Ảnh & Biểu đồ Histogram Trước - Sau", figsize=(10, 6))

    plt.subplot(2, 2, 1)
    if len(img_before.shape) == 2:
        plt.imshow(img_before, cmap="gray")
    else:
        plt.imshow(cv2.cvtColor(img_before, cv2.COLOR_BGR2RGB))
    plt.title("Ảnh gốc (Before)")
    plt.axis("off")

    plt.subplot(2, 2, 2)
    plt.plot(hist_before, color="black")
    plt.fill_between(range(256), hist_before.flatten(), color="gray", alpha=0.3)
    plt.title("Histogram Ảnh gốc")
    plt.xlim([0, 256])
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.subplot(2, 2, 3)
    if len(img_after.shape) == 2:
        plt.imshow(img_after, cmap="gray")
    else:
        plt.imshow(cv2.cvtColor(img_after, cv2.COLOR_BGR2RGB))
    plt.title(title_after)
    plt.axis("off")

    plt.subplot(2, 2, 4)
    plt.plot(hist_after, color="blue")
    plt.fill_between(range(256), hist_after.flatten(), color="royalblue", alpha=0.3)
    plt.title(f"Histogram ({title_after})")
    plt.xlim([0, 256])
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()
