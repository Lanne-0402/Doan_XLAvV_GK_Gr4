"""
CHƯƠNG TRÌNH CHÍNH: PHOTO ENHANCER & SKETCH TOOL (NHÓM 4)
---------------------------------------------------------
Phụ trách xây dựng giao diện & tích hợp: Thành viên 1
Cấu trúc kết nối:
- Mô-đun 1 (module_enhance.py) : Tăng sáng, Cân bằng Histogram, Log, Gamma, Vẽ Histogram
- Mô-đun 2 (module_denoise.py) : Làm mịn & Khử nhiễu (Thành viên 2)
- Mô-đun 3 (module_sketch.py)  : Tạo hiệu ứng Tranh vẽ phác thảo Sketch Art (Thành viên 3)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

# 1. Import Mô-đun 1 (Nhiệm vụ của Thành viên 1)
import module_enhance as mod1

# 2. Import Mô-đun 2 (Nhiệm vụ của Thành viên 2 - Có kiểm tra an toàn khi ghép code)
try:
    import module_denoise as mod2
    HAS_MOD2 = True
except ImportError:
    mod2 = None
    HAS_MOD2 = False

# 3. Import Mô-đun 3 (Nhiệm vụ của Thành viên 3 - Có kiểm tra an toàn khi ghép code)
try:
    import module_sketch as mod3
    HAS_MOD3 = True
except ImportError:
    mod3 = None
    HAS_MOD3 = False


def read_image_unicode(file_path: str) -> np.ndarray:
    """Đọc ảnh hỗ trợ đường dẫn tiếng Việt có dấu trên Windows."""
    stream = np.fromfile(file_path, dtype=np.uint8)
    img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
    return img


def save_image_unicode(file_path: str, img: np.ndarray) -> bool:
    """Lưu ảnh hỗ trợ đường dẫn tiếng Việt có dấu trên Windows."""
    ext = os.path.splitext(file_path)[1]
    if not ext:
        ext = ".png"
    success, encoded_img = cv2.imencode(ext, img)
    if success:
        encoded_img.tofile(file_path)
        return True
    return False


class PhotoEnhancerSketchApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Photo Enhancer & Sketch Tool - Đồ án Giữa kỳ Xử lý ảnh & Video (Nhóm 4)")
        self.root.geometry("1280x780")
        self.root.minsize(1100, 680)
        self.root.configure(bg="#f4f6f9")

        # Biến lưu trữ ảnh gốc (Before) và ảnh sau xử lý (After)
        self.img_original: np.ndarray = None
        self.img_processed: np.ndarray = None
        self.last_operation_name: str = "Ảnh sau xử lý"
        self.chain_mode = tk.BooleanVar(value=False)

        self._build_ui()
        # Khởi tạo sẵn một bức ảnh mẫu thiếu sáng để có thể bấm thử ngay lập tức
        self.load_demo_image()

    def _build_ui(self):
        """Thiết kế bố cục giao diện chính: Cột điều khiển bên trái & Khung ảnh Trước-Sau bên phải."""
        # Tiêu đề ứng dụng
        header = tk.Frame(self.root, bg="#1e293b", height=50)
        header.pack(side=tk.TOP, fill=tk.X)
        lbl_title = tk.Label(
            header,
            text="PHOTO ENHANCER & SKETCH TOOL (CÔNG CỤ XỬ LÝ & BIẾN ẢNH CHỤP THÀNH TRANH VẼ)",
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg="#1e293b",
            pady=10,
        )
        lbl_title.pack()

        # Vùng nội dung chính
        main_frame = tk.Frame(self.root, bg="#f4f6f9")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=8)

        # --- CỘT ĐIỀU KHIỂN BÊN TRÁI (Có thanh cuộn) ---
        left_container = tk.Frame(main_frame, bg="#f4f6f9", width=340)
        left_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_container.pack_propagate(False)

        canvas_ctrl = tk.Canvas(left_container, bg="#f4f6f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas_ctrl.yview)
        self.ctrl_frame = tk.Frame(canvas_ctrl, bg="#f4f6f9")

        self.ctrl_frame.bind(
            "<Configure>",
            lambda e: canvas_ctrl.configure(scrollregion=canvas_ctrl.bbox("all")),
        )
        canvas_ctrl.create_window((0, 0), window=self.ctrl_frame, anchor="nw", width=320)
        canvas_ctrl.configure(yscrollcommand=scrollbar.set)

        canvas_ctrl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- KHUNG HIỂN THỊ ẢNH TRƯỚC - SAU BÊN PHẢI ---
        right_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief=tk.SOLID)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(1, weight=1)
        right_frame.rowconfigure(1, weight=1)

        # Tiêu đề khung Trước - Sau
        lbl_before_title = tk.Label(
            right_frame,
            text="ẢNH GỐC (BEFORE)",
            font=("Segoe UI", 11, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            pady=6,
        )
        lbl_before_title.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=(8, 4))

        self.lbl_after_title = tk.Label(
            right_frame,
            text="ẢNH SAU XỬ LÝ (AFTER)",
            font=("Segoe UI", 11, "bold"),
            bg="#dbeafe",
            fg="#1e3a8a",
            pady=6,
        )
        self.lbl_after_title.grid(row=0, column=1, sticky="ew", padx=(4, 8), pady=(8, 4))

        # Khung chứa ảnh Trước và Sau
        self.panel_before = tk.Label(right_frame, bg="#f8fafc", bd=1, relief=tk.SUNKEN)
        self.panel_before.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))

        self.panel_after = tk.Label(right_frame, bg="#f8fafc", bd=1, relief=tk.SUNKEN)
        self.panel_after.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))

        # Tự động co giãn ảnh khi thay đổi kích thước cửa sổ
        self.panel_before.bind("<Configure>", lambda e: self.refresh_image_panels())

        # Thanh trạng thái dưới đáy
        self.status_var = tk.StringVar(value="Sẵn sàng. Hãy tải ảnh lên hoặc dùng ảnh mẫu để trải nghiệm.")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            padx=10,
            pady=4,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Xây dựng các nhóm nút chức năng ở cột trái
        self._build_file_section()
        self._build_module1_section()
        self._build_module2_section()
        self._build_module3_section()
        self._build_pipeline_section()

    # =========================================================================
    # XÂY DỰNG CÁC BẢNG ĐIỀU KHIỂN CỘT TRÁI
    # =========================================================================
    def _build_file_section(self):
        frame = tk.LabelFrame(
            self.ctrl_frame,
            text=" 0. Quản lý Ảnh Đầu Vào / Đầu Ra ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 8))

        btn_open = tk.Button(
            frame,
            text="📂 Chọn ảnh từ máy tính...",
            command=self.open_image,
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            pady=4,
        )
        btn_open.pack(fill=tk.X, pady=2)

        btn_demo = tk.Button(
            frame,
            text="🌙 Tạo ảnh mẫu thiếu sáng & nhiễu",
            command=self.load_demo_image,
            bg="#475569",
            fg="white",
            font=("Segoe UI", 9),
            pady=3,
        )
        btn_demo.pack(fill=tk.X, pady=2)

        chk_chain = tk.Checkbutton(
            frame,
            text="Xử lý nối tiếp trên ảnh kết quả (Chaining)",
            variable=self.chain_mode,
            bg="#ffffff",
            font=("Segoe UI", 9),
        )
        chk_chain.pack(anchor="w", pady=2)

        row_btn = tk.Frame(frame, bg="#ffffff")
        row_btn.pack(fill=tk.X, pady=2)

        btn_reset = tk.Button(
            row_btn,
            text="🔄 Khôi phục gốc",
            command=self.reset_image,
            bg="#e2e8f0",
            font=("Segoe UI", 9),
        )
        btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        btn_save = tk.Button(
            row_btn,
            text="💾 Lưu ảnh kết quả",
            command=self.save_image,
            bg="#16a34a",
            fg="white",
            font=("Segoe UI", 9, "bold"),
        )
        btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

    def _build_module1_section(self):
        """Giao diện Mô-đun 1: Nhiệm vụ của Thành viên 1."""
        frame = tk.LabelFrame(
            self.ctrl_frame,
            text=" 1. Tăng Sáng & Tương Phản (Thành viên 1) ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1d4ed8",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 8))

        tk.Button(
            frame,
            text="Chuyển sang Ảnh Xám (Grayscale)",
            command=self.action_grayscale,
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="Cân bằng Histogram (Ảnh xám - equalizeHist)",
            command=lambda: self.action_hist_eq(keep_color=False),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="Cân bằng Histogram (Giữ màu tự nhiên)",
            command=lambda: self.action_hist_eq(keep_color=True),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="Biến đổi Logarit (Bù sáng vùng tối)",
            command=self.action_log_transform,
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="Kéo giãn tương phản (Contrast Stretching)",
            command=self.action_contrast_stretch,
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        # Thanh trượt điều chỉnh Gamma
        lbl_gamma = tk.Label(
            frame,
            text="Hệ số Gamma (γ < 1: Tăng sáng | γ > 1: Giảm sáng):",
            bg="#ffffff",
            font=("Segoe UI", 8, "bold"),
        )
        lbl_gamma.pack(anchor="w", pady=(6, 0))

        self.gamma_var = tk.DoubleVar(value=0.45)
        scale_gamma = tk.Scale(
            frame,
            from_=0.1,
            to=3.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.gamma_var,
            bg="#ffffff",
            highlightthickness=0,
        )
        scale_gamma.pack(fill=tk.X)

        tk.Button(
            frame,
            text="⚡ Áp dụng Biến đổi Gamma",
            command=self.action_gamma_transform,
            bg="#dbeafe",
            fg="#1e3a8a",
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="📊 Vẽ biểu đồ Histogram Trước - Sau",
            command=self.action_show_histogram,
            bg="#0284c7",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            pady=3,
        ).pack(fill=tk.X, pady=(6, 2))

    def _build_module2_section(self):
        """Giao diện Mô-đun 2: Điểm kết nối với Thành viên 2."""
        frame = tk.LabelFrame(
            self.ctrl_frame,
            text=" 2. Làm Mịn & Khử Nhiễu (Thành viên 2) ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#047857",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 8))

        lbl_ksize = tk.Label(
            frame,
            text="Kích thước mặt nạ lọc (Kernel size):",
            bg="#ffffff",
            font=("Segoe UI", 8, "bold"),
        )
        lbl_ksize.pack(anchor="w")

        self.ksize_var = tk.IntVar(value=5)
        scale_k = tk.Scale(
            frame,
            from_=3,
            to=15,
            resolution=2,
            orient=tk.HORIZONTAL,
            variable=self.ksize_var,
            bg="#ffffff",
            highlightthickness=0,
        )
        scale_k.pack(fill=tk.X)

        tk.Button(
            frame,
            text="Bộ lọc Trung bình (Mean Filter)",
            command=lambda: self.action_mod2("mean"),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="Bộ lọc Gaussian (Gaussian Blur)",
            command=lambda: self.action_mod2("gaussian"),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="Bộ lọc Trung vị (Median - Khử nhiễu đốm)",
            command=lambda: self.action_mod2("median"),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="✨ Lọc Bilateral (Làm mịn da & Giữ nét biên)",
            command=lambda: self.action_mod2("bilateral"),
            bg="#d1fae5",
            fg="#065f46",
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X, pady=2)

    def _build_module3_section(self):
        """Giao diện Mô-đun 3: Điểm kết nối với Thành viên 3."""
        frame = tk.LabelFrame(
            self.ctrl_frame,
            text=" 3. Phác Thảo Tranh Vẽ - Sketch (Thành viên 3) ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#7c3aed",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 8))

        lbl_sketch_k = tk.Label(
            frame,
            text="Độ đậm nét phác thảo chì (Gaussian Kernel):",
            bg="#ffffff",
            font=("Segoe UI", 8, "bold"),
        )
        lbl_sketch_k.pack(anchor="w")

        self.sketch_blur_var = tk.IntVar(value=21)
        scale_sketch = tk.Scale(
            frame,
            from_=5,
            to=51,
            resolution=2,
            orient=tk.HORIZONTAL,
            variable=self.sketch_blur_var,
            bg="#ffffff",
            highlightthickness=0,
        )
        scale_sketch.pack(fill=tk.X)

        tk.Button(
            frame,
            text="Lấy Ảnh Âm Bản (Negative Image)",
            command=lambda: self.action_mod3("negative"),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="✏️ Tranh vẽ chì (Pencil Sketch - Color Dodge)",
            command=lambda: self.action_mod3("pencil"),
            bg="#ede9fe",
            fg="#5b21b6",
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="🖋️ Tranh nét viền (Sobel Edge Sketch)",
            command=lambda: self.action_mod3("sobel"),
            bg="#f1f5f9",
            font=("Segoe UI", 9),
        ).pack(fill=tk.X, pady=2)

    def _build_pipeline_section(self):
        """Kết hợp toàn diện cả 3 mô-đun của 3 thành viên."""
        frame = tk.LabelFrame(
            self.ctrl_frame,
            text=" 4. Quy trình Kết hợp Tự động (3 Mô-đun) ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#be123c",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 8))

        tk.Button(
            frame,
            text="🚀 Bù sáng Gamma + Làm mịn da Bilateral",
            command=self.action_combo_enhance_smooth,
            bg="#ffe4e6",
            fg="#9f1239",
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="🎨 Bù sáng + Khử nhiễu + Chuyển thành Sketch",
            command=self.action_combo_full_sketch,
            bg="#be123c",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            pady=3,
        ).pack(fill=tk.X, pady=2)

    # =========================================================================
    # CÁC HÀM HỖ TRỢ HIỂN THỊ & ĐỌC/GHI ẢNH
    # =========================================================================
    def _get_source_image(self) -> np.ndarray:
        """
        Lấy ảnh đầu vào cho phép toán:
        - Nếu bật chế độ 'Xử lý nối tiếp (Chaining)' thì lấy ảnh kết quả hiện tại làm đầu vào.
        - Ngược lại luôn lấy từ ảnh gốc ban đầu.
        """
        if self.chain_mode.get() and self.img_processed is not None:
            return self.img_processed.copy()
        if self.img_original is not None:
            return self.img_original.copy()
        return None

    def _update_result(self, result_img: np.ndarray, op_name: str):
        """Cập nhật ảnh đầu ra và hiển thị lên khung bên phải."""
        if result_img is None:
            return
        self.img_processed = result_img
        self.last_operation_name = op_name
        self.lbl_after_title.config(text=f"ẢNH SAU XỬ LÝ: {op_name.upper()}")
        self.refresh_image_panels()
        h, w = result_img.shape[:2]
        channels = 1 if len(result_img.shape) == 2 else result_img.shape[2]
        self.status_var.set(f"Đã thực hiện: {op_name} | Kích thước: {w}x{h} | Số kênh: {channels}")

    def _cv2_to_imagetk(self, img: np.ndarray, max_w: int, max_h: int) -> ImageTk.PhotoImage:
        """Chuyển đổi mảng ảnh OpenCV (BGR/Gray) sang ImageTk vừa khít khung hiển thị."""
        if len(img.shape) == 2:
            rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        h, w = rgb.shape[:2]
        max_w = max(150, max_w - 16)
        max_h = max(150, max_h - 16)
        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        pil_img = Image.fromarray(rgb).resize((new_w, new_h), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(pil_img)

    def refresh_image_panels(self):
        """Cập nhật lại 2 khung ảnh Trước và Sau."""
        w = self.panel_before.winfo_width()
        h = self.panel_before.winfo_height()
        if w <= 10 or h <= 10:
            w, h = 420, 480

        if self.img_original is not None:
            tk_before = self._cv2_to_imagetk(self.img_original, w, h)
            self.panel_before.config(image=tk_before)
            self.panel_before.image = tk_before

        if self.img_processed is not None:
            tk_after = self._cv2_to_imagetk(self.img_processed, w, h)
            self.panel_after.config(image=tk_after)
            self.panel_after.image = tk_after

    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Chọn hình ảnh cần xử lý",
            filetypes=[
                ("Tệp hình ảnh", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Tất cả các tệp", "*.*"),
            ],
        )
        if not file_path:
            return
        img = read_image_unicode(file_path)
        if img is None:
            messagebox.showerror("Lỗi đọc ảnh", "Không thể đọc tệp hình ảnh đã chọn!")
            return
        self.img_original = img
        self._update_result(img.copy(), "Ảnh gốc mới tải lên")

    def save_image(self):
        if self.img_processed is None:
            messagebox.showwarning("Chưa có ảnh", "Chưa có ảnh kết quả để lưu!")
            return
        file_path = filedialog.asksaveasfilename(
            title="Lưu ảnh kết quả",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("BMP Image", "*.bmp")],
        )
        if not file_path:
            return
        if save_image_unicode(file_path, self.img_processed):
            messagebox.showinfo("Thành công", f"Đã lưu ảnh thành công tại:\n{file_path}")
        else:
            messagebox.showerror("Lỗi", "Không thể lưu ảnh!")

    def reset_image(self):
        if self.img_original is not None:
            self._update_result(self.img_original.copy(), "Khôi phục ảnh gốc")

    def load_demo_image(self):
        """Tạo một bức ảnh chân dung/phong cảnh giả lập thiếu sáng kèm nhiễu hạt để test ngay."""
        h, w = 420, 520
        # Tạo nền đêm tối chuyển sắc (mức sáng thấp từ 12 đến 75)
        y_grad = np.linspace(15, 70, h, dtype=np.float32)[:, None]
        x_grad = np.linspace(10, 50, w, dtype=np.float32)[None, :]
        bg_b = np.clip(y_grad + x_grad * 0.4, 0, 255).astype(np.uint8)
        bg_g = np.clip(y_grad * 0.8 + x_grad * 0.3, 0, 255).astype(np.uint8)
        bg_r = np.clip(y_grad * 0.7 + x_grad * 0.2, 0, 255).astype(np.uint8)
        img = cv2.merge([bg_b, bg_g, bg_r])

        # Vẽ mặt trăng và các tòa nhà/cây cối cùng nhân vật cách điệu trong bóng tối
        cv2.circle(img, (410, 85), 42, (95, 115, 125), -1)
        cv2.rectangle(img, (40, 210), (140, 420), (28, 34, 45), -1)
        cv2.rectangle(img, (160, 170), (260, 420), (35, 42, 55), -1)

        # Vẽ khuôn mặt chân dung cách điệu ở trung tâm
        cv2.ellipse(img, (330, 260), (75, 95), 0, 0, 360, (62, 76, 98), -1)
        cv2.circle(img, (302, 240), 10, (20, 22, 28), -1)
        cv2.circle(img, (358, 240), 10, (20, 22, 28), -1)
        cv2.ellipse(img, (330, 295), (28, 14), 0, 0, 180, (35, 38, 65), 3)

        # Thêm một số hạt nhiễu muối tiêu nhẹ để test bộ lọc khử nhiễu
        rng = np.random.default_rng(42)
        noise_mask = rng.random((h, w))
        img[noise_mask < 0.008] = [180, 180, 180]
        img[noise_mask > 0.992] = [5, 5, 5]

        self.img_original = img
        self._update_result(img.copy(), "Ảnh mẫu thiếu sáng (Demo)")

    # =========================================================================
    # XỬ LÝ SỰ KIỆN MÔ-ĐUN 1 (THÀNH VIÊN 1)
    # =========================================================================
    def action_grayscale(self):
        src = self._get_source_image()
        res = mod1.to_grayscale(src)
        self._update_result(res, "Ảnh mức xám (Grayscale)")

    def action_hist_eq(self, keep_color: bool):
        src = self._get_source_image()
        res = mod1.apply_histogram_eq(src, keep_color=keep_color)
        label = "Cân bằng Histogram (Giữ màu)" if keep_color else "Cân bằng Histogram (Ảnh xám)"
        self._update_result(res, label)

    def action_log_transform(self):
        src = self._get_source_image()
        res = mod1.apply_log_transform(src)
        self._update_result(res, "Biến đổi Logarit")

    def action_gamma_transform(self):
        src = self._get_source_image()
        gamma = float(self.gamma_var.get())
        res = mod1.apply_gamma_transform(src, gamma=gamma)
        self._update_result(res, f"Biến đổi Gamma (γ = {gamma:.2f})")

    def action_contrast_stretch(self):
        src = self._get_source_image()
        res = mod1.apply_contrast_stretching(src)
        self._update_result(res, "Kéo giãn tương phản tuyến tính")

    def action_show_histogram(self):
        if self.img_original is None or self.img_processed is None:
            messagebox.showwarning("Thông báo", "Cần có ảnh gốc và ảnh sau xử lý để vẽ Histogram!")
            return
        mod1.plot_histogram_comparison(
            self.img_original, self.img_processed, title_after=self.last_operation_name
        )

    # =========================================================================
    # XỬ LÝ SỰ KIỆN MÔ-ĐUN 2 (KẾT NỐI CODE THÀNH VIÊN 2)
    # =========================================================================
    def action_mod2(self, filter_type: str):
        if not HAS_MOD2 or mod2 is None:
            messagebox.showinfo(
                "Chờ ghép code Thành viên 2",
                "Mô-đun 2 (module_denoise.py) chưa được kết nối!",
            )
            return

        src = self._get_source_image()
        ksize = int(self.ksize_var.get())

        if filter_type == "mean":
            res = mod2.apply_mean_filter(src, ksize=ksize)
            self._update_result(res, f"Lọc Trung bình ({ksize}x{ksize})")
        elif filter_type == "gaussian":
            res = mod2.apply_gaussian_filter(src, ksize=ksize)
            self._update_result(res, f"Lọc Gaussian ({ksize}x{ksize})")
        elif filter_type == "median":
            res = mod2.apply_median_filter(src, ksize=ksize)
            self._update_result(res, f"Lọc Trung vị Median ({ksize}x{ksize})")
        elif filter_type == "bilateral":
            res = mod2.apply_bilateral_filter(src, d=ksize, sigma_color=75, sigma_space=75)
            self._update_result(res, f"Lọc Bilateral Làm mịn giữ biên (d={ksize})")

    # =========================================================================
    # XỬ LÝ SỰ KIỆN MÔ-ĐUN 3 (KẾT NỐI CODE THÀNH VIÊN 3)
    # =========================================================================
    def action_mod3(self, sketch_type: str):
        if not HAS_MOD3 or mod3 is None:
            messagebox.showinfo(
                "Chờ ghép code Thành viên 3",
                "Mô-đun 3 (module_sketch.py) chưa được kết nối!",
            )
            return

        src = self._get_source_image()
        blur_k = int(self.sketch_blur_var.get())

        if sketch_type == "negative":
            res = mod3.apply_negative(src)
            self._update_result(res, "Ảnh Âm Bản (Negative)")
        elif sketch_type == "pencil":
            res = mod3.apply_pencil_sketch(src, blur_ksize=blur_k)
            self._update_result(res, f"Tranh Vẽ Chì - Color Dodge (k={blur_k})")
        elif sketch_type == "sobel":
            res = mod3.apply_sobel_sketch(src, ksize=3)
            self._update_result(res, "Tranh Nét Viền - Sobel Sketch")

    # =========================================================================
    # QUY TRÌNH PHỐI HỢP CẢ 3 MÔ-ĐUN (PIPELINE)
    # =========================================================================
    def action_combo_enhance_smooth(self):
        """Kết hợp Mô-đun 1 (Bù sáng Gamma) + Mô-đun 2 (Khử nhiễu & Làm mịn Bilateral)."""
        if self.img_original is None:
            return
        gamma = float(self.gamma_var.get())
        step1 = mod1.apply_gamma_transform(self.img_original, gamma=gamma)
        if HAS_MOD2 and mod2 is not None:
            step2 = mod2.apply_median_filter(step1, ksize=3)
            step3 = mod2.apply_bilateral_filter(step2, d=9, sigma_color=75, sigma_space=75)
            self._update_result(step3, f"Tăng sáng Gamma ({gamma}) + Làm mịn da")
        else:
            self._update_result(step1, f"Tăng sáng Gamma ({gamma})")

    def action_combo_full_sketch(self):
        """Kết hợp cả 3 Mô-đun: Bù sáng Gamma -> Khử nhiễu -> Chuyển thành Tranh vẽ chì."""
        if self.img_original is None:
            return
        gamma = float(self.gamma_var.get())
        blur_k = int(self.sketch_blur_var.get())

        # Sử dụng hàm pipeline do Toàn (Thành viên 3) phụ trách
        if HAS_MOD3 and hasattr(mod3, "pipeline_enhance_denoise_sketch"):
            res = mod3.pipeline_enhance_denoise_sketch(
                self.img_original, gamma=gamma, median_ksize=3, sketch_ksize=blur_k
            )
            self._update_result(res, "Pipeline: Tăng sáng + Khử nhiễu + Sketch Art")
            return

        step1 = mod1.apply_gamma_transform(self.img_original, gamma=gamma)
        if HAS_MOD2 and mod2 is not None:
            step2 = mod2.apply_median_filter(step1, ksize=3)
        else:
            step2 = step1

        if HAS_MOD3 and mod3 is not None:
            step3 = mod3.apply_pencil_sketch(step2, blur_ksize=blur_k)
            self._update_result(step3, "Pipeline: Tăng sáng + Khử nhiễu + Sketch Art")
        else:
            self._update_result(step2, "Pipeline: Tăng sáng + Khử nhiễu")


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEnhancerSketchApp(root)
    root.mainloop()
