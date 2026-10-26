# Photo Enhancer & Sketch Tool - Đồ án Giữa kỳ Xử lý ảnh và Video (Nhóm 4)

Công cụ xử lý ảnh nhanh: Tăng sáng & cải thiện tương phản cho ảnh chụp thiếu sáng/ngược sáng, khử nhiễu & làm mịn da bảo toàn biên, và chuyển ảnh chụp thành tranh vẽ phác thảo nghệ thuật (Sketch Art).

## 1. Cấu trúc thư mục dự án

```text
Doan_XLAvV_GK_Gr4/
├── main_app.py         # Giao diện chính hiển thị Trước - Sau & tích hợp 3 mô-đun (Thành viên 1)
├── module_enhance.py   # Mô-đun 1: Tăng sáng, Cân bằng Histogram, Log, Gamma, Vẽ Histogram (Thành viên 1)
├── module_denoise.py   # Mô-đun 2: Làm mịn & Khử nhiễu Mean, Gaussian, Median, Bilateral (Thành viên 2)
├── module_sketch.py    # Mô-đun 3: Ảnh âm bản, Pencil Sketch (Color Dodge), Sobel Sketch (Thành viên 3)
└── README.md           # Hướng dẫn sử dụng & ghép nối code cho nhóm
```

## 2. Cách chạy chương trình

Mở Terminal / PowerShell tại thư mục `Doan_XLAvV_GK_Gr4` và chạy lệnh:

```bash
python main_app.py
```

## 3. Hướng dẫn ghép code cho HÂN và TOÀN

Giao diện `main_app.py` đã được thiết kế sẵn các nút bấm và thanh trượt tham số cho cả 3 mô-đun:

- **HÂN** chỉ cần viết hoặc chỉnh sửa nội dung các hàm trong [`module_denoise.py`](module_denoise.py):
  - `apply_mean_filter(img, ksize=5)`
  - `apply_gaussian_filter(img, ksize=5)`
  - `apply_median_filter(img, ksize=5)`
  - `apply_bilateral_filter(img, d=9, sigma_color=75, sigma_space=75)`

- **TOÀN** chỉ cần viết hoặc chỉnh sửa nội dung các hàm trong [`module_sketch.py`](module_sketch.py):
  - `apply_negative(img)`
  - `apply_pencil_sketch(img, blur_ksize=21)`
  - `apply_sobel_sketch(img, ksize=3)`
