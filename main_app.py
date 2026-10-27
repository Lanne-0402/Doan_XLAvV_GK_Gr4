"""
main_app.py - Giao diện chính: Photo Enhancer & Sketch Tool
Quy trình chuẩn 3 bước:
- Bước 1 (Xử lý đầu vào): Tăng sáng Gamma/Histogram & Làm mịn da tẩy khuyết điểm (Bilateral + Median).
- Bước 2 (Phong cách tranh vẽ): Tranh phác thảo chì (Color Dodge) hoặc Tranh nét viền truyện tranh (Sobel).
- Bước 3 (Xuất sản phẩm): Quy trình 1-Chạm (All-in-One), Xem biểu đồ Histogram & Lưu tranh kết quả.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

import module_enhance as mod1
import module_denoise as mod2
import module_sketch as mod3


def read_image_unicode(file_path: str) -> np.ndarray:
    """Đọc ảnh hỗ trợ đường dẫn tiếng Việt có dấu trên Windows."""
    stream = np.fromfile(file_path, dtype=np.uint8)
    return cv2.imdecode(stream, cv2.IMREAD_COLOR)


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
        self.root.geometry("1280x760")
        self.root.minsize(1050, 650)
        self.root.configure(bg="#f1f5f9")

        # Quản lý trạng thái ảnh
        self.img_original: np.ndarray = None
        self.img_processed: np.ndarray = None
        self.last_op_name: str = "Ảnh gốc"
        self.history_stack: list[tuple[np.ndarray, str]] = []

        self._build_ui()
        self.load_demo_image()

    def _build_ui(self):
        # 1. Header ứng dụng
        header = tk.Frame(self.root, bg="#0f172a", height=48)
        header.pack(side=tk.TOP, fill=tk.X)
        lbl_title = tk.Label(
            header,
            text="PHOTO ENHANCER & SKETCH TOOL (XỬ LÝ ẢNH & BIẾN ẢNH CHỤP THÀNH TRANH VẼ NÉT VIỀN)",
            font=("Segoe UI", 12, "bold"),
            fg="#f8fafc",
            bg="#0f172a",
            pady=10,
        )
        lbl_title.pack()

        # 2. Vùng làm việc chính
        work_area = tk.Frame(self.root, bg="#f1f5f9")
        work_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Cột điều khiển bên trái (có thanh cuộn nếu màn hình nhỏ)
        left_box = tk.Frame(work_area, bg="#f1f5f9", width=350)
        left_box.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_box.pack_propagate(False)

        canvas_ctrl = tk.Canvas(left_box, bg="#f1f5f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_box, orient="vertical", command=canvas_ctrl.yview)
        self.ctrl_panel = tk.Frame(canvas_ctrl, bg="#f1f5f9")

        self.ctrl_panel.bind(
            "<Configure>",
            lambda e: canvas_ctrl.configure(scrollregion=canvas_ctrl.bbox("all")),
        )
        ctrl_win = canvas_ctrl.create_window((0, 0), window=self.ctrl_panel, anchor="nw", width=330)
        canvas_ctrl.configure(yscrollcommand=scrollbar.set)
        canvas_ctrl.bind("<Configure>", lambda e: canvas_ctrl.itemconfig(ctrl_win, width=e.width))

        canvas_ctrl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Hỗ trợ cuộn chuột
        def _on_mousewheel(event):
            delta = event.delta if hasattr(event, "delta") and event.delta else 120
            canvas_ctrl.yview_scroll(int(-1 * (delta / 60)), "units")

        canvas_ctrl.bind("<Enter>", lambda e: canvas_ctrl.bind_all("<MouseWheel>", _on_mousewheel))
        canvas_ctrl.bind("<Leave>", lambda e: canvas_ctrl.unbind_all("<MouseWheel>"))

        # Cột hiển thị ảnh Trước - Sau bên phải
        right_box = tk.Frame(work_area, bg="#ffffff", bd=1, relief=tk.SOLID)
        right_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_box.columnconfigure(0, weight=1)
        right_box.columnconfigure(1, weight=1)
        right_box.rowconfigure(1, weight=1)

        lbl_before = tk.Label(
            right_box,
            text="ẢNH GỐC (BEFORE)",
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            pady=5,
        )
        lbl_before.grid(row=0, column=0, sticky="ew", padx=(6, 3), pady=(6, 3))

        self.lbl_after = tk.Label(
            right_box,
            text="ẢNH SAU XỬ LÝ (AFTER)",
            font=("Segoe UI", 10, "bold"),
            bg="#dbeafe",
            fg="#1e3a8a",
            pady=5,
        )
        self.lbl_after.grid(row=0, column=1, sticky="ew", padx=(3, 6), pady=(6, 3))

        self.panel_before = tk.Label(right_box, bg="#f8fafc", bd=1, relief=tk.SUNKEN)
        self.panel_before.grid(row=1, column=0, sticky="nsew", padx=(6, 3), pady=(0, 6))

        self.panel_after = tk.Label(right_box, bg="#f8fafc", bd=1, relief=tk.SUNKEN)
        self.panel_after.grid(row=1, column=1, sticky="nsew", padx=(3, 6), pady=(0, 6))

        self.panel_before.bind("<Configure>", lambda e: self.refresh_image_panels())

        # Thanh trạng thái dưới cùng
        self.status_var = tk.StringVar(value="Sẵn sàng. Hãy tải ảnh lên hoặc chọn ảnh mẫu.")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            padx=10,
            pady=3,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Xây dựng các khối chức năng 3 bước
        self._build_top_file_bar()
        self._build_step1_enhance()
        self._build_step2_sketch()
        self._build_step3_output()

    # =========================================================================
    # CÁC KHỐI CHỨC NĂNG THEO QUY TRÌNH 3 BƯỚC
    # =========================================================================
    def _build_top_file_bar(self):
        """Khung công cụ đầu vào nhanh."""
        frame = tk.LabelFrame(
            self.ctrl_panel,
            text=" Tệp tin & Lịch sử ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#334155",
            padx=6,
            pady=4,
        )
        frame.pack(fill=tk.X, pady=(0, 6))

        btn_open = tk.Button(
            frame,
            text="📂 Chọn ảnh từ máy tính...",
            command=self.open_image,
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            pady=3,
        )
        btn_open.pack(fill=tk.X, pady=2)

        btn_demo = tk.Button(
            frame,
            text="🌙 Tải ảnh mẫu ban đêm (Demo)",
            command=self.load_demo_image,
            bg="#475569",
            fg="white",
            font=("Segoe UI", 8),
            pady=2,
        )
        btn_demo.pack(fill=tk.X, pady=2)

        row = tk.Frame(frame, bg="#ffffff")
        row.pack(fill=tk.X, pady=2)

        tk.Button(
            row,
            text="🔄 Khôi phục gốc",
            command=self.reset_image,
            bg="#f1f5f9",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        tk.Button(
            row,
            text="↩️ Hoàn tác (Undo)",
            command=self.action_undo,
            bg="#f1f5f9",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

    def _build_step1_enhance(self):
        """BƯỚC 1: XỬ LÝ ĐẦU VÀO (Tăng sáng Gamma & Làm mịn da tẩy khuyết điểm)."""
        frame = tk.LabelFrame(
            self.ctrl_panel,
            text=" BƯỚC 1: XỬ LÝ ĐẦU VÀO ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1d4ed8",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 6))

        # 1. Bù sáng Gamma
        lbl_g = tk.Label(
            frame,
            text="1. Tăng sáng Gamma (γ < 1: Sáng lên | γ > 1: Giảm lóa):",
            bg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            fg="#1e293b",
        )
        lbl_g.pack(anchor="w")

        self.gamma_var = tk.DoubleVar(value=0.50)
        scale_gamma = tk.Scale(
            frame,
            from_=0.10,
            to=2.50,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.gamma_var,
            bg="#ffffff",
            highlightthickness=0,
        )
        scale_gamma.pack(fill=tk.X)

        row_light = tk.Frame(frame, bg="#ffffff")
        row_light.pack(fill=tk.X, pady=2)

        tk.Button(
            row_light,
            text="⚡ Bù sáng Gamma",
            command=self.action_apply_gamma,
            bg="#dbeafe",
            fg="#1e3a8a",
            font=("Segoe UI", 8, "bold"),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        tk.Button(
            row_light,
            text="Cân bằng sáng YCrCb",
            command=self.action_apply_hist_eq_color,
            bg="#f1f5f9",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # 2. Làm mịn da & Tẩy khuyết điểm
        lbl_smooth = tk.Label(
            frame,
            text="2. Mức độ làm mịn da (Bilateral diameter):",
            bg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            fg="#047857",
        )
        lbl_smooth.pack(anchor="w", pady=(6, 0))

        self.smooth_d_var = tk.IntVar(value=9)
        scale_smooth = tk.Scale(
            frame,
            from_=3,
            to=19,
            resolution=2,
            orient=tk.HORIZONTAL,
            variable=self.smooth_d_var,
            bg="#ffffff",
            highlightthickness=0,
        )
        scale_smooth.pack(fill=tk.X)

        tk.Button(
            frame,
            text="✨ Làm mịn da & Khử khuyết điểm (Bilateral + Median)",
            command=self.action_apply_skin_smooth,
            bg="#d1fae5",
            fg="#065f46",
            font=("Segoe UI", 8, "bold"),
            pady=3,
        ).pack(fill=tk.X, pady=2)

    def _build_step2_sketch(self):
        """BƯỚC 2: CHỌN PHONG CÁCH TRANH VẼ (Color Dodge hoặc Sobel)."""
        frame = tk.LabelFrame(
            self.ctrl_panel,
            text=" BƯỚC 2: CHỌN PHONG CÁCH TRANH VẼ ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#7c3aed",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 6))

        self.sketch_style_var = tk.StringVar(value="pencil")

        rb1 = tk.Radiobutton(
            frame,
            text="✏️ Tranh phác thảo chì (Color Dodge)",
            variable=self.sketch_style_var,
            value="pencil",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            command=self._on_style_change,
        )
        rb1.pack(anchor="w", pady=1)

        rb2 = tk.Radiobutton(
            frame,
            text="🖋️ Tranh nét viền truyện tranh (Sobel Outline)",
            variable=self.sketch_style_var,
            value="sobel",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            command=self._on_style_change,
        )
        rb2.pack(anchor="w", pady=1)

        self.lbl_sketch_param = tk.Label(
            frame,
            text="Độ đậm nhạt nét vẽ (Gaussian Blur):",
            bg="#ffffff",
            font=("Segoe UI", 8, "bold"),
        )
        self.lbl_sketch_param.pack(anchor="w", pady=(4, 0))

        self.sketch_ksize_var = tk.IntVar(value=21)
        self.scale_sketch = tk.Scale(
            frame,
            from_=5,
            to=45,
            resolution=2,
            orient=tk.HORIZONTAL,
            variable=self.sketch_ksize_var,
            bg="#ffffff",
            highlightthickness=0,
        )
        self.scale_sketch.pack(fill=tk.X)

        tk.Button(
            frame,
            text="🎨 Biến thành Tranh vẽ",
            command=self.action_apply_sketch,
            bg="#ede9fe",
            fg="#5b21b6",
            font=("Segoe UI", 9, "bold"),
            pady=3,
        ).pack(fill=tk.X, pady=3)

    def _build_step3_output(self):
        """BƯỚC 3: XUẤT SẢN PHẨM & BÁO CÁO."""
        frame = tk.LabelFrame(
            self.ctrl_panel,
            text=" BƯỚC 3: XUẤT SẢN PHẨM & BÁO CÁO ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#be123c",
            padx=8,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=(0, 6))

        # Nút 1-Chạm All-in-One
        tk.Button(
            frame,
            text="🚀 QUY TRÌNH 1-CHẠM (ALL-IN-ONE)\nẢnh chụp ➔ Tranh vẽ nét hoàn chỉnh",
            command=self.action_one_click_all_in_one,
            bg="#be123c",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            pady=6,
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            frame,
            text="📊 Xem biểu đồ Histogram Trước - Sau",
            command=self.action_show_histogram,
            bg="#0284c7",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            pady=3,
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="💾 Lưu tranh kết quả",
            command=self.save_image,
            bg="#16a34a",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            pady=3,
        ).pack(fill=tk.X, pady=(2, 0))

    # =========================================================================
    # HÀM XỬ LÝ SỰ KIỆN & CHUYỂN ĐỔI ẢNH
    # =========================================================================
    def _on_style_change(self):
        if self.sketch_style_var.get() == "pencil":
            self.lbl_sketch_param.config(text="Độ đậm nét chì (Gaussian Blur ksize):")
            self.scale_sketch.config(from_=5, to=45, resolution=2)
            self.sketch_ksize_var.set(21)
        else:
            self.lbl_sketch_param.config(text="Kích thước mặt nạ biên Sobel (1, 3, 5, 7):")
            self.scale_sketch.config(from_=1, to=7, resolution=2)
            self.sketch_ksize_var.set(3)

    def _update_result(self, result_img: np.ndarray, op_name: str):
        if result_img is None:
            return

        if self.img_processed is not None:
            self.history_stack.append((self.img_processed.copy(), self.last_op_name))
            if len(self.history_stack) > 10:
                self.history_stack.pop(0)

        self.img_processed = result_img
        self.last_op_name = op_name
        self.lbl_after.config(text=f"ẢNH SAU XỬ LÝ: {op_name.upper()}")
        self.refresh_image_panels()

        h, w = result_img.shape[:2]
        ch = 1 if len(result_img.shape) == 2 else result_img.shape[2]
        self.status_var.set(f"Thực hiện: {op_name} | Kích thước: {w}x{h} | Kênh: {ch}")

    def action_undo(self):
        if not self.history_stack:
            messagebox.showinfo("Hoàn tác", "Chưa có bước xử lý trước đó!")
            return
        prev_img, prev_op = self.history_stack.pop()
        self.img_processed = prev_img
        self.last_op_name = prev_op
        self.lbl_after.config(text=f"ẢNH SAU XỬ LÝ: {prev_op.upper()}")
        self.refresh_image_panels()
        self.status_var.set(f"Đã hoàn tác về: {prev_op}")

    # BƯỚC 1: XỬ LÝ ĐẦU VÀO
    def action_apply_gamma(self):
        src = self.img_processed if self.img_processed is not None else self.img_original
        if src is None:
            return
        g = float(self.gamma_var.get())
        res = mod1.apply_gamma_transform(src, gamma=g)
        self._update_result(res, f"Tăng sáng Gamma (γ={g:.2f})")

    def action_apply_hist_eq_color(self):
        src = self.img_processed if self.img_processed is not None else self.img_original
        if src is None:
            return
        res = mod1.apply_histogram_eq(src, keep_color=True)
        self._update_result(res, "Cân bằng sáng YCrCb")

    def action_apply_skin_smooth(self):
        src = self.img_processed if self.img_processed is not None else self.img_original
        if src is None:
            return
        d_val = int(self.smooth_d_var.get())
        res = mod2.smooth_and_clean_skin(src, d=d_val)
        self._update_result(res, f"Mịn da & Khử đốm (d={d_val})")

    # BƯỚC 2: CHỌN PHONG CÁCH TRANH VẼ
    def action_apply_sketch(self):
        src = self.img_processed if self.img_processed is not None else self.img_original
        if src is None:
            return
        style = self.sketch_style_var.get()
        k = int(self.sketch_ksize_var.get())
        if style == "pencil":
            res = mod3.apply_pencil_sketch(src, blur_ksize=k)
            self._update_result(res, f"Tranh phác thảo chì (k={k})")
        else:
            res = mod3.apply_sobel_sketch(src, ksize=k)
            self._update_result(res, f"Tranh nét viền Sobel (k={k})")

    # BƯỚC 3: QUY TRÌNH 1-CHẠM ALL-IN-ONE
    def action_one_click_all_in_one(self):
        if self.img_original is None:
            return
        g = float(self.gamma_var.get())
        d_val = int(self.smooth_d_var.get())
        style = self.sketch_style_var.get()
        k = int(self.sketch_ksize_var.get())

        # 1. Tăng sáng Gamma
        bright = mod1.apply_gamma_transform(self.img_original, gamma=g)
        # 2. Khử khuyết điểm da & Làm mịn giữ biên
        smoothed = mod2.smooth_and_clean_skin(bright, d=d_val)
        # 3. Chuyển thành tranh vẽ
        if style == "pencil":
            sketch = mod3.apply_pencil_sketch(smoothed, blur_ksize=k)
            label = f"1-Chạm: Sáng(γ={g:.2f}) + Mịn da + Tranh chì"
        else:
            sketch = mod3.apply_sobel_sketch(smoothed, ksize=k)
            label = f"1-Chạm: Sáng(γ={g:.2f}) + Mịn da + Nét viền Sobel"

        self._update_result(sketch, label)

    def action_show_histogram(self):
        if self.img_original is None or self.img_processed is None:
            messagebox.showwarning("Thông báo", "Cần có ảnh gốc và ảnh sau xử lý để vẽ Histogram!")
            return
        mod1.plot_histogram_comparison(
            self.img_original, self.img_processed, title_after=self.last_op_name
        )

    # =========================================================================
    # QUẢN LÝ ĐỌC/LƯU & HIỂN THỊ ẢNH
    # =========================================================================
    def _cv2_to_imagetk(self, img: np.ndarray, max_w: int, max_h: int) -> ImageTk.PhotoImage:
        if len(img.shape) == 2:
            rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        h, w = rgb.shape[:2]
        max_w = max(120, max_w - 12)
        max_h = max(120, max_h - 12)
        scale = min(max_w / w, max_h / h)
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))

        pil_img = Image.fromarray(rgb).resize((nw, nh), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(pil_img)

    def refresh_image_panels(self):
        w = self.panel_before.winfo_width()
        h = self.panel_before.winfo_height()
        if w <= 10 or h <= 10:
            w, h = 400, 450

        if self.img_original is not None:
            tk_b = self._cv2_to_imagetk(self.img_original, w, h)
            self.panel_before.config(image=tk_b)
            self.panel_before.image = tk_b

        if self.img_processed is not None:
            tk_a = self._cv2_to_imagetk(self.img_processed, w, h)
            self.panel_after.config(image=tk_a)
            self.panel_after.image = tk_a

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
            messagebox.showerror("Lỗi", "Không thể đọc tệp hình ảnh đã chọn!")
            return
        self.img_original = img
        self.img_processed = img.copy()
        self.history_stack.clear()
        self.last_op_name = "Ảnh gốc"
        self.lbl_after.config(text="ẢNH SAU XỬ LÝ: ẢNH GỐC")
        self.refresh_image_panels()
        self.status_var.set(f"Đã mở: {os.path.basename(file_path)}")

    def save_image(self):
        if self.img_processed is None:
            messagebox.showwarning("Thông báo", "Chưa có ảnh kết quả để lưu!")
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
            self._update_result(self.img_original.copy(), "Ảnh gốc")

    def load_demo_image(self):
        """Tạo ảnh chân dung đêm thiếu sáng và nhiễu hạt nhẹ để test ngay."""
        h, w = 420, 520
        y_grad = np.linspace(15, 65, h, dtype=np.float32)[:, None]
        x_grad = np.linspace(10, 45, w, dtype=np.float32)[None, :]
        b = np.clip(y_grad + x_grad * 0.4, 0, 255).astype(np.uint8)
        g = np.clip(y_grad * 0.8 + x_grad * 0.3, 0, 255).astype(np.uint8)
        r = np.clip(y_grad * 0.7 + x_grad * 0.2, 0, 255).astype(np.uint8)
        img = cv2.merge([b, g, r])

        # Trăng & cảnh nền
        cv2.circle(img, (420, 80), 40, (90, 110, 120), -1)
        cv2.rectangle(img, (30, 200), (130, 420), (25, 32, 42), -1)
        cv2.rectangle(img, (150, 160), (250, 420), (32, 40, 52), -1)

        # Chân dung người
        cv2.ellipse(img, (340, 255), (75, 95), 0, 0, 360, (62, 75, 95), -1)
        cv2.circle(img, (312, 235), 9, (20, 22, 28), -1)
        cv2.circle(img, (368, 235), 9, (20, 22, 28), -1)
        cv2.ellipse(img, (340, 290), (28, 14), 0, 0, 180, (35, 38, 65), 3)

        # Nhiễu hạt / mụn nhỏ giả lập
        rng = np.random.default_rng(42)
        mask = rng.random((h, w))
        img[mask < 0.008] = [170, 170, 170]
        img[mask > 0.992] = [8, 8, 8]

        self.img_original = img
        self.img_processed = img.copy()
        self.history_stack.clear()
        self.last_op_name = "Ảnh mẫu thiếu sáng (Demo)"
        self.lbl_after.config(text="ẢNH SAU XỬ LÝ: ẢNH MẪU (DEMO)")
        self.refresh_image_panels()
        self.status_var.set("Đã tải ảnh mẫu ban đêm (Demo).")


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEnhancerSketchApp(root)
    root.mainloop()
