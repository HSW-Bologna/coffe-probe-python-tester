from pymcuprog.backend import Backend, SessionConfig
from pymcuprog.toolconnection import ToolSerialConnection
from pymcuprog.hexfileutils import read_memories_from_hex
from pymcuprog.deviceinfo.memorynames import MemoryNameAliases
from pymcuprog.deviceinfo.deviceinfokeys import DeviceMemoryInfoKeys
import serial.tools.list_ports
import minimalmodbus


def modbus_connect(serial_port):
    if (
        not hasattr(modbus_connect, "instr")
        or modbus_connect.instr.serial.port != serial_port
    ):
        # port name, slave address (in decimal)
        modbus_connect.instr = minimalmodbus.Instrument(serial_port, 1)
        # https://minimalmodbus.readthedocs.io/en/stable/usage.html#default-values
        modbus_connect.instr.serial.baudrate = 115200
        modbus_connect.instr.serial.timeout = 0.05  # 0.05
        # modbus_connect.instr.close_port_after_each_call = True

        # consume input stream
        modbus_connect.instr.serial.reset_input_buffer()
        modbus_connect.instr.serial.readline()

    return modbus_connect.instr


def modbus_set_cmd(instr, v):
    # register 0 = cmd
    instr.write_bit(0, v)


def modbus_get_state(instr):
    # register 1 = state
    return instr.read_register(1)


def get_formatted_serial_ports():
    # return ["/dev/ttyUSB0 (desc1)", "/dev/ttyUSB1 (desc2)"]
    ports = serial.tools.list_ports.comports()
    return [f"{port} ({desc})" for port, desc, hwid in sorted(ports)]


def get_port_from_formatted_serial_port(formatted_port):
    return formatted_port.split("(")[0].strip() if formatted_port else None


def flash_file(filename, serial_port):
    try:
        # instantiate backend
        backend = Backend()

        # setup tool connection
        transport = ToolSerialConnection(
            serialport=serial_port, baudrate=115200, timeout=1.0
        )

        # connect to tool using transport
        # this can trigger a PymcuprogToolConnectionError exception
        backend.connect_to_tool(transport)

        # configure the session
        device = "attiny202"
        sessionconfig = SessionConfig(device)

        # start the session
        # this can trigger one of the following exceptions:
        #   PymcuprogDeviceLockedError
        #   PymcuprogNotSupportedError
        #   PymcuprogSessionConfigError
        backend.start_session(sessionconfig)

        # ping the device
        device_id = backend.read_device_id()

        # erase before write
        backend.erase(MemoryNameAliases.ALL, address=None)

        # write content of list of memory segments
        memory_segments = read_memories_from_hex(filename, backend.device_memory_info)
        for segment in memory_segments:
            memory_name = segment.memory_info[DeviceMemoryInfoKeys.NAME]
            # write
            backend.write_memory(segment.data, memory_name, segment.offset)
            # verify
            backend.verify_memory(segment.data, memory_name, segment.offset)
    except Exception as error:
        # if the exception is important, it was then handled by the logger
        print(error)
        return False

    return True
