"""
MÔ-ĐUN 1: TĂNG SÁNG & CẢI THIỆN ĐỘ TƯƠNG PHẢN (THÀNH VIÊN 1)
------------------------------------------------------------
Chuẩn hóa từ các bài thực hành: anh_gray.py, anh_gamma.py, anh_bo_loc.py
Bao gồm các chức năng:
1. Chuyển ảnh màu sang ảnh mức xám (Grayscale)
2. Cân bằng lược đồ xám (Histogram Equalization) cho ảnh xám & ảnh màu
3. Biến đổi Logarit (Log Transform) bù sáng vùng tối
4. Biến đổi Gamma (Power-Law / Gamma Correction)
5. Kéo giãn tương phản tuyến tính (Contrast Stretching)
6. Tính toán và vẽ biểu đồ Histogram so sánh Trước - Sau
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """
    Chuyển đổi ảnh đầu vào sang ảnh mức xám (Grayscale - 1 kênh).
    Nếu ảnh đầu vào đã là ảnh xám thì giữ nguyên.
    """
    if img is None:
        return None
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.copy()


def apply_histogram_eq(img: np.ndarray, keep_color: bool = False) -> np.ndarray:
    """
    Cân bằng lược đồ xám (Histogram Equalization) bằng hàm cv2.equalizeHist.
    - Nếu keep_color = False: Chuyển sang ảnh xám rồi cân bằng (chuẩn theo bài học).
    - Nếu keep_color = True: Chuyển sang không gian YCrCb, chỉ cân bằng kênh độ sáng Y
      để tăng tương phản mà không làm sai lệch màu sắc của ảnh chụp ban đêm (night.jpg).
    """
    if img is None:
        return None

    # Trường hợp ảnh đã là ảnh xám hoặc người dùng chọn xuất ảnh xám
    if len(img.shape) == 2 or not keep_color:
        gray = to_grayscale(img)
        equalized = cv2.equalizeHist(gray)
        return equalized

    # Trường hợp giữ màu cho ảnh BGR 3 kênh
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel, cr, cb = cv2.split(ycrcb)
    y_equalized = cv2.equalizeHist(y_channel)
    merged_ycrcb = cv2.merge((y_equalized, cr, cb))
    result_bgr = cv2.cvtColor(merged_ycrcb, cv2.COLOR_YCrCb2BGR)
    return result_bgr


def apply_log_transform(img: np.ndarray) -> np.ndarray:
    """
    Biến đổi Logarit giúp mở rộng dải mức xám vùng tối (bù sáng ảnh chụp thiếu sáng).
    Công thức: s = c * log(1 + r), với c = 255 / log(1 + max(r))
    """
    if img is None:
        return None

    img_float = img.astype(np.float32)
    max_val = np.max(img_float)
    if max_val <= 0:
        return img.copy()

    c = 255.0 / np.log(1.0 + max_val)
    log_image = c * np.log(1.0 + img_float)
    log_image = np.clip(log_image, 0, 255).astype(np.uint8)
    return log_image


def apply_gamma_transform(img: np.ndarray, gamma: float = 0.5) -> np.ndarray:
    """
    Biến đổi Gamma (Power-Law Transformation).
    Công thức: s = 255 * (r / 255) ^ gamma
    - gamma < 1.0 (ví dụ 0.4 - 0.6): Làm sáng vùng tối (sửa ảnh thiếu sáng/ngược sáng).
    - gamma > 1.0 (ví dụ 1.5 - 2.5): Làm tối ảnh bị cháy sáng.
    - gamma = 1.0: Giữ nguyên ảnh gốc.
    """
    if img is None:
        return None
    if gamma <= 0:
        gamma = 0.1

    # Chuẩn hóa pixel về đoạn [0, 1], lũy thừa gamma rồi đưa về [0, 255]
    img_float = img.astype(np.float32) / 255.0
    gamma_corrected = np.power(img_float, gamma)
    gamma_corrected = np.clip(gamma_corrected * 255.0, 0, 255).astype(np.uint8)
    return gamma_corrected


def apply_contrast_stretching(img: np.ndarray) -> np.ndarray:
    """
    Kéo giãn tương phản tuyến tính (Contrast Stretching).
    Công thức: s = (r - r_min) * (255 / (r_max - r_min))
    """
    if img is None:
        return None

    r_min = float(np.min(img))
    r_max = float(np.max(img))

    if r_max - r_min == 0:
        return img.copy()

    stretched = (img.astype(np.float32) - r_min) * (255.0 / (r_max - r_min))
    stretched = np.clip(stretched, 0, 255).astype(np.uint8)
    return stretched


def compute_histogram(img: np.ndarray) -> np.ndarray:
    """
    Tính biểu đồ tần suất mức xám (Histogram) có 256 mức [0..255] bằng cv2.calcHist.
    """
    gray = to_grayscale(img)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    return hist


def plot_histogram_comparison(
    img_before: np.ndarray,
    img_after: np.ndarray,
    title_after: str = "Ảnh sau tăng sáng & tương phản",
) -> None:
    """
    Hiển thị cửa sổ Matplotlib gồm 4 khung (2x2):
    - (1, 1): Ảnh gốc (Before)
    - (1, 2): Biểu đồ Histogram của ảnh gốc
    - (2, 1): Ảnh sau xử lý (After)
    - (2, 2): Biểu đồ Histogram của ảnh sau xử lý
    """
    if img_before is None or img_after is None:
        return

    hist_before = compute_histogram(img_before)
    hist_after = compute_histogram(img_after)

    plt.figure("So sánh Ảnh & Biểu đồ Histogram Trước - Sau", figsize=(11, 6))

    # 1. Hiển thị Ảnh gốc
    plt.subplot(2, 2, 1)
    if len(img_before.shape) == 2:
        plt.imshow(img_before, cmap="gray")
    else:
        plt.imshow(cv2.cvtColor(img_before, cv2.COLOR_BGR2RGB))
    plt.title("Ảnh gốc (Before)")
    plt.axis("off")

    # 2. Hiển thị Histogram gốc
    plt.subplot(2, 2, 2)
    plt.plot(hist_before, color="black")
    plt.fill_between(range(256), hist_before.flatten(), color="gray", alpha=0.3)
    plt.title("Histogram Ảnh gốc")
    plt.xlabel("Mức xám (0 - 255)")
    plt.ylabel("Số lượng pixel")
    plt.xlim([0, 256])
    plt.grid(True, linestyle="--", alpha=0.5)

    # 3. Hiển thị Ảnh sau xử lý
    plt.subplot(2, 2, 3)
    if len(img_after.shape) == 2:
        plt.imshow(img_after, cmap="gray")
    else:
        plt.imshow(cv2.cvtColor(img_after, cv2.COLOR_BGR2RGB))
    plt.title(title_after)
    plt.axis("off")

    # 4. Hiển thị Histogram sau xử lý
    plt.subplot(2, 2, 4)
    plt.plot(hist_after, color="blue")
    plt.fill_between(range(256), hist_after.flatten(), color="royalblue", alpha=0.3)
    plt.title(f"Histogram ({title_after})")
    plt.xlabel("Mức xám (0 - 255)")
    plt.ylabel("Số lượng pixel")
    plt.xlim([0, 256])
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()


# Chạy kiểm thử độc lập Mô-đun 1 nếu chạy trực tiếp file này
if __name__ == "__main__":
    # Tạo một bức ảnh giả lập thiếu sáng (mức xám tập trung ở vùng tối 10 -> 90)
    h, w = 300, 400
    gradient = np.tile(np.linspace(10, 90, w, dtype=np.uint8), (h, 1))
    sample_dark_img = cv2.merge([gradient, gradient, gradient])
    cv2.circle(sample_dark_img, (200, 150), 70, (80, 110, 120), -1)

    # Áp dụng biến đổi Gamma và Cân bằng Histogram
    gamma_img = apply_gamma_transform(sample_dark_img, gamma=0.45)
    plot_histogram_comparison(sample_dark_img, gamma_img, "Ảnh sau biến đổi Gamma (0.45)")
