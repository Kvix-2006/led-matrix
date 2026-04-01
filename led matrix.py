import tkinter as tk

ROWS = 8
SIZE = 22

class LedMatrix:

    def __init__(self,root):

        self.root=root
        self.root.title("LED Matrix Animator")

        self.cols=32

        self.frames=[]
        self.current=0
        self.frames.append(self.empty_frame())

        sizebar=tk.Frame(root)
        sizebar.pack()

        tk.Button(sizebar,text="8x12",
                  command=lambda:self.change_size(12)).grid(row=0,column=0)

        tk.Button(sizebar,text="8x24",
                  command=lambda:self.change_size(24)).grid(row=0,column=1)

        tk.Button(sizebar,text="8x32",
                  command=lambda:self.change_size(32)).grid(row=0,column=2)

        tk.Button(sizebar,text="8x64",
                  command=lambda:self.change_size(64)).grid(row=0,column=3)

        self.canvas=tk.Canvas(root)
        self.canvas.pack()

        self.led=[]

        framebar=tk.Frame(root)
        framebar.pack()

        tk.Button(framebar,text="<<",
                  command=self.prev_frame).grid(row=0,column=0)

        tk.Button(framebar,text=">>",
                  command=self.next_frame).grid(row=0,column=1)

        tk.Button(framebar,text="Frame +",
                  command=self.new_frame).grid(row=0,column=2)

        tk.Button(framebar,text="Delete",
                  command=self.delete_frame).grid(row=0,column=3)

        self.frame_label=tk.Label(framebar,text="")
        self.frame_label.grid(row=0,column=4)

        shift=tk.Frame(root)
        shift.pack()

        tk.Button(shift,text="←",
                  command=lambda:self.shift(-1,0)).grid(row=0,column=0)

        tk.Button(shift,text="→",
                  command=lambda:self.shift(1,0)).grid(row=0,column=1)

        tk.Button(shift,text="↑",
                  command=lambda:self.shift(0,-1)).grid(row=0,column=2)

        tk.Button(shift,text="↓",
                  command=lambda:self.shift(0,1)).grid(row=0,column=3)

        tk.Button(root,text="Clear",
                  command=self.clear).pack()

        tk.Button(root,text="Export ASM",
                  command=self.export).pack()

        self.text=tk.Text(root,height=8)
        self.text.pack(fill="both")

        self.build_matrix()

    def empty_frame(self):

        return [[0]*self.cols for _ in range(ROWS)]

    def change_size(self,new_cols):

        self.cols=new_cols

        self.frames=[self.empty_frame()]
        self.current=0

        self.build_matrix()

    def build_matrix(self):

        self.canvas.delete("all")

        self.canvas.config(
            width=self.cols*SIZE,
            height=ROWS*SIZE
        )

        self.led=[]

        for r in range(ROWS):

            row=[]

            for c in range(self.cols):

                x1=c*SIZE
                y1=r*SIZE
                x2=x1+SIZE
                y2=y1+SIZE

                obj=self.canvas.create_oval(
                    x1,y1,x2,y2,
                    fill="white",
                    outline="gray"
                )

                self.canvas.tag_bind(
                    obj,
                    "<Button-1>",
                    lambda e,r=r,c=c:self.toggle(r,c)
                )

                row.append(obj)

            self.led.append(row)

        self.update_frame_label()
        self.draw()

    def toggle(self,r,c):

        frame=self.frames[self.current]

        frame[r][c]^=1

        self.draw()

    def draw(self):

        frame=self.frames[self.current]

        for r in range(ROWS):
            for c in range(self.cols):

                color="lime" if frame[r][c] else "white"

                self.canvas.itemconfig(self.led[r][c],fill=color)

    def new_frame(self):

        new=[row[:] for row in self.frames[self.current]]

        self.frames.append(new)

        self.current=len(self.frames)-1

        self.update_frame_label()
        self.draw()

    def delete_frame(self):

        if len(self.frames)>1:

            self.frames.pop(self.current)
            self.current=max(0,self.current-1)

        self.update_frame_label()
        self.draw()

    def next_frame(self):

        if self.current < len(self.frames)-1:

            self.current+=1

        self.update_frame_label()
        self.draw()

    def prev_frame(self):

        if self.current>0:

            self.current-=1

        self.update_frame_label()
        self.draw()

    def update_frame_label(self):

        self.frame_label.config(
            text=f"Frame {self.current+1} / {len(self.frames)}"
        )

    def clear(self):

        self.frames[self.current]=self.empty_frame()
        self.draw()

    def shift(self,dx,dy):

        frame=self.frames[self.current]

        new=self.empty_frame()

        for r in range(ROWS):
            for c in range(self.cols):

                nr=r+dy
                nc=c+dx

                if 0<=nr<ROWS and 0<=nc<self.cols:

                    new[nr][nc]=frame[r][c]

        self.frames[self.current]=new
        self.draw()

    def export(self):

        output=[]

        for frame in self.frames:

            result=[]

            for c in range(self.cols):

                value=0xFF

                for r in range(ROWS):

                    if frame[r][c]:

                        value &= ~(1<<r)

                if value==0:
                    result.append("0H")
                else:
                    result.append(f"0{value:02X}H")

            output.append("DB "+",".join(result))

        text="\n".join(output)

        self.text.delete("1.0",tk.END)
        self.text.insert(tk.END,text)


root=tk.Tk()
LedMatrix(root)
root.mainloop()