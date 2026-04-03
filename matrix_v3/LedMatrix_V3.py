import tkinter as tk
from tkinter import messagebox
import copy

class LedMatrixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Led Matrix v11.0 - Full Animation Effects")
        self.root.configure(bg="#f0f0f0")
        
        # Cấu hình mặc định
        self.cols = 32
        self.rows = 16
        self.cell_size = 20
        
        # Quản lý Animation (Frames)
        self.frames = [self.create_empty_grid()]
        self.current_frame_idx = 0
        self.grid_data = self.frames[0] 
        
        # Trạng thái điều khiển chuột
        self.selection = None 
        self.sel_start_coords = None
        self.current_draw_mode = 1 
        
        self.setup_ui()
        self.draw_grid()
        self.update_frame_lbl()

    def create_empty_grid(self):
        return [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    def setup_ui(self):
        # --- KHU VỰC CÀI ĐẶT KÍCH THƯỚC ---
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(pady=5)
        
        tk.Label(top_frame, text="Số Cột:", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5)
        self.size_var = tk.IntVar(value=32)
        for i, val in enumerate([8, 16, 32]):
            tk.Radiobutton(top_frame, text=str(val), variable=self.size_var, value=val, 
                           command=self.update_dimensions, bg="#f0f0f0").grid(row=0, column=i+1)

        tk.Label(top_frame, text=" |  Số Hàng:", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=0, column=4, padx=5)
        self.rows_var = tk.IntVar(value=16)
        tk.Radiobutton(top_frame, text="8", variable=self.rows_var, value=8, 
                       command=self.update_dimensions, bg="#f0f0f0").grid(row=0, column=5)
        tk.Radiobutton(top_frame, text="16", variable=self.rows_var, value=16, 
                       command=self.update_dimensions, bg="#f0f0f0").grid(row=0, column=6)

        # --- VÙNG VẼ MA TRẬN ---
        self.canvas_frame = tk.Frame(self.root, bg="#222", bd=5, relief=tk.SUNKEN)
        self.canvas_frame.pack(pady=5, padx=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#111", highlightthickness=0)
        self.canvas.pack()
        
        self.canvas.bind("<ButtonPress-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)

        # --- KHU VỰC HIỂN THỊ CODE ---
        code_frame = tk.Frame(self.root, bg="#f0f0f0")
        code_frame.pack(padx=10, pady=5)
        self.code_output = tk.Text(code_frame, height=8, width=95, font=("Courier New", 10), bg="#fafafa")
        self.code_output.pack(side=tk.LEFT)
        
        scrollbar = tk.Scrollbar(code_frame, command=self.code_output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_output.config(yscrollcommand=scrollbar.set)

        # --- KHU VỰC ĐIỀU KHIỂN CHÍNH ---
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(pady=5)

        # 1. Công cụ chuột
        tool_frame = tk.LabelFrame(control_frame, text="1. Công cụ", padx=5, pady=2, bg="#f0f0f0")
        tool_frame.grid(row=0, column=0, padx=5, sticky="n")
        self.tool_mode = tk.StringVar(value="draw")
        tk.Radiobutton(tool_frame, text="Bút / Xóa", variable=self.tool_mode, value="draw", bg="#f0f0f0").pack(anchor=tk.W)
        tk.Radiobutton(tool_frame, text="Chọn vùng", variable=self.tool_mode, value="select", bg="#f0f0f0").pack(anchor=tk.W)
        tk.Button(tool_frame, text="Hủy chọn", command=self.clear_selection, width=12).pack(pady=1)
        tk.Button(tool_frame, text="Xóa lưới hiện tại", command=self.clear_current_grid, width=12, fg="red").pack(pady=1)
        tk.Button(tool_frame, text="RESET TẤT CẢ", command=self.reset_all, width=12, fg="white", bg="#d9534f").pack(pady=3)

        # 2. Quản lý Frame
        anim_frame = tk.LabelFrame(control_frame, text="2. Quản lý Frames", padx=5, pady=2, bg="#f0f0f0")
        anim_frame.grid(row=0, column=1, padx=5, sticky="n")
        
        self.lbl_frame_info = tk.Label(anim_frame, text="Frame: 1 / 1", bg="#f0f0f0", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_frame_info.pack(pady=2)
        
        nav_frame = tk.Frame(anim_frame, bg="#f0f0f0")
        nav_frame.pack()
        tk.Button(nav_frame, text="◄ Prev", command=self.prev_frame, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(nav_frame, text="Next ►", command=self.next_frame, width=6).pack(side=tk.LEFT, padx=1)
        
        tk.Button(anim_frame, text="+ Copy Frame", command=self.add_copy_frame, width=16).pack(pady=1)
        tk.Button(anim_frame, text="+ Thêm trống", command=self.add_empty_frame, width=16).pack(pady=1)
        tk.Button(anim_frame, text="- Xóa Frame này", command=self.delete_frame, fg="red", width=16).pack(pady=1)
        tk.Button(anim_frame, text="Xóa TẤT CẢ Frames", command=self.delete_all_frames, fg="white", bg="#d9534f", width=16).pack(pady=1)

        # 3. Dịch chuyển Thủ công
        shift_frame = tk.LabelFrame(control_frame, text="3. Dịch 1 ô", padx=5, pady=2, bg="#f0f0f0")
        shift_frame.grid(row=0, column=2, padx=5, sticky="n")
        tk.Button(shift_frame, text="↑", command=lambda: self.shift_logic(0, -1), width=4).pack(pady=2)
        shift_mid = tk.Frame(shift_frame, bg="#f0f0f0")
        shift_mid.pack()
        tk.Button(shift_mid, text="←", command=lambda: self.shift_logic(-1, 0), width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(shift_mid, text="↓", command=lambda: self.shift_logic(0, 1), width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(shift_mid, text="→", command=lambda: self.shift_logic(1, 0), width=4).pack(side=tk.LEFT, padx=2)

        # 4. TỰ ĐỘNG TẠO ANIMATION & HIỆU ỨNG (NÂNG CẤP)
        auto_frame = tk.LabelFrame(control_frame, text="4. Auto Animation Effects", padx=5, pady=2, bg="#f0f0f0")
        auto_frame.grid(row=0, column=3, padx=5, sticky="n")
        
        # --- A. Dịch tự động ---
        shift_auto_f = tk.Frame(auto_frame, bg="#f0f0f0")
        shift_auto_f.pack()
        tk.Label(shift_auto_f, text="Dịch", bg="#f0f0f0", font=("Arial", 8)).pack(side=tk.LEFT)
        self.auto_steps_var = tk.StringVar(value="32")
        tk.Entry(shift_auto_f, textvariable=self.auto_steps_var, width=3, justify="center").pack(side=tk.LEFT, padx=2)
        tk.Label(shift_auto_f, text="ô:", bg="#f0f0f0", font=("Arial", 8)).pack(side=tk.LEFT)
        
        tk.Button(shift_auto_f, text="↑", command=lambda: self.auto_shift(0, -1), width=2, bg="#ffeb3b").pack(side=tk.LEFT, padx=1)
        tk.Button(shift_auto_f, text="↓", command=lambda: self.auto_shift(0, 1), width=2, bg="#ffeb3b").pack(side=tk.LEFT, padx=1)
        tk.Button(shift_auto_f, text="←", command=lambda: self.auto_shift(-1, 0), width=2, bg="#ffeb3b").pack(side=tk.LEFT, padx=1)
        tk.Button(shift_auto_f, text="→", command=lambda: self.auto_shift(1, 0), width=2, bg="#ffeb3b").pack(side=tk.LEFT, padx=1)

        tk.Frame(auto_frame, height=2, bg="#ccc").pack(fill=tk.X, pady=3)

        # --- B. Wipe Out (Xóa Dần) ---
        tk.Label(auto_frame, text="XÓA dần (Wipe Out):", bg="#f0f0f0", font=("Arial", 8, "bold"), fg="#d9534f").pack()
        wipe_f1 = tk.Frame(auto_frame, bg="#f0f0f0")
        wipe_f1.pack()
        tk.Button(wipe_f1, text="Cột L→R", command=lambda: self.auto_wipe('col_lr'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(wipe_f1, text="Cột R→L", command=lambda: self.auto_wipe('col_rl'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        wipe_f2 = tk.Frame(auto_frame, bg="#f0f0f0")
        wipe_f2.pack(pady=1)
        tk.Button(wipe_f2, text="Hàng T→B", command=lambda: self.auto_wipe('row_tb'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(wipe_f2, text="Hàng B→T", command=lambda: self.auto_wipe('row_bt'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        tk.Frame(auto_frame, height=2, bg="#ccc").pack(fill=tk.X, pady=3)

        # --- C. Reveal In (Hiện Dần) ---
        tk.Label(auto_frame, text="HIỆN dần (Wipe In):", bg="#f0f0f0", font=("Arial", 8, "bold"), fg="#5cb85c").pack()
        rev_f1 = tk.Frame(auto_frame, bg="#f0f0f0")
        rev_f1.pack()
        tk.Button(rev_f1, text="Cột L→R", command=lambda: self.auto_reveal('col_lr'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(rev_f1, text="Cột R→L", command=lambda: self.auto_reveal('col_rl'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        rev_f2 = tk.Frame(auto_frame, bg="#f0f0f0")
        rev_f2.pack(pady=1)
        tk.Button(rev_f2, text="Hàng T→B", command=lambda: self.auto_reveal('row_tb'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(rev_f2, text="Hàng B→T", command=lambda: self.auto_reveal('row_bt'), width=7, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        # 5. Xuất Code
        col5 = tk.LabelFrame(control_frame, text="5. Xuất Mã ASM", padx=5, pady=2, bg="#f0f0f0")
        col5.grid(row=0, column=4, padx=5, sticky="n")
        
        self.polarity_var = tk.StringVar(value="cathode")
        tk.Radiobutton(col5, text="Cathode (1=Sáng)", variable=self.polarity_var, value="cathode", bg="#f0f0f0").pack(anchor=tk.W)
        tk.Radiobutton(col5, text="Anode (0=Sáng)", variable=self.polarity_var, value="anode", bg="#f0f0f0").pack(anchor=tk.W)
        
        tk.Button(col5, text="XÓA CODE", command=self.clear_asm, width=15, fg="white", bg="#d9534f").pack(pady=2)
        tk.Button(col5, text="XUẤT MÃ ASM", command=self.generate_asm, width=15, height=2, bg="#5cb85c", fg="white", font=("Arial", 9, "bold")).pack(pady=2)

    # --- CÁC HÀM XÓA CƠ BẢN ---
    def delete_all_frames(self):
        if messagebox.askyesno("Cảnh báo", "Xóa TOÀN BỘ các frame (chỉ giữ lại 1 frame trống)?"):
            self.frames = [self.create_empty_grid()]
            self.current_frame_idx = 0
            self.grid_data = self.frames[0]
            self.clear_selection()
            self.draw_grid()
            self.update_frame_lbl()

    def reset_all(self):
        if messagebox.askyesno("Cảnh báo nguy hiểm", "Xóa sạch: Lưới, Frames, và Mã ASM. Bạn chắc chắn?"):
            self.frames = [self.create_empty_grid()]
            self.current_frame_idx = 0
            self.grid_data = self.frames[0]
            self.clear_selection()
            self.draw_grid()
            self.update_frame_lbl()
            self.clear_asm()

    # --- HIỆU ỨNG: DỊCH CHUYỂN TỰ ĐỘNG ---
    def auto_shift(self, dc, dr):
        try:
            steps = int(self.auto_steps_var.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số nguyên!")
            return
        if steps <= 0: return

        for _ in range(steps):
            new_frame = copy.deepcopy(self.grid_data)
            self.current_frame_idx += 1
            self.frames.insert(self.current_frame_idx, new_frame)
            self.grid_data = self.frames[self.current_frame_idx]
            self.shift_logic(dc, dr, draw=False)
            
        self.draw_grid()
        self.update_frame_lbl()
        messagebox.showinfo("Thành công", f"Tạo {steps} Frames dịch chuyển!")

    # --- HIỆU ỨNG: XÓA DẦN (WIPE OUT) ---
    def auto_wipe(self, mode):
        steps = self.cols if mode.startswith('col') else self.rows
        
        if not messagebox.askyesno("Tạo hiệu ứng Xóa dần", f"Tạo thêm {steps} frames để xóa dần?"):
            return

        for step in range(steps):
            new_frame = copy.deepcopy(self.grid_data)
            
            if mode == 'col_lr':
                col_to_clear = step
                for r in range(self.rows): new_frame[r][col_to_clear] = 0
            elif mode == 'col_rl':
                col_to_clear = self.cols - 1 - step
                for r in range(self.rows): new_frame[r][col_to_clear] = 0
            elif mode == 'row_tb':
                row_to_clear = step
                for c in range(self.cols): new_frame[row_to_clear][c] = 0
            elif mode == 'row_bt':
                row_to_clear = self.rows - 1 - step
                for c in range(self.cols): new_frame[row_to_clear][c] = 0
                
            self.current_frame_idx += 1
            self.frames.insert(self.current_frame_idx, new_frame)
            self.grid_data = self.frames[self.current_frame_idx]
            
        self.draw_grid()
        self.update_frame_lbl()
        messagebox.showinfo("Thành công", f"Đã tạo hiệu ứng Xóa Dần ({steps} Frames)!")

    # --- HIỆU ỨNG: HIỆN DẦN (REVEAL / WIPE IN) ---
    def auto_reveal(self, mode):
        steps = self.cols if mode.startswith('col') else self.rows
        
        if not messagebox.askyesno("Tạo hiệu ứng Hiện dần", f"Dùng hình ảnh hiện tại làm 'đích' và tạo {steps} frames bắt đầu từ màn hình trống để hiện dần lên?"):
            return

        target_frame = copy.deepcopy(self.grid_data)
        progressive_frame = self.create_empty_grid()

        for step in range(steps):
            if mode == 'col_lr':
                col = step
                for r in range(self.rows): progressive_frame[r][col] = target_frame[r][col]
            elif mode == 'col_rl':
                col = self.cols - 1 - step
                for r in range(self.rows): progressive_frame[r][col] = target_frame[r][col]
            elif mode == 'row_tb':
                row = step
                for c in range(self.cols): progressive_frame[row][c] = target_frame[row][c]
            elif mode == 'row_bt':
                row = self.rows - 1 - step
                for c in range(self.cols): progressive_frame[row][c] = target_frame[row][c]
                
            self.current_frame_idx += 1
            self.frames.insert(self.current_frame_idx, copy.deepcopy(progressive_frame))
            self.grid_data = self.frames[self.current_frame_idx]
            
        self.draw_grid()
        self.update_frame_lbl()
        messagebox.showinfo("Thành công", f"Đã tạo hiệu ứng Hiện Dần ({steps} Frames)!")

    # --- QUẢN LÝ FRAME & GIAO DIỆN CHUNG ---
    def update_frame_lbl(self):
        self.lbl_frame_info.config(text=f"Frame: {self.current_frame_idx + 1} / {len(self.frames)}")

    def prev_frame(self):
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.grid_data = self.frames[self.current_frame_idx]
            self.clear_selection()
            self.draw_grid()
            self.update_frame_lbl()

    def next_frame(self):
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            self.grid_data = self.frames[self.current_frame_idx]
            self.clear_selection()
            self.draw_grid()
            self.update_frame_lbl()

    def add_copy_frame(self):
        new_frame = copy.deepcopy(self.grid_data)
        self.current_frame_idx += 1
        self.frames.insert(self.current_frame_idx, new_frame)
        self.grid_data = self.frames[self.current_frame_idx]
        self.clear_selection()
        self.draw_grid()
        self.update_frame_lbl()

    def add_empty_frame(self):
        new_frame = self.create_empty_grid()
        self.current_frame_idx += 1
        self.frames.insert(self.current_frame_idx, new_frame)
        self.grid_data = self.frames[self.current_frame_idx]
        self.clear_selection()
        self.draw_grid()
        self.update_frame_lbl()

    def delete_frame(self):
        if len(self.frames) == 1:
            self.grid_data = self.create_empty_grid()
            self.frames[0] = self.grid_data
        else:
            self.frames.pop(self.current_frame_idx)
            if self.current_frame_idx >= len(self.frames):
                self.current_frame_idx = len(self.frames) - 1
            self.grid_data = self.frames[self.current_frame_idx]
        self.clear_selection()
        self.draw_grid()
        self.update_frame_lbl()

    def update_dimensions(self):
        if messagebox.askyesno("Cảnh báo", "Đổi kích thước sẽ xóa toàn bộ Frames. Tiếp tục?"):
            self.cols = self.size_var.get()
            self.rows = self.rows_var.get()
            self.clear_selection()
            self.frames = [self.create_empty_grid()]
            self.current_frame_idx = 0
            self.grid_data = self.frames[0]
            self.draw_grid()
            self.update_frame_lbl()
        else:
            self.size_var.set(self.cols)
            self.rows_var.set(self.rows)

    def draw_grid(self):
        canvas_w = self.cols * self.cell_size
        canvas_h = self.rows * self.cell_size
        self.canvas.config(width=canvas_w, height=canvas_h)
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                self.draw_single_led(r, c)
        if self.selection: self.draw_selection_box()

    def draw_single_led(self, r, c):
        x1, y1 = c * self.cell_size, r * self.cell_size
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size
        pad = 2 
        color = "#00ff00" if self.grid_data[r][c] == 1 else "#333333"
        self.canvas.delete(f"cell_{r}_{c}")
        self.canvas.create_oval(x1 + pad, y1 + pad, x2 - pad, y2 - pad, fill=color, outline="#222", tags=f"cell_{r}_{c}")

    def on_left_click(self, event):
        if self.tool_mode.get() == "draw":
            c, r = event.x // self.cell_size, event.y // self.cell_size
            if 0 <= c < self.cols and 0 <= r < self.rows:
                self.current_draw_mode = 0 if self.grid_data[r][c] == 1 else 1
                self.update_cell(r, c, self.current_draw_mode)
        else:
            self.sel_start_coords = (event.x, event.y)
            self.clear_selection()

    def on_left_drag(self, event):
        if self.tool_mode.get() == "draw":
            c, r = event.x // self.cell_size, event.y // self.cell_size
            if 0 <= c < self.cols and 0 <= r < self.rows:
                self.update_cell(r, c, self.current_draw_mode)
        else:
            if self.sel_start_coords:
                self.canvas.delete("sel_temp")
                self.canvas.create_rectangle(self.sel_start_coords[0], self.sel_start_coords[1], 
                                             event.x, event.y, outline="#00ffff", dash=(4,4), tags="sel_temp")

    def on_left_release(self, event):
        if self.tool_mode.get() == "select" and self.sel_start_coords:
            c1, r1 = self.sel_start_coords[0] // self.cell_size, self.sel_start_coords[1] // self.cell_size
            c2, r2 = event.x // self.cell_size, event.y // self.cell_size
            self.selection = (max(0, min(c1, c2)), max(0, min(r1, r2)), 
                              min(self.cols-1, max(c1, c2)), min(self.rows-1, max(r1, r2)))
            self.draw_grid()
            self.sel_start_coords = None

    def update_cell(self, r, c, val):
        if self.grid_data[r][c] != val:
            self.grid_data[r][c] = val
            self.draw_single_led(r, c)

    def draw_selection_box(self):
        c1, r1, c2, r2 = self.selection
        self.canvas.create_rectangle(c1*self.cell_size, r1*self.cell_size, 
                                     (c2+1)*self.cell_size, (r2+1)*self.cell_size, 
                                     outline="#00ffff", width=2, dash=(4,4), tags="selection_rect")

    def clear_selection(self):
        self.selection = None
        self.canvas.delete("selection_rect")
        self.canvas.delete("sel_temp")

    def shift_logic(self, dc, dr, draw=True):
        c_min, r_min, c_max, r_max = self.selection if self.selection else (0, 0, self.cols-1, self.rows-1)
        temp_data = {}
        for r in range(r_min, r_max + 1):
            for c in range(c_min, c_max + 1):
                temp_data[(r, c)] = self.grid_data[r][c]
                self.grid_data[r][c] = 0 
        for (r, c), val in temp_data.items():
            new_r, new_c = r + dr, c + dc
            if r_min <= new_r <= r_max and c_min <= new_c <= c_max:
                self.grid_data[new_r][new_c] = val
        if draw:
            self.draw_grid()

    def clear_current_grid(self):
        self.grid_data = self.create_empty_grid()
        self.frames[self.current_frame_idx] = self.grid_data
        self.draw_grid()

    def clear_asm(self):
        self.code_output.delete(1.0, tk.END)

    def generate_asm(self):
        self.clear_asm()
        final_text = ""
        is_anode = (self.polarity_var.get() == "anode")
        
        for idx, frame in enumerate(self.frames):
            final_text += f"; ====== FRAME {idx + 1} ({self.cols}x{self.rows}) ======\n"
            asm_lines = []
            
            for c in range(self.cols):
                if self.rows == 8:
                    byte = 0
                    for r in range(8):
                        if frame[r][c]: byte |= (1 << r)
                    
                    if is_anode:
                        byte ^= 0xFF
                        
                    asm_lines.append(f"0x{byte:02X}")
                else:
                    byte_high = 0 
                    byte_low = 0  
                    for r in range(8):
                        if frame[r][c]: byte_high |= (1 << r)
                    for r in range(8, 16):
                        if frame[r][c]: byte_low |= (1 << (r - 8))
                    
                    if is_anode:
                        byte_high ^= 0xFF
                        byte_low ^= 0xFF
                        
                    asm_lines.append(f"0x{byte_high:02X}")
                    asm_lines.append(f"0x{byte_low:02X}")

            step = 8 if self.rows == 8 else 16
            for i in range(0, len(asm_lines), step):
                chunk = asm_lines[i:i+step]
                final_text += "    DB " + ", ".join(chunk) + "\n"
            final_text += "\n" 
            
        self.code_output.insert(tk.END, final_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = LedMatrixApp(root)
    root.mainloop()