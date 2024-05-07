# Copyright (C) 2024 saintnoodle <hi@noodle.moe>
#
# This program is free software:
# you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warrantyof MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from typing import TypedDict


PERCENT_START = 20
PERCENT_RANGE = 100 - PERCENT_START
VOLTAGE_START = 4
VOLTAGE_RANGE = 12 - VOLTAGE_START


class Command:
    """Initialise a command to send to the controller."""

    def __init__(self, hex_str: str, in_size: int, out_size: int):
        self.hex_str = hex_str
        """The command prefix as a hex string."""
        self.in_size = in_size
        """The expected byte size of the command being written."""
        self.out_size = out_size
        """The expected byte size of the response from the command."""


class CommandDict(TypedDict):
    PING: Command
    GET_RPM: Command
    GET_VOLTAGE: Command
    GET_WATTAGE: Command
    SET_FAN: Command


class GridFanError(Exception):
    """
    The Exception class for GridPlusAPI.

    Args:
        message (str): The error message
        code (int): The error code
    """

    def __init__(self, message: str, code: int) -> None:
        """Initialise the GridFanError with an error message and a code."""
        super().__init__(message)

        self.code = code
        """
        The error codes are as follows:

        1: A communication error occured
        2: The controller responded but its response was invalid or unexpected
        3: The expected arguments for a function were missing or invalid
        4: An internal error occured
        5: An unknown or unexpected error occured
        """
        self.message = message
        """The error message."""


def percent_to_voltage_hex(percent: int):
    """
    Convert a "percentage" into a valid voltage hex string.

    Args:
        percent (int): A percentage value either 0 or between 20-100.

    Returns:
        str: The voltage value as a hex string.
    """
    if percent == 0:
        return "0000"

    translation_factor = VOLTAGE_RANGE / PERCENT_RANGE
    # Range starts from 20 which is 4v. Values below this other than 0 are invalid.
    voltage = (
        (percent - PERCENT_START) if percent > PERCENT_START else 0
    ) * translation_factor + 4
    voltage_floor = int(voltage)

    # The controller only accepts increments of 0.5v
    # which greatly impacts precision...
    low_byte = "00" if voltage % 1 < 0.5 else "50"

    return f"{voltage_floor:02x}{low_byte}"


def voltage_to_percent(voltage: float) -> int:
    """
    Convert a voltage value into a percentage integer.

    Args:
        voltage (float): The voltage value.

    Returns:
        int: The percentage value.
    """
    if voltage == 0:
        return 0
    if voltage <= 4:
        # Because it will report values lower than 4...
        return 20
    elif voltage >= 12:
        return 100
    else:
        return (
            round(((voltage - VOLTAGE_START) / VOLTAGE_RANGE) * PERCENT_RANGE)
            + PERCENT_START
        )


def is_valid_channel(channel: int):
    """
    Check if the channel is valid.

    Args:
        channel (int): The fan's channel, between 1-6.

    Raises:
        GridFanError: Do not continue if the channel is out of bounds.

    Returns:
        True
    """
    if type(channel) is not int:
        raise GridFanError("Fan channel must be an int between 1 and 6.", 3)
    elif channel not in range(1, 7):
        raise GridFanError("Fan channel must be between 1 and 6.", 3)
    else:
        return True


def is_valid_speed(speed: int):
    """
    Check if the speed value is valid.

    Args:
        speed (int): The speed to set between 20-100% or 0.

    Raises:
        GridFanError: Do not continue if the speed value is invalid.

    Returns:
        True
    """
    if type(speed) is not int:
        raise GridFanError("Missing arg: speed.", 3)
    elif speed < 0:
        raise GridFanError(
            f"Invalid speed: {speed}. Speed must be a non-negative number", 3
        )
    elif speed > 100:
        raise GridFanError(f"Invalid speed: {speed}. Speed must be within 0-100", 3)
    else:
        return True


def is_valid_data(data: bytes):
    """
    Check if the data recieved by the controller is expected.

    Args:
        data (bytes): The data recieved from the controller.

    Raises:
        GridFanError: An error is raised if the data is invalid.
    """
    if type(data) is not bytes:
        raise GridFanError(f"Unexpected response type from send_command: {data}", 4)
    elif data[:3] != b"\xC0\x00\x00":
        raise GridFanError(f"Unexpected response from controller: {data}", 2)
