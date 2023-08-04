import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import os
from threading import Thread

import utils
from .output import Output


def _flash_file_thread(*args):
    objfilename, serial_port, output_queue_func = args  # unpack args
    objbasename = os.path.basename(objfilename)

    if utils.flash_file(objfilename, serial_port):
        output_queue_func(f"\n{objbasename} flashed succesfully", Output.TAG_SUCCESS)
    else:
        output_queue_func(f"\n{objbasename} flash failed", Output.TAG_ERROR)


class FlashArg(ttk.Labelframe):
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent

        # container
        super().__init__(
            self.parent,
            text="Flash Arguments",
            style="custom.TLabelframe",
            padding=(12, 2, 12, 15),
        )

        # object file input
        self.objfile_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        self.objfile_label = ttk.Label(self.objfile_frame, text="Object File")
        self.objfile_button = ttk.Button(
            self.objfile_frame,
            text="Choose File",
            style="file.TButton",
            command=self.handle_choose_file_click,
        )
        self.objfile_desc_textvar = tk.StringVar(value="No file chosen")
        self.objfile_desc = ttk.Label(
            self.objfile_frame,
            textvariable=self.objfile_desc_textvar,
            style="file.TLabel",
            width=12,  # this makes the labelframe not expand for long filenames
        )

        # device input
        serial_ports = utils.get_formatted_serial_ports()
        self.device_frame = ttk.Frame(self, padding=(0, 0, 0, 15))
        self.device_label = ttk.Label(self.device_frame, text="Device")
        self.device_textvar = tk.StringVar()
        self.device_select = ttk.Combobox(
            self.device_frame, textvariable=self.device_textvar, values=serial_ports
        )
        # self.device_select.state(["disabled"])
        # set the first port as the default value if this is available
        if serial_ports:
            self.device_select.current(0)

        # flash button
        self.submit_frame = ttk.Frame(self)
        self.submit_button = ttk.Button(
            self.submit_frame,
            text="Flash",
            style="submit.TButton",
            command=self.handle_submit_click,
        )

        #
        self.objfile_frame.grid(sticky="we")
        self.objfile_label.grid(sticky="w", columnspan=2)
        self.objfile_button.grid(row=1, column=0)
        self.objfile_desc.grid(sticky="we", row=1, column=1)
        self.device_frame.grid(sticky="we")
        self.device_label.grid(sticky="w")
        self.device_select.grid(sticky="we")
        self.submit_frame.grid(sticky="we")
        self.submit_button.grid()

        #
        self.grid_columnconfigure(0, weight=1)
        self.objfile_frame.grid_columnconfigure(1, weight=1)
        self.device_frame.grid_columnconfigure(0, weight=1)
        self.submit_frame.grid_columnconfigure(0, weight=1)

        #
        self.objfile_button.bind("<Return>", lambda event: self.objfile_button.invoke())
        self.submit_button.bind("<Return>", lambda event: self.submit_button.invoke())
        # shortcut, F5 to flash
        self.root.bind("<F5>", lambda event: self.submit_button.invoke())

    """
    Getters
    """

    def get_objfilename(self):
        return getattr(self, "objfilename", None)

    def get_device_port(self):
        return utils.get_port_from_formatted_serial_port(self.device_textvar.get())

    def set_available_formatted_serial_ports(self, serial_ports):
        self.device_select["values"] = serial_ports

    """
    Event Handlers
    """

    def handle_choose_file_click(self, *args):
        self.objfilename = filedialog.askopenfilename(
            filetypes=(("Intel HEX File", "*.hex"),)
        )

        if self.objfilename:
            self.objfile_desc_textvar.set(os.path.basename(self.objfilename))

    def handle_submit_click(self, *args):
        self.root.flashoutput.clear()

        # input validation
        if not self.get_objfilename() or not self.get_device_port():
            self.root.flashoutput.print("Invalid flash arguments", Output.TAG_ERROR)
            return

        # disable submit button to avoid multiple threads / clicks
        self.submit_button.state(["disabled"])

        # create thread
        self.flash_file_thread = Thread(
            target=_flash_file_thread,
            args=[
                self.get_objfilename(),
                self.get_device_port(),
                self.root.flashoutput.queue,
            ],
        )
        self.flash_file_thread.start()

        # start timer for handling queued output lines
        self.root.after(100, self.handle_submit_timer)

    def handle_submit_timer(self, *args):
        # saving the result here to avoid race conditions
        is_thread_alive = self.flash_file_thread.is_alive()

        self.root.flashoutput.dequeue()

        if is_thread_alive:
            # there may be other output lines incoming
            self.root.after(100, self.handle_submit_timer)
        else:
            # re-enable submit button
            self.submit_button.state(["!disabled"])
