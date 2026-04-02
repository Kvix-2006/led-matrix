import tkinter as tk
import tkinter.messagebox as messagebox

ROWS = 8
SIZE = 22
PREVIEW_SIZE = 8
MAX_COLS = 1024

class LedMatrix:

    def __init__(self, root):
        self.root = root
        self.root.title("LED Matrix Animator - Ultimate Mode FIXED (LED không mất)")

        self.cols = 32
        self.shift_mode = "wrap"

        self.frames = [self.empty_frame()]
        self.current = 0

        # ==================== Size Bar ====================
        sizebar = tk.Frame(root)
        sizebar.pack(pady=5)
        for c, text in [(12,"8x12"), (16,"8x16"), (24,"8x24"), (32,"8x32"), (64,"8x64")]:
            tk.Button(sizebar, text=text,
                      command=lambda cols=c: self.change_size(cols)).grid(row=0, column=len(sizebar.winfo_children()), padx=3)

        self.canvas = tk.Canvas(root, bg="#f0f0f0")
        self.canvas.pack(pady=8)
        self.led = []          # lưu id của từng oval

        # === Biến cho chức năng kéo chuột ===
        self.dragging = False
        self.drag_mode = 0     # 1 = bật LED (trái),  2 = tắt LED (phải)

        # Frame control
        framebar = tk.Frame(root)
        framebar.pack(pady=5)
        tk.Button(framebar, text="<<", command=self.prev_frame).grid(row=0, column=0, padx=3)
        tk.Button(framebar, text=">>", command=self.next_frame).grid(row=0, column=1, padx=3)
        tk.Button(framebar, text="Frame +", command=self.new_frame).grid(row=0, column=2, padx=3)
        tk.Button(framebar, text="Delete", command=self.delete_frame).grid(row=0, column=3, padx=3)
        self.frame_label = tk.Label(framebar, text="", font=("Arial", 10, "bold"))
        self.frame_label.grid(row=0, column=4, padx=15)

        # Shift Mode
        mode_frame = tk.Frame(root)
        mode_frame.pack(pady=5)
        tk.Label(mode_frame, text="Chế độ Shift:").pack(side="left", padx=8)
        self.mode_var = tk.StringVar(value="wrap")
        tk.Radiobutton(mode_frame, text="Wrap Around", variable=self.mode_var, value="wrap", command=self.update_mode).pack(side="left", padx=8)
        tk.Radiobutton(mode_frame, text="Ultimate", variable=self.mode_var, value="ultimate", command=self.update_mode).pack(side="left", padx=8)

        # Control buttons
        control_bar = tk.Frame(root)
        control_bar.pack(pady=8)
        tk.Button(control_bar, text="Xóa Tất Cả", bg="#ff6666", fg="white", width=12, command=self.clear_all).grid(row=0, column=0, padx=6)
        tk.Button(control_bar, text="Xóa Mã Hex", bg="#ffaa66", width=12, command=self.clear_export_text).grid(row=0, column=1, padx=6)
        tk.Button(control_bar, text="Copy Clipboard", bg="#66ccff", fg="black", width=14, command=self.copy_to_clipboard).grid(row=0, column=2, padx=6)

        # Preview
        self.preview_label = tk.Label(root, text="Xem lại các Frames (lăn chuột để cuộn):", font=("Arial", 10, "bold"))
        self.preview_label.pack(pady=(10,2))

        preview_container = tk.Frame(root)
        preview_container.pack(fill="x", padx=10)

        self.preview_scroll = tk.Canvas(preview_container, height=ROWS * PREVIEW_SIZE + 30, bg="#f8f8f8")
        self.preview_scroll.pack(side="left", fill="x", expand=True)

        h_scroll = tk.Scrollbar(preview_container, orient="horizontal", command=self.preview_scroll.xview)
        h_scroll.pack(side="bottom", fill="x")
        self.preview_scroll.configure(xscrollcommand=h_scroll.set)

        self.preview_inner = tk.Frame(self.preview_scroll)
        self.preview_scroll.create_window((0, 0), window=self.preview_inner, anchor="nw")

        self.preview_scroll.bind("<MouseWheel>", self.on_mouse_wheel)
        self.preview_scroll.bind("<Button-4>", self.on_mouse_wheel)
        self.preview_scroll.bind("<Button-5>", self.on_mouse_wheel)

        self.previews = []

        # Shift Buttons
        shift = tk.Frame(root)
        shift.pack(pady=10)
        tk.Button(shift, text="←", width=6, command=lambda: self.shift(-1, 0)).grid(row=0, column=0, padx=8)
        tk.Button(shift, text="→", width=6, command=lambda: self.shift(1, 0)).grid(row=0, column=1, padx=8)
        tk.Button(shift, text="↑", width=6, command=lambda: self.shift(0, -1)).grid(row=0, column=2, padx=8)
        tk.Button(shift, text="↓", width=6, command=lambda: self.shift(0, 1)).grid(row=0, column=3, padx=8)

        tk.Button(root, text="Clear Frame Hiện Tại", command=self.clear).pack(pady=5)
        tk.Button(root, text="Export ASM", command=self.export).pack(pady=5)

        self.text = tk.Text(root, height=9, font=("Consolas", 10))
        self.text.pack(fill="both", padx=10, pady=5)

        self.build_matrix()
        self.build_previews()

    def empty_frame(self):
        return [[0] * MAX_COLS for _ in range(ROWS)]

    def update_mode(self):
        self.shift_mode = self.mode_var.get()

    def change_size(self, new_cols):
        self.cols = new_cols
        self.frames = [self.empty_frame()]
        self.current = 0
        self.build_matrix()
        self.build_previews()

    # ====================== BUILD MATRIX - SỬ DỤNG CÁCH MỚI ======================
    def build_matrix(self):
        self.canvas.delete("all")
        self.canvas.config(width=self.cols * SIZE, height=ROWS * SIZE)

        self.led = []
        for r in range(ROWS):
            row = []
            for c in range(self.cols):
                x1 = c * SIZE
                y1 = r * SIZE
                x2 = x1 + SIZE
                y2 = y1 + SIZE
                obj = self.canvas.create_oval(x1, y1, x2, y2, fill="white", outline="gray")
                row.append(obj)
            self.led.append(row)

        # Bind sự kiện trên toàn Canvas (phương pháp ổn định hơn)
        self.canvas.bind("<ButtonPress-1>", self.start_drag_left)
        self.canvas.bind("<ButtonPress-3>", self.start_drag_right)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<B3-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        self.canvas.bind("<ButtonRelease-3>", self.end_drag)

        self.update_frame_label()
        self.draw()

    # ====================== KÉO CHUỘT - PHIÊN BẢN MỚI ======================
    def start_drag_left(self, event):
        self.dragging = True
        self.drag_mode = 1   # 1 = bật LED
        self.apply_drag(event)

    def start_drag_right(self, event):
        self.dragging = True
        self.drag_mode = 2   # 2 = tắt LED
        self.apply_drag(event)

    def on_drag(self, event):
        if self.dragging:
            self.apply_drag(event)

    def end_drag(self, event=None):
        self.dragging = False

    def apply_drag(self, event):
        # Lấy tọa độ chuột trên canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Tính toán vị trí LED
        col = int(x // SIZE)
        row = int(y // SIZE)

        if 0 <= row < ROWS and 0 <= col < self.cols:
            if self.drag_mode == 1:        # Chuột trái: bật LED
                self.frames[self.current][row][col] = 1
            else:                          # Chuột phải: tắt LED
                self.frames[self.current][row][col] = 0

            self.draw()
            self.update_previews()

    def toggle(self, r, c):   # vẫn giữ toggle click đơn (nếu cần)
        self.frames[self.current][r][c] ^= 1
        self.draw()
        self.update_previews()

    def draw(self):
        frame = self.frames[self.current]
        for r in range(ROWS):
            for c in range(self.cols):
                color = "lime" if frame[r][c] else "white"
                self.canvas.itemconfig(self.led[r][c], fill=color)

    # ====================== SHIFT ======================
    def shift(self, dx, dy):
        frame = self.frames[self.current]
        new = self.empty_frame()

        if self.shift_mode == "wrap":
            for r in range(ROWS):
                for c in range(self.cols):
                    nr = (r + dy) % ROWS
                    nc = (c + dx) % self.cols
                    new[nr][nc] = frame[r][c]
        else:
            for r in range(ROWS):
                for c in range(MAX_COLS):
                    nr = r + dy
                    nc = c + dx
                    if 0 <= nr < ROWS and 0 <= nc < MAX_COLS:
                        new[nr][nc] = frame[r][c]

        self.frames[self.current] = new
        self.draw()
        self.update_previews()

    def on_mouse_wheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.preview_scroll.xview_scroll(2, "units")
        elif event.num == 4 or event.delta > 0:
            self.preview_scroll.xview_scroll(-2, "units")

    # ====================== Phần còn lại giữ nguyên ======================
    def build_previews(self):
        for widget in self.preview_inner.winfo_children():
            widget.destroy()
        self.previews = []

        for idx in range(len(self.frames)):
            p_canvas = tk.Canvas(self.preview_inner, width=self.cols*PREVIEW_SIZE, height=ROWS*PREVIEW_SIZE,
                                 bg="#ffffff", highlightthickness=2, highlightbackground="#ddd")
            p_canvas.pack(side="left", padx=5, pady=5)

            p_leds = []
            for r in range(ROWS):
                row_leds = []
                for c in range(self.cols):
                    obj = p_canvas.create_oval(c*PREVIEW_SIZE, r*PREVIEW_SIZE,
                                               (c+1)*PREVIEW_SIZE, (r+1)*PREVIEW_SIZE,
                                               fill="white", outline="#bbbbbb")
                    row_leds.append(obj)
                p_leds.append(row_leds)
            self.previews.append((p_canvas, p_leds))
            p_canvas.bind("<Button-1>", lambda e, i=idx: self.switch_to_frame(i))

        self.update_previews()
        self.highlight_current_preview()
        self.preview_inner.update_idletasks()
        self.preview_scroll.configure(scrollregion=self.preview_scroll.bbox("all"))

    def update_previews(self):
        for i, (p_canvas, p_leds) in enumerate(self.previews):
            frame = self.frames[i]
            for r in range(ROWS):
                for c in range(self.cols):
                    color = "lime" if frame[r][c] else "white"
                    p_canvas.itemconfig(p_leds[r][c], fill=color)

    def highlight_current_preview(self):
        for i, (p_canvas, _) in enumerate(self.previews):
            if i == self.current:
                p_canvas.config(highlightthickness=4, highlightbackground="#00aa00")
            else:
                p_canvas.config(highlightthickness=2, highlightbackground="#dddddd")

    def switch_to_frame(self, idx):
        if 0 <= idx < len(self.frames):
            self.current = idx
            self.update_frame_label()
            self.draw()
            self.highlight_current_preview()

    def new_frame(self):
        new = [row[:] for row in self.frames[self.current]]
        self.frames.append(new)
        self.current = len(self.frames) - 1
        self.update_frame_label()
        self.draw()
        self.build_previews()

    def delete_frame(self):
        if len(self.frames) > 1:
            self.frames.pop(self.current)
            self.current = max(0, self.current - 1)
        self.update_frame_label()
        self.draw()
        self.build_previews()

    def next_frame(self):
        if self.current < len(self.frames) - 1:
            self.current += 1
            self.update_frame_label()
            self.draw()
            self.highlight_current_preview()

    def prev_frame(self):
        if self.current > 0:
            self.current -= 1
            self.update_frame_label()
            self.draw()
            self.highlight_current_preview()

    def update_frame_label(self):
        self.frame_label.config(text=f"Frame {self.current+1} / {len(self.frames)}")

    def clear(self):
        self.frames[self.current] = self.empty_frame()
        self.draw()
        self.update_previews()

    def clear_all(self):
        if messagebox.askyesno("Xác nhận", "Xóa TẤT CẢ frames và LED?"):
            self.frames = [self.empty_frame()]
            self.current = 0
            self.build_matrix()
            self.build_previews()
            self.text.delete("1.0", tk.END)

    def clear_export_text(self):
        self.text.delete("1.0", tk.END)

    def copy_to_clipboard(self):
        content = self.text.get("1.0", tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Thành công", "Đã copy mã ASM vào clipboard!")
        else:
            messagebox.showwarning("Cảnh báo", "Chưa có mã để copy!")

    def export(self):
        output = []
        for frame in self.frames:
            result = []
            for c in range(self.cols):
                value = 0xFF
                for r in range(ROWS):
                    if frame[r][c]:
                        value &= ~(1 << r)
                result.append("0H" if value == 0 else f"0{value:02X}H")
            output.append("DB " + ",".join(result))

        text = "\n".join(output)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text)


root = tk.Tk()
LedMatrix(root)
root.mainloop()