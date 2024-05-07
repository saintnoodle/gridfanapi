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


"""
GridFanAPI:

A set of methods for communicating with the NZXT Grid+ v2 fan controller
on Linux systems.

Refer to readme for appropriate setup.
"""

import serial
import time
import logging
from . import util
from .util import Command, CommandDict, GridFanError


logger = logging.getLogger("gridfanapi")
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(log_handler)


class GridFanAPI:
    """
    The class instance which configures the controller
    and exposes the main set of functions.
    """

    def __init__(self, device_name="GridPlus0", dir="/dev", log_level="WARNING"):
        """
        Args:
            device_name (str, optional): Name of the controller (Default: "GridFan0")
            dir (str, optional): Directory the controller resides (Default: "/dev")
            log_level (str, optional): The log level (Default: "WARNING")

        """
        self.device_name = device_name
        """The name of the controller"""
        self.device_loc = f"{dir}/{device_name}"
        """The location of the controller"""
        self.COMMAND: CommandDict = {
            "PING": Command("C0", 1, 1),
            "GET_RPM": Command("8A", 2, 5),
            "GET_VOLTAGE": Command("84", 2, 5),
            "GET_WATTAGE": Command("85", 2, 5),
            "SET_FAN": Command("44", 7, 1),
        }
        """The dict of known commands"""

        logger.setLevel(log_level)

    def connect(self):
        """
        Initialise a connection with the controller.

        Raises:
            GridFanError: _description_
            e: _description_

        Returns:
            Serial: A pyserial instance with a connection to the controller
        """
        try:
            controller = serial.Serial(
                port=self.device_loc, baudrate=4800, timeout=2, write_timeout=4
            )
        except serial.SerialException as e:
            logger.error(e)
            raise GridFanError(
                " ".join(
                    [
                        "Failed to initialise a connection with the controller.",
                        f"Check the controller exists at {self.device_loc}.",
                        "If it exists, make sure you have sufficient permissions.",
                    ]
                ),
                1,
            )

        return controller

    def send_command(self, command: Command, data=""):
        """
        Sends a command to the controller and returns the response.

        Args:
            command (Command): The command to send as initialised by the Command class.
            data (str, optional): Any hex data to send to the controller.

        Returns:
            bytes: The response from the Grid.
        """
        if not isinstance(command, Command):
            raise GridFanError("Invalid command.", 3)

        write_bytes = bytes.fromhex(command.hex_str + data)

        if len(write_bytes) != command.in_size:
            raise GridFanError(
                " ".join(
                    [
                        "Invalid input size.",
                        f"Expected: {command.in_size}.",
                        f"Recieved: {len(write_bytes)}.",
                    ]
                ),
                4,
            )

        controller = self.connect()

        logger.debug(f"Sending to controller: {write_bytes}")
        try:
            bytes_written = controller.write(write_bytes)
            logger.debug(f"Wrote {bytes_written} bytes.")

            response = controller.read(command.out_size)
            logger.debug(f"Controller responded: {response}")

        except serial.SerialException as e:
            raise GridFanError(f"Communication failure: {e.strerror}", 1)

        if not len(response) == command.out_size:
            raise GridFanError(f"Unexpected response from controller: {response}", 2)

        return response

    def ping(self):
        """
        Ping the controller.

        Returns:
            bool: True if the controller responds with the expected pong message.
        """
        try:
            response = self.send_command(self.COMMAND["PING"])

            if response.hex() == "21":
                logger.info("Pong!")
                return True
            elif response.hex() == "02":
                logger.warning(
                    "The controller returned an error code, but it responded"
                )
                return True
            else:
                logger.error(f"Unexpected response from controller: {response}")

        except GridFanError as error:
            logger.error(error.message)
        return False

    def init(self):
        """
        Initialise the controller.
        It might take a while before the controller responds,
        so we will ping it 30 times to wake it up.

        Returns:
            bool
        """
        retry = 0
        while retry < 30:
            if retry > 1:
                time.sleep(0.1)

            retry += 1
            if self.ping():
                return True

        if retry == 30:
            logger.error(f"Giving up after {retry} tries.")
            return False

    def get_fan_rpm(self, channel: int):
        """
        Get a fan's RPM.

        Args:
            channel (int): Which fan to get the RPM of, between 1-6.

        Returns:
            int: The RPM of the fan.
        """
        util.is_valid_channel(channel)
        logger.info(f"Getting rpm of fan {channel}")

        response = self.send_command(self.COMMAND["GET_RPM"], str(channel).zfill(2))
        util.is_valid_data(response)
        fan_rpm = int.from_bytes(response[3:5], byteorder="big")

        logger.info(f"Fan {channel}: {fan_rpm} RPM")

        return fan_rpm

    def get_fan_rpm_all(self):
        """
        Get a list of all fan speeds.

        Returns:
            list[int]: A list of all fan speeds.
        """
        fan_rpm_list: list[int] = []

        for i in range(6):
            fan_rpm = self.get_fan_rpm(i + 1)
            fan_rpm_list.append(fan_rpm)

        return fan_rpm_list

    def get_fan_voltage(self, channel: int):
        """
        Get the voltage the controller is currently supplying to a fan.
        If no fan is plugged into the target port, the voltage will always read ~12.

        Note that the voltage may fluctuate.

        Args:
            channel (int): Which fan to get the voltage of, between 1-6.

        Returns:
            float: The value of the current applied voltage (0_4-12)
        """
        util.is_valid_channel(channel)
        logger.info(f"Getting voltage of fan {channel}")

        response = self.send_command(self.COMMAND["GET_VOLTAGE"], str(channel).zfill(2))
        util.is_valid_data(response)
        high_byte = response[3:4]
        low_byte = response[4:5]

        voltage = round(int(high_byte.hex(), 16) + (int(low_byte.hex(), 16) / 100), 1)

        logger.info(f"Fan {channel}: {voltage}V")
        return voltage

    def get_fan_voltage_all(self):
        """
        Get all voltages.

        Note that the voltage may fluctuate.

        Returns:
            list[float]: A list of each fan's current applied voltage (0_4-12)
        """
        fan_voltage_list: list[float] = []

        for i in range(6):
            fan_voltage = self.get_fan_voltage(i + 1)
            fan_voltage_list.append(fan_voltage)

        return fan_voltage_list

    def get_fan_percent(self, channel: int):
        """
        Get the voltage the controller is currently supplying to a fan as a percentage.
        If no fan is plugged into the target port, the percent will always read ~100%.

        Note that this value should be read as voltage percentage
        and not fan speed percentage.

        Args:
            channel (int): Which fan to get the applied voltage of in percent, (1-6).

        Returns:
            int: The value of the current applied voltage as a percentage.
        """
        voltage = self.get_fan_voltage(channel)
        percent = util.voltage_to_percent(voltage)

        logger.info(f"Fan {channel}: Approximately {percent}%")

        return percent

    def get_fan_percent_all(self):
        """
        Get all voltages as percentage.

        Note that this value should be read as voltage percentage
        and not fan speed percentage.

        Returns:
            list[int]: A list of each fan's current applied voltage as a percentage.
        """
        percent_list: list[int] = []
        voltage_list = self.get_fan_voltage_all()

        for voltage in voltage_list:
            percent_list.append(util.voltage_to_percent(voltage))

        return percent_list

    def get_fan_wattage(self, channel: int):
        """
        Get a fan's power consumption.

        Args:
            channel (int): _description_

        Returns:
            float: A fan's power consumption in Watts
        """
        util.is_valid_channel(channel)

        logger.info(f"Getting wattage of fan {channel}")

        response = self.send_command(self.COMMAND["GET_WATTAGE"], str(channel).zfill(2))
        util.is_valid_data(response)
        wattage = int(response[4:5].hex()) / 10

        logger.info(f"Fan {channel}: {wattage}W")

        return wattage

    def get_fan_wattage_all(self):
        """
        Get all wattages.

        Returns:
            list[float]: A list of each fan's power consumption in Watts.
        """
        fan_wattage_list: list[float] = []

        for i in range(6):
            fan_wattage = self.get_fan_wattage(i + 1)
            fan_wattage_list.append(fan_wattage)

        return fan_wattage_list

    def set_fan(self, channel: int, speed: int | float):
        """
        Set the speed of a fan by its ID.

        Args:
            channel (int): Which fan to set the speed of, between 1-6.
            speed (int | float): The speed to set between 20-100% or 0.

        Returns:
            bool: True if speed successfully set.
        """
        util.is_valid_channel(channel)
        util.is_valid_speed(speed)

        logger.info(f"Setting fan {channel} to {speed}% speed")

        speed_hex = util.percent_to_voltage_hex(speed)
        data = str(channel).zfill(2) + "c00000" + speed_hex

        logger.debug(f"sending {data} to channel {channel}")
        response = self.send_command(self.COMMAND["SET_FAN"], data)

        if response.hex() == "01":
            logger.info(f"Fan {channel}'s speed successfully set to {speed}%")
            return True
        elif response:
            raise GridFanError(
                " ".join(
                    [
                        f"Failed to set fan {channel};",
                        f"invalid response from controller: {response}",
                    ]
                ),
                2,
            )
        else:
            raise GridFanError(
                f"Failed to set fan {channel}; no response from controller.", 1
            )

    def set_fan_all(self, speed: int):
        """
        Set all fans to one speed.

        Args:
            speed (int): The speed between 20-100% or 0.
        """
        util.is_valid_speed(speed)

        for i in range(6):
            self.set_fan(i + 1, speed)

        return True

    def is_fan_connected(self, channel: int):
        """
        Check if a fan is connected or alive.
        It cannot be guaranteed that the result from this is 100% correct,
        but it is likely more correct than not.

        Args:
            channel (int): Which fan channel to check.

        Raises:
            e: Raises a GridFanError if it cannot succeed after 3 attempts.

        Returns:
            bool: Whether the fan is connected.
        """
        util.is_valid_channel(channel)
        retry = 0
        fan_was_off: bool = False
        logger.info(f"Checking if a fan is connected on channel {channel}")

        while True:
            try:
                # Attempt some error recovery
                if retry > 0:
                    logger.info("Something went wrong... Attempting to recover.")
                    self.init()
                    logger.info("Trying again.")

                fan_voltage = self.get_fan_voltage(channel)
                fan_wattage = self.get_fan_wattage(channel)

                logger.debug(f"fan {channel}: {fan_voltage}V - {fan_wattage}W")

                # If the channel is set to off, wake it to perform the check
                if fan_voltage == 0:
                    logger.info("The channel was off. waking up...")
                    fan_was_off = True
                    self.set_fan(channel, 100)
                    time.sleep(1)
                    continue

                # Turn the fan back off if it was off before
                if fan_was_off:
                    logger.debug("Turning channel back off.")
                    self.set_fan(channel, 0)

                # If there's no rpm value and the wattage is 0 whilst the controller
                # is supplying a high voltage, there is no fan connected or
                # there is a problem.
                #
                # For those interested, if the controller cannot detect a readout
                # from a fan, it will supply full power in an attempt to wake it.
                # Of course, if there is no fan, there will never be a readout,
                # so the voltage will be 12 and the rpm will be 0 regardless of
                # what voltage was set.
                if fan_wattage == 0 and fan_voltage > 11:
                    return False
                else:
                    return True

            except GridFanError as e:
                retry += 1
                if retry >= 3:
                    raise e
