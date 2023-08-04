import tkinter as tk
from tkinter import ttk
from tkinter import font

import queue


class Output(ttk.Labelframe):
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent

        # init output text queue
        self.output_text_queue = queue.Queue()

        # container
        super().__init__(
            self.parent,
            text="Output",
            style="custom.TLabelframe",
            padding=(12, 2, 12, 15),
        )

        # output textarea
        # height = 1 because it will auto-expand its height
        self.output_text = tk.Text(
            self, state="disabled", padx=4, pady=4, height=1, width=35
        )
        self.output_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.output_text.yview
        )
        self.output_text.config(yscrollcommand=self.output_scrollbar.set)

        #
        self.output_text.grid(row=0, column=0, sticky="nswe")
        self.output_scrollbar.grid(row=0, column=1, sticky="ns")

        #
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._setup_tags()

    """
    Actions
    """

    def clear(self):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.config(state="disabled")

    def print(self, msg, tags=(), end="\n"):
        self.output_text.config(state="normal")
        self.output_text.insert("end", msg + end, tags)
        self.output_text.config(state="disabled")
        # always scroll to end
        self.output_text.yview_moveto("1.0")

    def queue(self, msg, tags=(), end="\n"):
        self.output_text_queue.put((msg, tags, end))

    def dequeue(self):
        while self.output_text_queue.qsize():
            try:
                msg, tags, end = self.output_text_queue.get_nowait()
                self.print(msg, tags, end)
            except queue.Empty:
                pass

    """
    Tags
    """

    TAG_CRITICAL = "critical"
    TAG_ERROR = "error"
    TAG_WARNING = "warning"
    TAG_INFO = "info"
    TAG_SUCCESS = "success"

    def _setup_tags(self):
        text_font = font.nametofont(self.output_text["font"]).actual()
        text_font_bold = [text_font["family"], text_font["size"], "bold"]

        self.output_text.tag_configure(
            self.TAG_CRITICAL, foreground="orange", font=text_font_bold
        )
        self.output_text.tag_configure(
            self.TAG_ERROR, foreground="red", font=text_font_bold
        )
        self.output_text.tag_configure(self.TAG_WARNING, foreground="yellow")
        self.output_text.tag_configure(self.TAG_INFO, foreground="blue")
        self.output_text.tag_configure(
            self.TAG_SUCCESS, foreground="green", font=text_font_bold
        )
