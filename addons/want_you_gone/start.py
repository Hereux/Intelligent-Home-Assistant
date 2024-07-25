import ctypes
import queue
import random
import subprocess
import threading

import customtkinter

from AnimatedGif import *

ctypes.windll.shcore.SetProcessDpiAwareness(0)
display_width = ctypes.windll.user32.GetSystemMetrics(0)
display_height = ctypes.windll.user32.GetSystemMetrics(1)
orig_geometry = "3840x2160"
pos_label4 = 0.95
distance_4_3 = 0.085
text_frame_dist = (0.03, 0.06)
box_distance = 0.01
box_height = 0.1388
some_weird_number = 1 - (2 * 0.039)
number_frame_pos = 0.64+0.157+box_distance

font1 = ("Console", 28)
font2 = ("Console", 11)
font3 = ("Console", 30)


def maintain_aspect_ratio(event, aspect_ratio):
    """ Event handler to override root window resize events to maintain the
        specified width to height aspect ratio.
    """
    if event.widget.master:  # Not root window?
        return  # Ignore.

    # <Configure> events contain the widget's new width and height in pixels.
    new_aspect_ratio = event.width / event.height
    # Decide which dimension controls.
    if new_aspect_ratio < aspect_ratio:
        # Use width as the controlling dimension.
        desired_width = event.width
        desired_height = int(event.width / aspect_ratio)
    else:
        # Use height as the controlling dimension.
        desired_height = event.height
        desired_width = int(event.height * aspect_ratio)

    # Override if necessary.
    if event.width != desired_width or event.height != desired_height:
        # Manually give it the proper dimensions.
        event.widget.geometry(f'{desired_width}x{desired_height}')
        return "break"  # Block further processing of this event.


class WrappingLabel(customtkinter.CTkLabel):
    """a type of Label that automatically adjusts the wrap to the size"""

    def __init__(self, master=None, root=None, **kwargs):
        self.root: customtkinter.CTk = root
        self.min_font_size = 10
        self.max_font_size = 100
        self.min_width = 100
        self.max_width = 3840
        customtkinter.CTkLabel.__init__(self, master, **kwargs)
        self.bind('<Configure>', self.__config__)

    def __config__(self, event):
        width = self.winfo_width()
        if orig_geometry == self.root.geometry():
            return
        font_size = self.clamp(self.min_font_size, self.calculate_preferred_size(width), self.max_font_size)
        self.configure(wraplength=self.winfo_width(), font=("Console", int(font_size)))

    def calculate_preferred_size(self, width):
        slope = (self.max_font_size - self.min_font_size) / (self.max_width - self.min_width)
        y_intercept = self.min_font_size - slope * self.min_width
        return y_intercept + slope * width

    def clamp(self, min_value, preferred_value, max_value):
        return max(min_value, min(preferred_value, max_value))


class CustomConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Want you gone GUI V0.8")

        self.geometry(orig_geometry)
        self.last_geometry = self.geometry()
        self.bind("<Configure>", lambda event: maintain_aspect_ratio(event, display_width / display_height))

        self.font_size = None
        self.configure(bg="#704910")
        # self.wm_attributes('-fullscreen', True)
        self.state('normal')
        self.gif = None
        self.frame4 = None
        self.fps = 60  # Dont fucking modify this, this is useless to modify
        self.delay = int(1000 / self.fps)  # Convert fps for binary to delay in milliseconds

        self.text_frame = customtkinter.CTkFrame(master=self, border_color="#a16e23", border_width=5,
                                                 fg_color="transparent")
        self.text_frame.place(relx=0.039, rely=0.0486, relwidth=1 - (2 * 0.039), relheight=1 - (2 * 0.0486), anchor="nw")

        self.output_text = WrappingLabel(root=self, anchor="nw", justify="left", text="", text_color="#e9b15d",
                                         font=("Console", 28))
        self.output_text.place(relx=0.078, rely=box_height, relwidth=1 - (2 * 0.039) - 0.078,
                               relheight=1 - (2 * 0.0486) - 0.15)

        # North East boxes
        self.matrix_frame = customtkinter.CTkFrame(master=self, border_color="#a16e23", border_width=5,
                                                   fg_color="transparent")
        self.matrix_frame.place(relx=0.64, rely=0.03, relwidth=0.157, relheight=box_height, anchor='nw')

        self.matrix = WrappingLabel(master=self.matrix_frame, root=self, anchor="nw", text="101001110100",
                                    fg_color="transparent",
                                    text_color="#e9b15d", font=("Console", 11))
        self.matrix.place(relx=text_frame_dist[0], rely=text_frame_dist[1], relwidth=1-0.07, relheight=1-0.14,
                          anchor='nw')

        self.number_frame = customtkinter.CTkFrame(master=self, border_color="#a16e23", border_width=5,
                                                   fg_color="transparent")
        self.number_frame.place(relx=number_frame_pos, rely=0.03, relwidth=0.05, relheight=0.1388, anchor='nw')
        self.number_frame.bind("<Configure>", self.resize)

        self.number_text = WrappingLabel(master=self.number_frame, root=self, anchor="center",
                                         text="2 . 67 1002 45 . 6", fg_color="transparent", text_color="#e9b15d",
                                         font=("Console", 30))
        self.number_text.place(relx=0.09, rely=text_frame_dist[1], relwidth=1-0.17, relheight=1-text_frame_dist[1]*2,
                               anchor='nw')

        self.update_matrix()
        self.process = None
        self.output_queue = queue.Queue()  # Queue to store subprocess output

        # Start the subprocess in a separate thread
        threading.Thread(target=self.start_console).start()

    def resize(self, event):
        # Get the current height of number_frame
        number_frame_height = self.number_frame.winfo_height()
        number_frame_position = (self.number_frame.winfo_x(), self.number_frame.winfo_y())

        space = 10
        border_width = 5
        space_border = space + 2 * border_width
        # Destroy the current frame4
        if self.frame4 is not None:
            self.frame4.destroy()

        # Create a new frame4 with the same height as number_frame
        self.frame4 = customtkinter.CTkFrame(master=self, border_color="#a16e23", border_width=border_width,
                                             width=number_frame_height,
                                             height=number_frame_height, fg_color="transparent", bg_color="transparent")
        self.frame4.place(relx=number_frame_pos+0.05+box_distance, y=number_frame_position[1], anchor='nw')

        # Resize and place the gif image
        if self.gif is not None:
            self.gif.destroy()
        im = Image.open("styles/aperture.png").resize((number_frame_height, number_frame_height), Image.LANCZOS)
        self.gif = customtkinter.CTkImage(dark_image=im,
                                          size=(number_frame_height - space_border, number_frame_height - space_border))
        self.gif = customtkinter.CTkLabel(self.frame4, text="", width=number_frame_height - space_border,
                                          height=number_frame_height - space_border,
                                          image=self.gif)
        self.gif.place(x=space, y=space, anchor='nw')

    def start_console(self):
        # Start the subprocess
        self.process = subprocess.Popen(['python', './wantyougone.py'], stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, universal_newlines=True)

        # Start reading the output in a separate function
        self.read_process_output()

    def update_matrix(self):
        # Generate a random binary string of 20 characters
        binary_string = ''.join(random.choice('01 ') for _ in range(500))

        # Get Size of the window
        geometry_size = self.geometry().split("+")[0]

        # Update the matrix label
        self.matrix.configure(text=binary_string)

        if geometry_size != self.last_geometry:
            if geometry_size != "1x1":
                self.last_geometry = geometry_size

        self.update_idletasks()

        # Schedule the next update
        self.after(self.delay, self.update_matrix)  # Update according to monitor's refresh rate

    def read_process_output(self):
        self.process: subprocess.Popen
        if self.process is not None:
            # Check if subprocess has terminated
            if self.process.poll() is not None:
                self.process = None  # Reset process if it has finished
                return

            # Read subprocess output without blocking
            try:
                char = self.process.stdout.read(1)

                if char != "":
                    self.output_queue.put(char)

            except Exception as e:
                # Handle subprocess output read error
                print("Error reading subprocess output:", e)

            # Update the output text if there is any content in the queue
            while not self.output_queue.empty():
                char = self.output_queue.get()
                if char == '\x0c':
                    self.output_text.configure(text="")
                else:
                    current_text = self.output_text.cget("text")
                    self.output_text.configure(text=current_text + char)

            # Continue reading in the background
            self.after(10, self.read_process_output)
        else:
            # If the process is not started or has terminated, wait and check again
            self.after(100, self.read_process_output)


if __name__ == "__main__":
    app = CustomConsole()
    app.bind("<Escape>", lambda e: app.destroy())
    app.bind("<F11>", lambda e: app.attributes("-fullscreen", not app.attributes("-fullscreen")))
    app.mainloop()
