BỘ ẢNH THỬ - MÔ-ĐUN 2: LÀM MỊN VÀ KHỬ NHIỄU
==========================================

Đặt denoise_images/ cùng thư mục main_app.py và module_denoise.py.

1. Dùng trong giao diện
- Bấm Chọn ảnh từ máy tính, mở ảnh trong noisy/ hoặc exposure/.
- Tắt Chaining khi so sánh từng bộ lọc để tất cả nhận cùng một ảnh gốc.
- Thử mặt nạ 3, 5, 9; giao diện cũng cho phép 7, 11, 13, 15.
- Median: thử camera_salt_pepper04.png; Gaussian/Mean: thử coffee_gaussian20.png.
- Bilateral: thử portrait_gaussian20.png, quan sát mắt, tóc và biên khuôn mặt.
- Pipeline tăng sáng + lọc: thử exposure/night_gaussian12.png hoặc
  exposure/backlit_gaussian12.png. Ảnh thiếu sáng/ngược sáng là GIẢ LẬP từ
  ảnh gốc, không phải ảnh chụp ban đêm hoặc ngược sáng thật.
- portrait_simulated_spots.png có đốm đỏ NHÂN TẠO; không phải mụn thật.
  Không dùng kết quả đó để tuyên bố tự động nhận diện/xóa mụn.

2. Cấu trúc
- clean/: 3 ảnh nguồn, chân dung cắt/phóng từ astronaut, ảnh biên tổng hợp.
- noisy/: nhiễu Gaussian sigma=20, muối tiêu xác suất tổng 4%, nhiễu hỗn hợp,
  chân dung có đốm nhân tạo. Gaussian thêm độc lập từng kênh, làm tròn và
  giới hạn 0..255. Muối tiêu tác động cả pixel màu, mỗi loại xác suất 2%.
- exposure/: cảnh tối gamma=2.2 và ngược sáng giả lập, mỗi loại có bản sạch
  cùng bản thêm nhiễu Gaussian sigma=12 để đánh giá khử nhiễu cùng mức sáng.
- manifest.json: đường dẫn, ảnh tham chiếu, thông số, kích thước, SHA-256.
- dataset_overview.jpg: xem nhanh toàn bộ 21 ảnh thử.
- results/: số liệu và ảnh so sánh minh họa đã chạy ở k=3,5,9.

3. Chạy thực nghiệm lại (từ thư mục chứa main_app.py)
   pip install numpy opencv-python pillow
   python denoise_images/compare_filters.py --sizes 3 5 9
   Thêm --save-images để lưu từng kết quả. CSV mặc định được ghi lại.
   python denoise_images/prepare_dataset.py
   Lệnh thứ hai tạo lại ảnh nhiễu với seed=42 từ 3 ảnh nguồn đã có,
   không tải lại ảnh. Nếu đổi dữ liệu, cần chạy lại compare_filters.py.

4. Đọc kết quả
- metrics.csv có MSE, PSNR trước/sau và thời gian trung vị 3 lần sau warm-up.
- PSNR tăng là sai số pixel giảm với ảnh tham chiếu này; không đủ để kết luận
  da tự nhiên hơn hoặc giữ biên tốt hơn. Quan sát thêm mắt/tóc/chữ/đường biên.
- Chỉ so PSNR với đúng reference trong manifest. Với ảnh tối, reference là
  bản tối chưa có nhiễu, không phải ảnh trước khi giảm sáng.
- So sánh cùng k chỉ là thiết lập thử nghiệm, không có nghĩa bốn bộ lọc có
  mức làm mịn tương đương. Bilateral dùng sigma_color=sigma_space=75;
  Gaussian dùng sigma=0 (OpenCV tự tính theo k).
- Thời gian phụ thuộc máy, phiên bản OpenCV, kích thước và số kênh ảnh.
- Lọc toàn ảnh có thể mất chi tiết; bộ dữ liệu nhỏ này là minh họa học tập.

5. Nguồn ảnh và ghi công
Ba ảnh tải từ kho chính thức scikit-image, phiên bản v0.19.3:
https://github.com/scikit-image/scikit-image/tree/v0.19.3/skimage/data
- astronaut.png: Eileen Collins, NASA, public domain.
- camera.png: Lav Varshney, CC0 (bản thay thế từ scikit-image 0.18).
- coffee.png: Rachel Michetti, CC0; ảnh tại Pikolo Espresso Bar.
Thông tin nguồn/quyền sử dụng:
https://scikit-image.org/docs/stable/api/skimage.data.html
Nguồn tải trực tiếp:
https://raw.githubusercontent.com/scikit-image/scikit-image/v0.19.3/skimage/data/astronaut.png
https://raw.githubusercontent.com/scikit-image/scikit-image/v0.19.3/skimage/data/camera.png
https://raw.githubusercontent.com/scikit-image/scikit-image/v0.19.3/skimage/data/coffee.png
Các bản nhiễu, thay đổi sáng, cắt ảnh và ảnh biên được tạo bằng prepare_dataset.py.

6. Tích hợp
main_app.py đã gọi đúng bốn hàm, không cần đổi giao diện.
module_denoise hỗ trợ uint8 xám (H,W) hoặc BGR (H,W,3), giữ nguyên ảnh gốc.
None trả None theo quy ước hiện tại. Dữ liệu sai kiểu/kích thước hoặc sigma
không hợp lệ phát sinh TypeError/ValueError với thông báo tiếng Việt.
Kích thước nguyên <3 được nâng lên 3, số chẵn tăng lên lẻ kế tiếp.
Gaussian có tham số tùy chọn sigma=0.0; lời gọi cũ không cần đổi.
Mô-đun chỉ cần numpy và opencv-python; Pillow dùng cho GUI/bộ ảnh thực nghiệm.
Để chạy toàn bộ main_app.py, cần thêm module_enhance.py; module_sketch.py
là mô-đun riêng của thành viên 3. Các file đó không thuộc phần bàn giao này.
