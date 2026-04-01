import tkinter as tk
import collections
from tkinter import messagebox

ROWS = 8
SIZE = 22
PREVIEW_SIZE = 6


class LedMatrix:

    def __init__(self, root):

        self.root = root
        self.root.title("LED Matrix Animator")

        self.visible_cols = 32
        self.frames = []
        self.current_frame = 0

        self.drag_start_r = None
        self.drag_start_c = None
        self.drag_preview = None

        self.unlimited_mode = False
        self.wrap_mode = False

        self.frames.append(self.empty_frame())

        sizebar = tk.Frame(root)
        sizebar.pack()

        tk.Button(sizebar, text="8x12", command=lambda: self.change_size(12)).grid(row=0, column=0)
        tk.Button(sizebar, text="8x24", command=lambda: self.change_size(24)).grid(row=0, column=1)
        tk.Button(sizebar, text="8x32", command=lambda: self.change_size(32)).grid(row=0, column=2)
        tk.Button(sizebar, text="8x64", command=lambda: self.change_size(64)).grid(row=0, column=3)

        modebar = tk.Frame(root)
        modebar.pack(pady=8)

        self.unlimited_btn = tk.Button(modebar, text="Unlimited: OFF", width=18,
                                       command=self.toggle_unlimited, font=("Arial", 9, "bold"))
        self.unlimited_btn.grid(row=0, column=0, padx=8)

        self.wrap_btn = tk.Button(modebar, text="Wrap Around: OFF", width=18,
                                  command=self.toggle_wrap, font=("Arial", 9, "bold"))
        self.wrap_btn.grid(row=0, column=1, padx=8)

        self.canvas = tk.Canvas(root)
        self.canvas.pack()

        framebar = tk.Frame(root)
        framebar.pack()

        tk.Button(framebar, text="<<", command=self.prev_frame).grid(row=0, column=0)
        tk.Button(framebar, text=">>", command=self.next_frame).grid(row=0, column=1)
        tk.Button(framebar, text="Frame +", command=self.add_frame).grid(row=0, column=2)
        tk.Button(framebar, text="Delete", command=self.delete_frame).grid(row=0, column=3)

        self.frame_label = tk.Label(framebar, text="")
        self.frame_label.grid(row=0, column=4)

        shift = tk.Frame(root)
        shift.pack()

        tk.Button(shift, text="←", command=lambda: self.shift(-1, 0)).grid(row=0, column=0)
        tk.Button(shift, text="→", command=lambda: self.shift(1, 0)).grid(row=0, column=1)
        tk.Button(shift, text="↑", command=lambda: self.shift(0, -1)).grid(row=0, column=2)
        tk.Button(shift, text="↓", command=lambda: self.shift(0, 1)).grid(row=0, column=3)

        tk.Button(root, text="Xóa Tất Cả", bg="#FF6666", fg="white",
                  command=self.delete_all).pack(pady=2)

        tk.Button(root, text="Clear", command=self.clear).pack(pady=2)

        tk.Button(root, text="Export ASM", command=self.export).pack(pady=2)

        tk.Button(root, text="Copy to Clipboard",
                  command=self.copy_clipboard).pack(pady=2)

        self.text = tk.Text(root, height=8)
        self.text.pack(fill="both")

        self.preview_canvas = tk.Canvas(root, height=80)
        self.preview_canvas.pack(fill="x")

        self.build_matrix()

        self.canvas.bind("<Button-1>", self.start_left_drag)
        self.canvas.bind("<B1-Motion>", self.left_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.end_left_drag)

        self.canvas.bind("<Button-3>", self.start_right_drag)
        self.canvas.bind("<B3-Motion>", self.right_drag_motion)
        self.canvas.bind("<ButtonRelease-3>", self.end_right_drag)

        self.preview_canvas.bind("<Button-1>", self.on_preview_click)

        self.root.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.preview_canvas.bind("<MouseWheel>", self.on_mouse_wheel)

    def empty_frame(self):
        return [collections.defaultdict(lambda: [0] * ROWS), 0]

    def toggle_unlimited(self):

        self.unlimited_mode = not self.unlimited_mode
        color = "#90EE90" if self.unlimited_mode else "SystemButtonFace"

        self.unlimited_btn.config(
            text=f"Unlimited: {'ON' if self.unlimited_mode else 'OFF'}",
            bg=color
        )

    def toggle_wrap(self):

        self.wrap_mode = not self.wrap_mode
        color = "#90EE90" if self.wrap_mode else "SystemButtonFace"

        self.wrap_btn.config(
            text=f"Wrap Around: {'ON' if self.wrap_mode else 'OFF'}",
            bg=color
        )

    def change_size(self, new_cols):

        self.visible_cols = new_cols
        self.frames = [self.empty_frame()]
        self.current_frame = 0
        self.build_matrix()

    def build_matrix(self):

        self.canvas.delete("all")

        self.canvas.config(width=self.visible_cols * SIZE,
                           height=ROWS * SIZE)

        self.led = []

        for r in range(ROWS):

            row = []

            for c in range(self.visible_cols):

                obj = self.canvas.create_rectangle(
                    c * SIZE, r * SIZE,
                    (c + 1) * SIZE, (r + 1) * SIZE,
                    fill="white",
                    outline="gray"
                )

                row.append(obj)

            self.led.append(row)

        self.update_frame_label()
        self.draw()

    def get_rc(self, event):

        c = event.x // SIZE
        r = event.y // SIZE

        if 0 <= r < ROWS and 0 <= c < self.visible_cols:
            return r, c

        return None, None

    def start_left_drag(self, event):

        r, c = self.get_rc(event)

        if r is not None:
            self.drag_start_r = r
            self.drag_start_c = c
            self.draw_led(r, c, 1)

    def left_drag_motion(self, event):

        if self.drag_start_r is None:
            return

        r, c = self.get_rc(event)

        if r is None:
            return

        if self.drag_preview:
            self.canvas.delete(self.drag_preview)

        x1 = self.drag_start_c * SIZE
        y1 = self.drag_start_r * SIZE
        x2 = (c + 1) * SIZE
        y2 = (r + 1) * SIZE

        self.drag_preview = self.canvas.create_rectangle(
            min(x1, x2), min(y1, y2),
            max(x1, x2), max(y1, y2),
            outline="#00AAFF",
            width=4,
            dash=(3, 3)
        )

    def end_left_drag(self, event):

        if self.drag_start_r is None:
            return

        r, vc = self.get_rc(event)

        if r is None:
            r, vc = self.drag_start_r, self.drag_start_c

        min_r = min(self.drag_start_r, r)
        max_r = max(self.drag_start_r, r)
        min_vc = min(self.drag_start_c, vc)
        max_vc = max(self.drag_start_c, vc)

        data, offset = self.frames[self.current_frame]

        for rr in range(min_r, max_r + 1):
            for vc_ in range(min_vc, max_vc + 1):
                data[offset + vc_][rr] = 1

        if self.drag_preview:
            self.canvas.delete(self.drag_preview)
            self.drag_preview = None

        self.drag_start_r = None
        self.drag_start_c = None

        self.draw()

    def start_right_drag(self, event):

        r, c = self.get_rc(event)

        if r is not None:
            self.drag_start_r = r
            self.drag_start_c = c
            self.draw_led(r, c, 0)

    def right_drag_motion(self, event):

        if self.drag_start_r is None:
            return

        r, c = self.get_rc(event)

        if r is None:
            return

        if self.drag_preview:
            self.canvas.delete(self.drag_preview)

        x1 = self.drag_start_c * SIZE
        y1 = self.drag_start_r * SIZE
        x2 = (c + 1) * SIZE
        y2 = (r + 1) * SIZE

        self.drag_preview = self.canvas.create_rectangle(
            min(x1, x2), min(y1, y2),
            max(x1, x2), max(y1, y2),
            outline="#FF4444",
            width=4,
            dash=(3, 3)
        )

    def end_right_drag(self, event):

        if self.drag_start_r is None:
            return

        r, vc = self.get_rc(event)

        if r is None:
            r, vc = self.drag_start_r, self.drag_start_c

        min_r = min(self.drag_start_r, r)
        max_r = max(self.drag_start_r, r)
        min_vc = min(self.drag_start_c, vc)
        max_vc = max(self.drag_start_c, vc)

        data, offset = self.frames[self.current_frame]

        for rr in range(min_r, max_r + 1):
            for vc_ in range(min_vc, max_vc + 1):
                data[offset + vc_][rr] = 0

        if self.drag_preview:
            self.canvas.delete(self.drag_preview)
            self.drag_preview = None

        self.drag_start_r = None
        self.drag_start_c = None

        self.draw()

    def draw_led(self, r, c, val):

        data, offset = self.frames[self.current_frame]
        data[offset + c][r] = val
        self.draw()

    def draw(self):

        data, offset = self.frames[self.current_frame]

        for r in range(ROWS):
            for vc in range(self.visible_cols):

                col = data.get(offset + vc, [0] * ROWS)

                color = "lime" if col[r] else "white"

                self.canvas.itemconfig(self.led[r][vc], fill=color)

        self.update_preview()

    def shift(self, dx, dy):

        data, offset = self.frames[self.current_frame]

        if dy != 0:

            new_data = collections.defaultdict(lambda: [0] * ROWS)

            for real_c, col in list(data.items()):
                for r in range(ROWS):

                    nr = r + dy

                    if 0 <= nr < ROWS:
                        new_data[real_c][nr] = col[r]

            self.frames[self.current_frame][0] = new_data

        if dx != 0:

            if self.wrap_mode:

                new_data = collections.defaultdict(lambda: [0] * ROWS)

                for real_c, col in list(data.items()):

                    new_c = (real_c + dx) % self.visible_cols

                    new_data[new_c] = col[:]

                self.frames[self.current_frame][0] = new_data
                self.frames[self.current_frame][1] = offset % self.visible_cols

            elif self.unlimited_mode:

                self.frames[self.current_frame][1] = offset - dx

            else:

                new_data = collections.defaultdict(lambda: [0] * ROWS)

                for real_c, col in list(data.items()):

                    new_c = real_c + dx

                    if new_c >= 0:
                        new_data[new_c] = col[:]

                self.frames[self.current_frame][0] = new_data

        self.draw()

    def on_preview_click(self, event):

        x = event.x
        preview_w = min(self.visible_cols, 24)
        block_width = preview_w * PREVIEW_SIZE + 15
        frame_idx = (x - 10) // block_width

        if 0 <= frame_idx < len(self.frames):
            self.current_frame = frame_idx
            self.update_frame_label()
            self.draw()

    def add_frame(self):

        old_data, old_offset = self.frames[self.current_frame]

        new_data = collections.defaultdict(lambda: [0] * ROWS)

        for k, v in old_data.items():
            new_data[k] = v[:]

        self.frames.append([new_data, old_offset])
        self.current_frame = len(self.frames) - 1

        self.update_frame_label()
        self.draw()

    def delete_frame(self):

        if len(self.frames) > 1:
            self.frames.pop(self.current_frame)
            self.current_frame = max(0, self.current_frame - 1)

        self.update_frame_label()
        self.draw()

    def delete_all(self):

        if messagebox.askyesno(
                "Xác nhận",
                "Xóa toàn bộ frame?"
        ):

            self.frames = [self.empty_frame()]
            self.current_frame = 0

            self.update_frame_label()
            self.draw()

    def next_frame(self):

        if self.current_frame < len(self.frames) - 1:
            self.current_frame += 1

        self.update_frame_label()
        self.draw()

    def prev_frame(self):

        if self.current_frame > 0:
            self.current_frame -= 1

        self.update_frame_label()
        self.draw()

    def update_frame_label(self):

        self.frame_label.config(
            text=f"Frame {self.current_frame + 1}/{len(self.frames)}"
        )

    def clear(self):

        self.frames[self.current_frame] = self.empty_frame()
        self.draw()

    def update_preview(self):

        self.preview_canvas.delete("all")

        x_offset = 10
        preview_w = min(self.visible_cols, 24)
        block_width = preview_w * PREVIEW_SIZE + 15

        for i, (data, offset) in enumerate(self.frames):

            for r in range(ROWS):
                for vc in range(preview_w):

                    col = data.get(offset + vc, [0] * ROWS)

                    x = x_offset + vc * PREVIEW_SIZE
                    y = 10 + r * PREVIEW_SIZE

                    color = "lime" if col[r] else "white"

                    self.preview_canvas.create_rectangle(
                        x, y,
                        x + PREVIEW_SIZE,
                        y + PREVIEW_SIZE,
                        fill=color,
                        outline="gray"
                    )

            if i == self.current_frame:

                self.preview_canvas.create_rectangle(
                    x_offset - 3,
                    7,
                    x_offset + preview_w * PREVIEW_SIZE + 3,
                    7 + ROWS * PREVIEW_SIZE + 3,
                    outline="red",
                    width=3
                )

            self.preview_canvas.create_text(
                x_offset + preview_w * PREVIEW_SIZE / 2,
                7 + ROWS * PREVIEW_SIZE + 12,
                text=str(i + 1),
                fill="black",
                font=("Arial", 8)
            )

            x_offset += block_width

    def export(self):

        output = []

        for frm_idx, (data, offset) in enumerate(self.frames):

            real_cols = sorted(data.keys())

            if not real_cols:
                output.append(f"; Frame {frm_idx + 1}: empty")
                output.append("DB 0H")
                continue

            result = []

            if self.wrap_mode:

                for vc in range(self.visible_cols):

                    real_c = (offset + vc) % self.visible_cols
                    col = data.get(real_c, [0] * ROWS)

                    value = 0xFF

                    for r in range(ROWS):
                        if col[r]:
                            value &= ~(1 << r)

                    result.append("0H" if value == 0 else f"0{value:02X}H")

            else:

                min_c = min(real_cols)
                max_c = max(real_cols)

                for real_c in range(min_c, max_c + 1):

                    col = data.get(real_c, [0] * ROWS)

                    value = 0xFF

                    for r in range(ROWS):
                        if col[r]:
                            value &= ~(1 << r)

                    result.append("0H" if value == 0 else f"0{value:02X}H")

            output.append(
                f"; Frame {frm_idx + 1} offset={offset} bytes={len(result)}"
            )

            output.append("DB " + ",".join(result))

        text = "\n".join(output)

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text)

    def copy_clipboard(self):

        data = self.text.get("1.0", tk.END)

        self.root.clipboard_clear()
        self.root.clipboard_append(data)
        self.root.update()

    def on_mouse_wheel(self, event):

        if event.state & 0x0001:

            dx = 1 if event.delta < 0 else -1
            self.shift(dx, 0)

        else:

            if event.delta > 0:
                self.prev_frame()
            else:
                self.next_frame()


root = tk.Tk()

LedMatrix(root)

root.mainloop()