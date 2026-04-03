import tkinter as tk
from tkinter import messagebox, simpledialog
import copy

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

class LedMatrixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Led Matrix v18.0 - Frame Navigator (Jump to Frame)")
        self.root.configure(bg="#f0f0f0")
        
        self.cols = 32
        self.rows = 16
        self.cell_size = 18
        
        self.frames = [self.create_empty_grid(self.cols, self.rows)]
        self.current_frame_idx = 0
        self.grid_data = self.frames[0] 
        
        self.library = [] 
        self.scroller_raw_data = None 
        
        self.selection = None 
        self.sel_start_coords = None
        self.current_draw_mode = 1 
        
        # --- UNDO / REDO ---
        self.history = []
        self.redo_stack = []
        
        # --- PLAYBACK ---
        self.is_playing = False
        
        self.setup_ui()
        self.draw_grid()
        self.update_frame_lbl()
        self.save_state()

        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())

    def create_empty_grid(self, c, r):
        return [[0 for _ in range(c)] for _ in range(r)]

    def setup_ui(self):
        # --- TOP CONTROL ---
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(pady=5)
        tk.Label(top_frame, text="Số Cột:", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5)
        self.size_var = tk.IntVar(value=32)
        for i, val in enumerate([8, 16, 32]):
            tk.Radiobutton(top_frame, text=str(val), variable=self.size_var, value=val, command=self.update_dimensions, bg="#f0f0f0").grid(row=0, column=i+1)

        tk.Label(top_frame, text=" | Số Hàng:", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=0, column=4, padx=5)
        self.rows_var = tk.IntVar(value=16)
        tk.Radiobutton(top_frame, text="8", variable=self.rows_var, value=8, command=self.update_dimensions, bg="#f0f0f0").grid(row=0, column=5)
        tk.Radiobutton(top_frame, text="16", variable=self.rows_var, value=16, command=self.update_dimensions, bg="#f0f0f0").grid(row=0, column=6)

        # --- CANVAS ---
        self.canvas_frame = tk.Frame(self.root, bg="#222", bd=5, relief=tk.SUNKEN)
        self.canvas_frame.pack(pady=5, padx=10)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#111", highlightthickness=0)
        self.canvas.pack()
        
        self.canvas.bind("<ButtonPress-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)

        # --- THƯ VIỆN & CODE ---
        mid_frame = tk.Frame(self.root, bg="#f0f0f0")
        mid_frame.pack(fill=tk.X, padx=10)

        self.lib_listbox = tk.Listbox(mid_frame, height=8, width=22)
        self.lib_listbox.pack(side=tk.LEFT, padx=5)
        
        lib_btn_frame = tk.Frame(mid_frame, bg="#f0f0f0")
        lib_btn_frame.pack(side=tk.LEFT)
        tk.Button(lib_btn_frame, text="🔠 TẠO CHỮ TỰ ĐỘNG", command=self.create_text_component, width=28, bg="#e2e3e5", font=("Arial", 8, "bold")).pack(pady=1)
        tk.Button(lib_btn_frame, text="Lưu Vùng Chọn vào Thư viện", command=self.add_to_library, width=28, font=("Arial", 8)).pack(pady=1)
        tk.Button(lib_btn_frame, text="Chèn Hình đã chọn vào Lưới", command=self.insert_from_library, width=28, bg="#d9edf7").pack(pady=1)
        tk.Button(lib_btn_frame, text="⚡ GHÉP NỐI & TẠO CHỮ CHẠY", command=self.generate_scroller, width=28, bg="#ffeb3b", font=("Arial", 8, "bold")).pack(pady=2)

        self.code_output = tk.Text(mid_frame, height=8, width=54, font=("Courier New", 9))
        self.code_output.pack(side=tk.RIGHT, padx=5)

        # --- CONTROL PANEL ---
        ctrl_frame = tk.Frame(self.root, bg="#f0f0f0")
        ctrl_frame.pack(pady=10)

        # 1. Công cụ & Undo
        f1 = tk.LabelFrame(ctrl_frame, text="1. Công cụ", padx=5, pady=2, bg="#f0f0f0")
        f1.grid(row=0, column=0, padx=3, sticky="n")
        self.tool_mode = tk.StringVar(value="draw")
        tk.Radiobutton(f1, text="Bút vẽ", variable=self.tool_mode, value="draw", bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(f1, text="Chọn vùng", variable=self.tool_mode, value="select", bg="#f0f0f0").pack(anchor="w")
        
        undo_f = tk.Frame(f1, bg="#f0f0f0")
        undo_f.pack(pady=2)
        tk.Button(undo_f, text="↩ Undo", command=self.undo, width=5).pack(side=tk.LEFT, padx=1)
        tk.Button(undo_f, text="Redo ↪", command=self.redo, width=5).pack(side=tk.LEFT, padx=1)
        
        tk.Button(f1, text="Xóa lưới", command=self.clear_current_grid, width=12).pack(pady=1)
        tk.Button(f1, text="RESET ALL", command=self.reset_all, fg="white", bg="#d9534f", width=12).pack(pady=1)

        # 2. Frames & Playback (CẬP NHẬT CHỌN FRAME TẠI ĐÂY)
        f2 = tk.LabelFrame(ctrl_frame, text="2. Xem trước & Play", padx=5, pady=2, bg="#f0f0f0")
        f2.grid(row=0, column=1, padx=3, sticky="n")
        
        info_f = tk.Frame(f2, bg="#f0f0f0")
        info_f.pack(pady=2)
        tk.Label(info_f, text="F:", bg="#f0f0f0", font=("Arial", 9, "bold"), fg="blue").pack(side=tk.LEFT)
        
        self.frame_var = tk.StringVar(value="1")
        self.frame_entry = tk.Entry(info_f, textvariable=self.frame_var, width=4, justify="center", font=("Arial", 9, "bold"))
        self.frame_entry.pack(side=tk.LEFT, padx=2)
        self.frame_entry.bind("<Return>", self.jump_to_frame) # Ấn Enter để nhảy
        
        self.lbl_total_frames = tk.Label(info_f, text="/ 1", bg="#f0f0f0", font=("Arial", 8, "bold"), fg="blue")
        self.lbl_total_frames.pack(side=tk.LEFT)
        tk.Button(info_f, text="Đến", command=self.jump_to_frame, font=("Arial", 7)).pack(side=tk.LEFT, padx=2)

        nav_f = tk.Frame(f2, bg="#f0f0f0")
        nav_f.pack()
        tk.Button(nav_f, text="◄", command=self.prev_frame, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(nav_f, text="►", command=self.next_frame, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(nav_f, text="Copy", command=self.add_copy_frame, width=4).pack(side=tk.LEFT, padx=1)
        
        play_f = tk.Frame(f2, bg="#f0f0f0")
        play_f.pack(pady=2)
        self.btn_play = tk.Button(play_f, text="▶ Play", command=self.toggle_play, bg="#5cb85c", fg="white", width=6)
        self.btn_play.pack(side=tk.LEFT, padx=1)
        tk.Button(play_f, text="Del F", command=self.delete_frame, fg="red", width=4).pack(side=tk.LEFT, padx=1)
        
        self.speed_var = tk.IntVar(value=100)
        tk.Scale(f2, from_=20, to=500, orient=tk.HORIZONTAL, variable=self.speed_var, length=100, showvalue=0, bg="#f0f0f0").pack()
        tk.Label(f2, text="Tốc độ (20-500ms)", font=("Arial", 7), bg="#f0f0f0").pack()

        # 3. Dịch chuyển
        f3 = tk.LabelFrame(ctrl_frame, text="3. Dịch chuyển", padx=5, pady=2, bg="#f0f0f0")
        f3.grid(row=0, column=2, padx=3, sticky="n")
        man_f = tk.Frame(f3, bg="#f0f0f0")
        man_f.pack()
        tk.Button(man_f, text="↑", command=lambda: self.shift_logic(0, -1), width=2).grid(row=0, column=1)
        tk.Button(man_f, text="←", command=lambda: self.shift_logic(-1, 0), width=2).grid(row=1, column=0)
        tk.Button(man_f, text="→", command=lambda: self.shift_logic(1, 0), width=2).grid(row=1, column=2)
        tk.Button(man_f, text="↓", command=lambda: self.shift_logic(0, 1), width=2).grid(row=2, column=1)
        
        auto_f = tk.Frame(f3, bg="#f0f0f0")
        auto_f.pack(pady=3)
        tk.Label(auto_f, text="Auto:", bg="#f0f0f0", font=("Arial", 7)).pack(side=tk.LEFT)
        self.auto_steps_var = tk.StringVar(value="32")
        tk.Entry(auto_f, textvariable=self.auto_steps_var, width=3).pack(side=tk.LEFT)
        tk.Label(auto_f, text="ô", bg="#f0f0f0", font=("Arial", 7)).pack(side=tk.LEFT)
        auto_btn_f = tk.Frame(f3, bg="#f0f0f0")
        auto_btn_f.pack()
        tk.Button(auto_btn_f, text="←", command=lambda: self.auto_shift(-1, 0), width=3, bg="#ffeb3b").pack(side=tk.LEFT, padx=1)
        tk.Button(auto_btn_f, text="→", command=lambda: self.auto_shift(1, 0), width=3, bg="#ffeb3b").pack(side=tk.LEFT, padx=1)

        # 4. Hiệu ứng (Wipe + Loop)
        f_eff = tk.LabelFrame(ctrl_frame, text="4. Wipe In/Out", padx=5, pady=2, bg="#f0f0f0")
        f_eff.grid(row=0, column=3, padx=3, sticky="n")
        
        loop_f = tk.Frame(f_eff, bg="#f0f0f0")
        loop_f.pack(pady=1)
        tk.Label(loop_f, text="Lặp:", font=("Arial", 8, "bold"), bg="#f0f0f0").pack(side=tk.LEFT)
        self.wipe_loop_var = tk.StringVar(value="1")
        tk.Entry(loop_f, textvariable=self.wipe_loop_var, width=3, justify="center").pack(side=tk.LEFT)
        tk.Label(loop_f, text="lần", font=("Arial", 8), bg="#f0f0f0").pack(side=tk.LEFT)

        w_out = tk.Frame(f_eff, bg="#f0f0f0")
        w_out.pack()
        tk.Label(w_out, text="Tắt:", fg="#d9534f", font=("Arial", 7, "bold"), bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Button(w_out, text="L→R", command=lambda: self.auto_wipe('col_lr'), width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(w_out, text="R→L", command=lambda: self.auto_wipe('col_rl'), width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(w_out, text="T→B", command=lambda: self.auto_wipe('row_tb'), width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        
        w_in = tk.Frame(f_eff, bg="#f0f0f0")
        w_in.pack(pady=2)
        tk.Label(w_in, text="Hiện:", fg="#5cb85c", font=("Arial", 7, "bold"), bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Button(w_in, text="L→R", command=lambda: self.auto_reveal('col_lr'), width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(w_in, text="R→L", command=lambda: self.auto_reveal('col_rl'), width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(w_in, text="T→B", command=lambda: self.auto_reveal('row_tb'), width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        # 5. Xuất mã 
        f4 = tk.LabelFrame(ctrl_frame, text="5. Xuất mã", padx=5, pady=2, bg="#f0f0f0")
        f4.grid(row=0, column=4, padx=3, sticky="n")
        
        self.polarity_var = tk.StringVar(value="cathode")
        tk.Radiobutton(f4, text="Cathode", variable=self.polarity_var, value="cathode", font=("Arial", 7), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(f4, text="Anode", variable=self.polarity_var, value="anode", font=("Arial", 7), bg="#f0f0f0").grid(row=0, column=1, sticky="w")
        
        self.format_var = tk.StringVar(value="hex")
        tk.Radiobutton(f4, text="C/C++ HEX", variable=self.format_var, value="hex", font=("Arial", 7, "bold"), fg="blue", bg="#f0f0f0").grid(row=1, column=0, sticky="w")
        tk.Radiobutton(f4, text="ASM", variable=self.format_var, value="asm", font=("Arial", 7), fg="blue", bg="#f0f0f0").grid(row=1, column=1, sticky="w")
        
        tk.Button(f4, text="MẢNG DÀI", command=self.generate_optimized_asm, bg="#5bc0de", fg="black", font=("Arial", 8, "bold")).grid(row=2, column=0, columnspan=2, sticky="we", pady=2)
        tk.Button(f4, text="TỪNG FRAME", command=self.generate_asm, bg="#ccc", fg="black", font=("Arial", 7)).grid(row=3, column=0, columnspan=2, sticky="we", pady=2)

    # --- UNDO / REDO ---
    def save_state(self):
        state = {
            'frames': copy.deepcopy(self.frames),
            'idx': self.current_frame_idx,
            'lib': copy.deepcopy(self.library)
        }
        self.history.append(state)
        if len(self.history) > 20: self.history.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if len(self.history) > 1:
            self.redo_stack.append(self.history.pop())
            last_state = self.history[-1]
            self.frames = copy.deepcopy(last_state['frames'])
            self.current_frame_idx = last_state['idx']
            self.library = copy.deepcopy(last_state['lib'])
            self.grid_data = self.frames[self.current_frame_idx]
            self.refresh_library_list()
            self.draw_grid()
            self.update_frame_lbl()

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.history.append(state)
            self.frames = copy.deepcopy(state['frames'])
            self.current_frame_idx = state['idx']
            self.library = copy.deepcopy(state['lib'])
            self.grid_data = self.frames[self.current_frame_idx]
            self.refresh_library_list()
            self.draw_grid()
            self.update_frame_lbl()

    # --- JUMP TO FRAME (CHỌN FRAME MUỐN XEM) ---
    def jump_to_frame(self, event=None):
        try:
            target = int(self.frame_var.get()) - 1
            if 0 <= target < len(self.frames):
                self.current_frame_idx = target
                self.grid_data = self.frames[self.current_frame_idx]
                self.clear_selection()
                self.draw_grid()
            else:
                messagebox.showwarning("Lỗi", f"Vui lòng nhập số Frame từ 1 đến {len(self.frames)}")
        except ValueError:
            messagebox.showwarning("Lỗi", "Vui lòng nhập số nguyên hợp lệ!")
        finally:
            self.update_frame_lbl() # Reset lại ô nhập liệu cho đúng

    # --- AUTO PLAYBACK ---
    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.config(text="⏸ Pause", bg="orange")
            self.play_loop()
        else:
            self.btn_play.config(text="▶ Play", bg="#5cb85c")

    def play_loop(self):
        if self.is_playing:
            if self.current_frame_idx < len(self.frames) - 1:
                self.current_frame_idx += 1
            else:
                self.current_frame_idx = 0 
            
            self.grid_data = self.frames[self.current_frame_idx]
            self.draw_grid()
            self.update_frame_lbl()
            
            speed = self.speed_var.get()
            self.root.after(speed, self.play_loop)

    # --- TEXT TOOL ---
    def create_text_component(self):
        if not HAS_PILLOW:
            messagebox.showerror("Thiếu", "Gõ lệnh: pip install pillow\nRồi khởi động lại app.")
            return

        text = simpledialog.askstring("Tạo chữ", "Nhập nội dung:")
        if not text: return
        
        try:
            try: font = ImageFont.truetype("arial.ttf", 15)
            except IOError: font = ImageFont.load_default()

            dummy_img = Image.new('L', (1, 1))
            draw = ImageDraw.Draw(dummy_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            img = Image.new('L', (w + 2, h + 2), color=255)
            draw = ImageDraw.Draw(img)
            draw.text((1, 1), text, font=font, fill=0)

            shape = []
            for r in range(img.height):
                row_data = []
                for c in range(img.width):
                    row_data.append(1 if img.getpixel((c, r)) < 128 else 0)
                shape.append(row_data)

            self.library.append({"name": f"TXT: {text}", "data": shape, "offset_r": 0})
            self.refresh_library_list()
            self.save_state()
            messagebox.showinfo("Thành công", f"Đã lưu chữ '{text}' vào thư viện.")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi: {e}")

    def refresh_library_list(self):
        self.lib_listbox.delete(0, tk.END)
        for item in self.library:
            self.lib_listbox.insert(tk.END, item["name"])

    # --- SỰ KIỆN CŨ ---
    def add_to_library(self):
        if not self.selection: return
        c1, r1, c2, r2 = self.selection
        name = simpledialog.askstring("Thư viện", "Đặt tên (VD: BẢO LÂM):")
        if not name: return
        shape = [[self.grid_data[r][c] for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]
        self.library.append({"name": name, "data": shape, "offset_r": r1})
        self.refresh_library_list()
        self.clear_selection()
        self.save_state()

    def insert_from_library(self):
        idx = self.lib_listbox.curselection()
        if not idx: return
        shape = self.library[idx[0]]["data"]
        offset_r = self.library[idx[0]]["offset_r"]
        offset_c = simpledialog.askinteger("Chèn hình", "Cột thứ mấy (0-31):", initialvalue=0)
        if offset_c is None: return

        for r in range(len(shape)):
            for c in range(len(shape[0])):
                tr, tc = offset_r + r, offset_c + c
                if 0 <= tr < self.rows and 0 <= tc < self.cols:
                    self.grid_data[tr][tc] = shape[r][c]
        self.draw_grid()
        self.save_state()

    def generate_scroller(self):
        if len(self.library) == 0: return
        gap = simpledialog.askinteger("Khoảng cách", "Khoảng trống (VD: 3):", initialvalue=3)
        if gap is None: return

        cropped_items = []
        for item in self.library:
            shape = item["data"]
            min_c, max_c = len(shape[0]), -1
            for r in range(len(shape)):
                for c in range(len(shape[0])):
                    if shape[r][c] == 1:
                        min_c = min(min_c, c)
                        max_c = max(max_c, c)
            if max_c == -1: continue 
            cropped = [[shape[r][c] for c in range(min_c, max_c + 1)] for r in range(len(shape))]
            cropped_items.append({"data": cropped, "offset_r": item["offset_r"]})

        long_grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for idx, item in enumerate(cropped_items):
            data, off_r = item["data"], item["offset_r"]
            w, h = len(data[0]), len(data)
            current_len = len(long_grid[0])
            for r in range(self.rows): long_grid[r].extend([0] * w)
            for r in range(h):
                if 0 <= off_r + r < self.rows:
                    for c in range(w): long_grid[off_r + r][current_len + c] = data[r][c]
            if idx < len(cropped_items) - 1:
                for r in range(self.rows): long_grid[r].extend([0] * gap)
        for r in range(self.rows): long_grid[r].extend([0] * self.cols)

        self.scroller_raw_data = long_grid
        self.frames = []
        total_cols = len(long_grid[0])
        for i in range(total_cols - self.cols + 1):
            new_frame = []
            for r in range(self.rows): new_frame.append(long_grid[r][i : i+self.cols])
            self.frames.append(new_frame)

        self.current_frame_idx = 0
        self.grid_data = self.frames[0]
        self.clear_selection()
        self.draw_grid()
        self.update_frame_lbl()
        self.save_state()
        self.generate_optimized_asm()

    def shift_logic(self, dc, dr, draw=True):
        c_min, r_min, c_max, r_max = self.selection if self.selection else (0, 0, self.cols-1, self.rows-1)
        temp = {}
        for r in range(r_min, r_max+1):
            for c in range(c_min, c_max+1):
                temp[(r,c)] = self.grid_data[r][c]
                self.grid_data[r][c] = 0
        for (r,c), v in temp.items():
            nr, nc = r+dr, c+dc
            if r_min <= nr <= r_max and c_min <= nc <= c_max: self.grid_data[nr][nc] = v
        if draw: 
            self.draw_grid()
            self.save_state()

    def auto_shift(self, dc, dr):
        try: steps = int(self.auto_steps_var.get())
        except ValueError: return
        if steps <= 0: return
        for _ in range(steps):
            new_frame = copy.deepcopy(self.grid_data)
            self.current_frame_idx += 1
            self.frames.insert(self.current_frame_idx, new_frame)
            self.grid_data = self.frames[self.current_frame_idx]
            self.shift_logic(dc, dr, draw=False)
        self.draw_grid()
        self.update_frame_lbl()
        self.save_state()

    def auto_wipe(self, mode):
        steps = self.cols if mode.startswith('col') else self.rows
        try: loops = int(self.wipe_loop_var.get())
        except: loops = 1
        base_frame = copy.deepcopy(self.grid_data)
        for _ in range(loops):
            for step in range(steps):
                new_frame = copy.deepcopy(base_frame)
                if mode == 'col_lr':
                    for r in range(self.rows): 
                        for c in range(step + 1): new_frame[r][c] = 0
                elif mode == 'col_rl':
                    for r in range(self.rows): 
                        for c in range(self.cols - 1 - step, self.cols): new_frame[r][c] = 0
                elif mode == 'row_tb':
                    for c in range(self.cols): 
                        for r in range(step + 1): new_frame[r][c] = 0
                self.current_frame_idx += 1
                self.frames.insert(self.current_frame_idx, new_frame)
        self.grid_data = self.frames[self.current_frame_idx]
        self.draw_grid()
        self.update_frame_lbl()
        self.save_state()

    def auto_reveal(self, mode):
        steps = self.cols if mode.startswith('col') else self.rows
        try: loops = int(self.wipe_loop_var.get())
        except: loops = 1
        target_frame = copy.deepcopy(self.grid_data)
        for _ in range(loops):
            for step in range(steps):
                progressive_frame = self.create_empty_grid(self.cols, self.rows)
                if mode == 'col_lr':
                    for r in range(self.rows):
                        for c in range(step + 1): progressive_frame[r][c] = target_frame[r][c]
                elif mode == 'col_rl':
                    for r in range(self.rows):
                        for c in range(self.cols - 1 - step, self.cols): progressive_frame[r][c] = target_frame[r][c]
                elif mode == 'row_tb':
                    for c in range(self.cols):
                        for r in range(step + 1): progressive_frame[r][c] = target_frame[r][c]
                self.current_frame_idx += 1
                self.frames.insert(self.current_frame_idx, progressive_frame)
        self.grid_data = self.frames[self.current_frame_idx]
        self.draw_grid()
        self.update_frame_lbl()
        self.save_state()

    def on_left_click(self, event):
        c, r = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= c < self.cols and 0 <= r < self.rows:
            if self.tool_mode.get() == "draw":
                self.current_draw_mode = 0 if self.grid_data[r][c] == 1 else 1
                self.update_cell(r, c, self.current_draw_mode)
            else:
                self.sel_start_coords = (event.x, event.y)
                self.clear_selection()

    def on_left_drag(self, event):
        c, r = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= c < self.cols and 0 <= r < self.rows:
            if self.tool_mode.get() == "draw":
                self.update_cell(r, c, self.current_draw_mode)
            elif self.sel_start_coords:
                self.canvas.delete("sel_temp")
                self.canvas.create_rectangle(self.sel_start_coords[0], self.sel_start_coords[1], event.x, event.y, outline="#00ffff", dash=(4,4), tags="sel_temp")

    def on_left_release(self, event):
        if self.tool_mode.get() == "select" and self.sel_start_coords:
            c1, r1 = self.sel_start_coords[0] // self.cell_size, self.sel_start_coords[1] // self.cell_size
            c2, r2 = event.x // self.cell_size, event.y // self.cell_size
            self.selection = (max(0, min(c1, c2)), max(0, min(r1, r2)), min(self.cols-1, max(c1, c2)), min(self.rows-1, max(r1, r2)))
            self.draw_grid()
        self.save_state() 

    def update_cell(self, r, c, val):
        if self.grid_data[r][c] != val:
            self.grid_data[r][c] = val
            color = "#00ff00" if val == 1 else "#333333"
            self.canvas.itemconfig(f"c_{r}_{c}", fill=color)

    def draw_grid(self):
        cw, ch = self.cols * self.cell_size, self.rows * self.cell_size
        self.canvas.config(width=cw, height=ch)
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = c*self.cell_size, r*self.cell_size
                x2, y2 = x1+self.cell_size, y1+self.cell_size
                color = "#00ff00" if self.grid_data[r][c] == 1 else "#333333"
                self.canvas.create_oval(x1+2, y1+2, x2-2, y2-2, fill=color, outline="#222", tags=f"c_{r}_{c}")
        if self.selection:
            c1, r1, c2, r2 = self.selection
            self.canvas.create_rectangle(c1*self.cell_size, r1*self.cell_size, (c2+1)*self.cell_size, (r2+1)*self.cell_size, outline="#00ffff", width=2, dash=(4,4))

    def update_dimensions(self):
        self.cols, self.rows = self.size_var.get(), self.rows_var.get()
        self.frames = [self.create_empty_grid(self.cols, self.rows)]
        self.current_frame_idx = 0
        self.grid_data = self.frames[0]
        self.draw_grid()
        self.update_frame_lbl()
        self.save_state()

    def clear_current_grid(self):
        self.grid_data = self.create_empty_grid(self.cols, self.rows)
        self.frames[self.current_frame_idx] = self.grid_data
        self.draw_grid()
        self.save_state()

    def clear_selection(self): self.selection = None; self.draw_grid()
    def prev_frame(self):
        if self.current_frame_idx > 0: self.current_frame_idx -= 1; self.grid_data = self.frames[self.current_frame_idx]; self.draw_grid(); self.update_frame_lbl()
    def next_frame(self):
        if self.current_frame_idx < len(self.frames)-1: self.current_frame_idx += 1; self.grid_data = self.frames[self.current_frame_idx]; self.draw_grid(); self.update_frame_lbl()
    def add_copy_frame(self):
        self.frames.insert(self.current_frame_idx+1, copy.deepcopy(self.grid_data)); self.next_frame(); self.save_state()
    def delete_frame(self):
        if len(self.frames) > 1: self.frames.pop(self.current_frame_idx); self.current_frame_idx = min(self.current_frame_idx, len(self.frames)-1); self.grid_data = self.frames[self.current_frame_idx]; self.draw_grid(); self.update_frame_lbl(); self.save_state()
    
    # CẬP NHẬT LABEL ĐỂ ĐỒNG BỘ VỚI Ô NHẬP LIỆU
    def update_frame_lbl(self): 
        self.frame_var.set(str(self.current_frame_idx + 1))
        self.lbl_total_frames.config(text=f"/ {len(self.frames)}")
        
    def reset_all(self): 
        if messagebox.askyesno("Cảnh báo", "Reset tất cả về ban đầu?"):
            self.update_dimensions(); self.code_output.delete(1.0, tk.END)
            self.library.clear(); self.lib_listbox.delete(0, tk.END)
            self.scroller_raw_data = None
            self.save_state()

    def generate_optimized_asm(self):
        if not self.scroller_raw_data: return
        self.code_output.delete(1.0, tk.END)
        is_anode = (self.polarity_var.get() == "anode")
        is_asm = (self.format_var.get() == "asm")
        total_cols = len(self.scroller_raw_data[0])
        asm_lines = []
        for c in range(total_cols):
            b1, b2 = 0, 0
            for r in range(8): 
                if self.scroller_raw_data[r][c]: b1 |= (1 << r)
            if self.rows == 16:
                for r in range(8, 16): 
                    if self.scroller_raw_data[r][c]: b2 |= (1 << (r-8))
            if is_anode: 
                b1 ^= 0xFF
                b2 ^= 0xFF
            asm_lines.append(f"0x{b1:02X}")
            if self.rows == 16: asm_lines.append(f"0x{b2:02X}")

        cmt = ";" if is_asm else "//"
        res = f"{cmt} === MẢNG DỮ LIỆU TỐI ƯU ({total_cols} cột x {self.rows} hàng) ===\n"
        if not is_asm: res += "const unsigned char scroll_data[] = {\n"
        step = 8 if self.rows == 8 else 16
        for i in range(0, len(asm_lines), step):
            chunk = asm_lines[i:i+step]
            res += ("    DB " if is_asm else "    ") + ", ".join(chunk) + ("\n" if is_asm else ",\n")
        if not is_asm: res += "};\n"
        self.code_output.insert(tk.END, res)

    def generate_asm(self):
        self.code_output.delete(1.0, tk.END)
        is_anode = (self.polarity_var.get() == "anode")
        is_asm = (self.format_var.get() == "asm")
        res = ""
        for i, f in enumerate(self.frames):
            res += f"; ====== FRAME {i+1} ======\n" if is_asm else f"// ====== FRAME {i+1} ======\n{{\n"
            asm_lines = []
            for c in range(self.cols):
                b1, b2 = 0, 0
                for r in range(8): 
                    if f[r][c]: b1 |= (1 << r)
                if self.rows == 16:
                    for r in range(8, 16): 
                        if f[r][c]: b2 |= (1 << (r-8))
                if is_anode: b1 ^= 0xFF; b2 ^= 0xFF
                asm_lines.append(f"0x{b1:02X}")
                if self.rows == 16: asm_lines.append(f"0x{b2:02X}")

            step = 8 if self.rows == 8 else 16
            for idx in range(0, len(asm_lines), step):
                chunk = asm_lines[idx:idx+step]
                res += ("    DB " if is_asm else "    ") + ", ".join(chunk) + ("\n" if is_asm else ",\n")
            res += "\n" if is_asm else "},\n"
        self.code_output.insert(tk.END, res)

if __name__ == "__main__":
    root = tk.Tk()
    app = LedMatrixApp(root)
    root.mainloop()