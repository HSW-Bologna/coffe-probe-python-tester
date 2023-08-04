import tkinter as tk
from tkinter import ttk

from threading import Thread
from time import sleep
from datetime import datetime

import utils
from .output import Output


class TestState:
    INIT = 0
    IN_PROGRESS = 1
    FAILED = 2
    SUCCESS = 3


def _test_thread(*args):
    serial_port, output_queue_func = args  # unpack args

    # connection
    try:
        modbus_instrument = utils.modbus_connect(serial_port)
    except IOError as error:
        output_queue_func(
            f"Connection failed with {serial_port}",
            Output.TAG_ERROR,
        )
        print(error)
        return

    # start test
    try:
        utils.modbus_set_cmd(modbus_instrument, 1)
    except IOError as error:
        output_queue_func("Test start failed", Output.TAG_ERROR)
        print(error)
        return

    # pool for test state
    try:
        modbus_state = last_modbus_state = -1
        while modbus_state != TestState.FAILED and modbus_state != TestState.SUCCESS:
            modbus_state = utils.modbus_get_state(modbus_instrument)

            if modbus_state != last_modbus_state:
                timestamp = datetime.now().strftime("%H:%M:%S")
                output_queue_func(f"[{timestamp}]", end=" ")

                if modbus_state == TestState.INIT:
                    output_queue_func("Test initialization")
                elif modbus_state == TestState.IN_PROGRESS:
                    output_queue_func("Test in progress")
                elif modbus_state == TestState.FAILED:
                    output_queue_func("Test failed", Output.TAG_ERROR)
                elif modbus_state == TestState.SUCCESS:
                    output_queue_func("Test success", Output.TAG_SUCCESS)
                else:
                    output_queue_func("Unknown test state", Output.TAG_CRITICAL)

                last_modbus_state = modbus_state

            sleep(0.1)  # 100ms
    except IOError as error:
        output_queue_func("Test interrupted for an exception", Output.TAG_ERROR)
        print(error)


class TestArg(ttk.Labelframe):
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent

        # container
        super().__init__(
            self.parent,
            text="Test Arguments",
            style="custom.TLabelframe",
            padding=(12, 2, 12, 15),
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
        # set the second port as the default value if this is available
        if len(serial_ports) > 1:
            self.device_select.current(1)

        # test button
        self.submit_frame = ttk.Frame(self)
        self.submit_button = ttk.Button(
            self.submit_frame,
            text="Test",
            style="submit.TButton",
            command=self.handle_submit_click,
        )

        #
        self.device_frame.grid(sticky="we")
        self.device_label.grid(sticky="w")
        self.device_select.grid(sticky="we")
        self.submit_frame.grid(sticky="we")
        self.submit_button.grid()

        #
        self.grid_columnconfigure(0, weight=1)
        self.device_frame.grid_columnconfigure(0, weight=1)
        self.submit_frame.grid_columnconfigure(0, weight=1)

        #
        self.submit_button.bind("<Return>", lambda event: self.submit_button.invoke())
        # shortcut, F6 to test
        self.root.bind("<F6>", lambda event: self.submit_button.invoke())

    """
    Getters
    """

    def get_device_port(self):
        return utils.get_port_from_formatted_serial_port(self.device_textvar.get())

    def set_available_formatted_serial_ports(self, serial_ports):
        self.device_select["values"] = serial_ports

    """
    Handlers
    """

    def handle_submit_click(self):
        self.root.testoutput.clear()

        # input validation
        if not self.get_device_port():
            self.root.testoutput.print("Invalid test arguments", Output.TAG_ERROR)
            return

        # disable submit button to avoid multiple threads / clicks
        self.submit_button.state(["disabled"])

        # create thread
        self.test_thread = Thread(
            target=_test_thread,
            args=[
                self.get_device_port(),
                self.root.testoutput.queue,
            ],
        )
        self.test_thread.start()

        # start timer for handling queued output lines
        self.root.after(100, self.handle_submit_timer)

    def handle_submit_timer(self, *args):
        # saving the result here to avoid race conditions
        is_thread_alive = self.test_thread.is_alive()

        self.root.testoutput.dequeue()

        if is_thread_alive:
            # there may be other output lines incoming
            self.root.after(100, self.handle_submit_timer)
        else:
            # re-enable submit button
            self.submit_button.state(["!disabled"])
