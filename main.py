#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk
from tkinter import font

import logging

import utils
from components import FlashArg, TestArg, Output


class OutputLineHandlerSafe(logging.Handler):
    LEVELNO_TAG_MAP = {
        logging.CRITICAL: Output.TAG_CRITICAL,
        logging.ERROR: Output.TAG_ERROR,
        logging.WARNING: Output.TAG_WARNING,
        logging.INFO: Output.TAG_INFO,
    }

    def __init__(self, output_queue_func, *args):
        super().__init__(*args)
        self.output_queue_func = output_queue_func
        self.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    def emit(self, record):
        levelname, *msg = self.format(record).split(":")
        self.output_queue_func(levelname, self.LEVELNO_TAG_MAP[record.levelno], end="")
        self.output_queue_func(":" + ":".join(msg))


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("coffe probe tester")

        self.setup_style()
        self.setup_gui()
        self.setup_loggers()

        self.after(1000, self.handle_periodic_check)

    def setup_gui(self):
        # set up widgets
        self.mainframe = ttk.Frame(self, padding=(15, 8, 15, 15))
        self.flasharg = FlashArg(self, self.mainframe)
        self.flashoutput = Output(self, self.mainframe)
        self.testarg = TestArg(self, self.mainframe)
        self.testoutput = Output(self, self.mainframe)

        # set up layout
        self.mainframe.grid(sticky="nswe")
        self.flasharg.grid(sticky="nswe", row=0, column=0, padx=(0, 6), pady=(0, 6))
        self.flashoutput.grid(sticky="nswe", row=0, column=1, pady=(0, 6))
        self.testarg.grid(sticky="nswe", row=1, column=0, padx=(0, 6))
        self.testoutput.grid(sticky="nswe", row=1, column=1)

        # set up how extra space is used
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.mainframe.grid_rowconfigure(0, weight=2)
        self.mainframe.grid_rowconfigure(1, weight=1)
        self.mainframe.grid_columnconfigure(0, weight=1)
        self.mainframe.grid_columnconfigure(1, weight=3)

    def setup_style(self):
        style = ttk.Style()

        # change theme
        theme_names = style.theme_names()
        theme_names_dict = dict((t, t) for t in theme_names)
        # use os native theme (vista = Windows, aqua = MacOS, alt = all)
        style.theme_use(
            theme_names_dict.get("vista")
            or theme_names_dict.get("aqua")
            or theme_names_dict.get("alt")
        )
        print(theme_names)

        default_font = font.nametofont("TkDefaultFont").actual()
        print(default_font)

        style.configure("custom.TLabelframe", labelmargins=(15, 5))
        style.configure(
            "custom.TLabelframe.Label",
            font=[default_font["family"], default_font["size"], "bold"],
        )
        style.configure(
            "file.TButton",
            font=[default_font["family"], default_font["size"] - 1],
        )
        style.configure(
            "file.TLabel",
            font=[default_font["family"], default_font["size"] - 1],
        )
        style.configure("debug.TFrame", background="red")

    def setup_loggers(self):
        # redirect pymcuprog logs to output text widget
        pymcuprog_logger = logging.getLogger("pymcuprog")
        pymcuprog_logger.setLevel(logging.INFO)  # no debug logs
        logger_handler = OutputLineHandlerSafe(self.flashoutput.queue)
        pymcuprog_logger.addHandler(logger_handler)

    """
    Interval Handler
    """

    def handle_periodic_check(self):
        # update available serial ports
        serial_ports = utils.get_formatted_serial_ports()
        self.flasharg.set_available_formatted_serial_ports(serial_ports)
        self.testarg.set_available_formatted_serial_ports(serial_ports)
        self.after(1000, self.handle_periodic_check)


if __name__ == "__main__":
    app = App()
    app.mainloop()
