# Photo Enhancer & Sketch Tool - Đồ án Giữa kỳ Xử lý ảnh và Video (Nhóm 4)

Công cụ xử lý ảnh nhanh: Tăng sáng & cải thiện tương phản cho ảnh chụp thiếu sáng/ngược sáng, khử khuyết điểm & làm mịn da bảo toàn biên, và chuyển ảnh chụp thành tranh vẽ phác thảo nghệ thuật (Sketch Art).

## 1. Cấu trúc thư mục dự án

```text
Doan_XLAvV_GK_Gr4/
├── main_app.py         # Giao diện chính quy trình chuẩn 3 bước & hiển thị Trước - Sau
├── module_enhance.py   # Mô-đun 1: Tăng sáng Gamma, Cân bằng Histogram YCrCb, Biến đổi Log, Trực quan hóa Histogram
├── module_denoise.py   # Mô-đun 2: Làm mịn da & Tẩy khuyết điểm (Bilateral + Median)
├── module_sketch.py    # Mô-đun 3: Tranh chì Color Dodge, Tranh nét viền Sobel & Pipeline 1-Chạm
├── test_all.py         # Bộ kiểm thử tự động toàn bộ chức năng (PASS 100%)
├── requirements.txt    # Danh sách thư viện phụ thuộc
└── README.md           # Tài liệu hướng dẫn
```

## 2. Quy trình chuẩn 3 bước trên giao diện phần mềm

1. **Bước 1 (Xử lý đầu vào):**
   - Mở ảnh từ máy tính (hoặc bấm tải ảnh mẫu đêm để thử ngay).
   - Kéo thanh trượt **Tăng sáng Gamma** $\rightarrow$ Bấm nút **Bù sáng Gamma** hoặc **Cân bằng sáng YCrCb**.
   - Kéo thanh trượt Mức độ làm mịn $\rightarrow$ Bấm nút **Làm mịn da & Khử khuyết điểm (Bilateral + Median)**.
2. **Bước 2 (Chọn phong cách tranh vẽ):**
   - Chọn kiểu: **Tranh phác thảo chì mỹ thuật (Color Dodge)** hoặc **Tranh nét viền truyện tranh (Sobel Outline)**.
   - Kéo thanh trượt điều chỉnh **Độ đậm / Chi tiết nét vẽ** $\rightarrow$ Bấm **Biến thành Tranh vẽ**.
3. **Bước 3 (Xuất sản phẩm & Báo cáo):**
   - Bấm nút lớn **Quy trình 1-Chạm (All-in-One)** để tự động thực thi chuỗi: Sáng ảnh $\rightarrow$ Mịn da $\rightarrow$ Tranh vẽ.
   - Bấm nút **Xem biểu đồ Histogram Trước - Sau** để giải thích đối chiếu học thuật với giảng viên.
   - Bấm **Lưu tranh kết quả** để xuất file ảnh chất lượng cao.

## 3. Cách chạy chương trình

Mở Terminal tại thư mục `Doan_XLAvV_GK_Gr4` và chạy:

```bash
python main_app.py
```

Để chạy kiểm thử tự động toàn bộ các hàm:
```bash
python test_all.py
```
