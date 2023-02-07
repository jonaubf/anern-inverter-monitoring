import ctypes
import re
import time
from threading import Lock

import serial


class BasicCommand:
    command: bytes = b''
    response_fmt: re.Pattern = re.compile('')
    response_typing: dict = {}

    @staticmethod
    def compute_crc(message: str) -> bytes:
        crc = 0
        crc_ta = [
            0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef
        ]

        for c in message:
            c = ord(c)

            t_da = ctypes.c_uint8(crc >> 8)
            da = t_da.value >> 4
            crc <<= 4
            index = da ^ (c >> 4)
            crc ^= crc_ta[index]
            t_da = ctypes.c_uint8(crc >> 8)
            da = t_da.value >> 4
            crc <<= 4
            index = da ^ (c & 0x0f)
            crc ^= crc_ta[index]

        crc_low = ctypes.c_uint8(crc).value
        crc_high = ctypes.c_uint8(crc >> 8).value

        if crc_low in (0x28, 0x0d, 0x0a):
            crc_low += 1

        if crc_high in (0x28, 0x0d, 0x0a):
            crc_high += 1

        return bytes((crc_high, crc_low))

    def fmt_command(self) -> bytes:
        crc = self.compute_crc(self.command.decode('utf8'))
        return self.command + crc + b'\r'


class QPIRI(BasicCommand):
    command = b'QPIRI'


class QPIGS(BasicCommand):
    command = b'QPIGS'
    response_fmt = re.compile(
        r'(?P<grid_voltage>\d{3}\.\d{1}) '  # V
        r'(?P<grid_frequency>\d{2}\.\d{1}) '  # Hz
        r'(?P<ac_output_voltage>\d{3}\.\d{1}) '  # V
        r'(?P<ac_output_frequency>\d{2}\.\d{1}) '  # Hz
        r'(?P<ac_output_apparent_power>\d{4}) '  # VA
        r'(?P<ac_output_active_power>\d{4}) '  # W
        r'(?P<ac_output_load>\d{3}) '  # %
        r'(?P<bus_voltage>\d{3}) '  # V
        r'(?P<battery_voltage>\d{2}\.\d{2}) '  # V
        r'(?P<battery_charging_current>\d{3}) '  # A
        r'(?P<battery_percent>\d{3}) '  # %
        r'(?P<heat_sink_temperature>\d{4}) '  # C
        r'(?P<pv_current>\d{2}\.\d{1}) '  # A
        r'(?P<pv_voltage>\d{3}\.\d{1}) '  # C
        r'(?P<scc_voltage>\d{2}\.\d{2}) '  # V
        r'(?P<battery_discharge_current>\d{5}) '  # A
        r'(?P<smth_1>\d{8}) '  #
        r'(?P<smth_2>\d{2}) '  #
        r'(?P<smth_3>\d{2}) '  #
        r'(?P<pv_power>\d{5}) '  # W
        r'(?P<smth_4>\d{3})'  #
    )
    response_typing = {
        'grid_voltage': float,
        'grid_frequency': float,
        'ac_output_voltage': float,
        'ac_output_frequency': float,
        'ac_output_apparent_power': int,
        'ac_output_active_power': int,
        'ac_output_load': int,
        'bus_voltage': int,
        'battery_voltage': float,
        'battery_charging_current': int,
        'battery_percent': int,
        'heat_sink_temperature': int,
        'pv_current': float,
        'pv_voltage': float,
        'scc_voltage': float,
        'battery_discharge_current': int,
        'smth_1': str,
        'smth_2': int,
        'smth_3': int,
        'pv_power': int,
        'smth_4': int,
    }


class Inverter:
    BAUD = 2400
    PARITY = serial.PARITY_NONE
    TIMEOUT = 1

    _comm_port = None

    def __init__(self, serial_device: str) -> None:
        self.serial_device: str = serial_device
        self._lock: Lock = Lock()

    @property
    def comm_port(self):
        if self._comm_port is None:
            self._comm_port = serial.Serial(
                port=self.serial_device,
                baudrate=self.BAUD,
                parity=self.PARITY,
                timeout=self.TIMEOUT
            )
        return self._comm_port

    def _parse_response(self, response: bytes, command_cls: BasicCommand) -> dict:
        if not response.startswith(b'('):
            raise RuntimeError('Got bad response from inverter')
        if not response.endswith(b'\r'):
            raise RuntimeError('Got bad response from inverter')

        stripped_response = response[1:-3].decode('utf-8')
        response_fmt = command_cls.response_fmt
        response_typing = command_cls.response_typing
        response_crc = BasicCommand.compute_crc(stripped_response)

        parsed_response = response_fmt.match(stripped_response)
        if parsed_response is None:
            raise RuntimeError('Inverter response does not match expected format')

        return {
            key: response_typing[key](value)
            for key, value in parsed_response.groupdict().items()
        }

    def get_qpigs(self) -> dict:
        qpigs = QPIGS()
        with self._lock:
            self.comm_port.write(qpigs.fmt_command())
            time.sleep(0.5)
            response = self.comm_port.readline()
        return self._parse_response(response, qpigs)

    def get_qpiri(self) -> bytes:
        qpiri_command = QPIRI()
        with self._lock:
            self.comm_port.write(qpiri_command.fmt_command())
            time.sleep(0.5)
            response = self.comm_port.readline()
        return response.strip()
