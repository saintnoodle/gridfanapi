# Copyright (C) 2024 saintnoodle <hi@noodle.moe>
#
# This program is free software:
# you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warrantyof MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

import pytest
from serial import Serial, SerialException
from gridfanapi import GridFanAPI
from gridfanapi.util import Command, GridFanError


@pytest.fixture
def mock_serial(mocker):
    """A mock Serial instance"""
    return mocker.patch("serial.Serial", autospec=Serial)


@pytest.fixture
def mock_serial_exception(mocker):
    """
    A mock Serial instance that raises an exception.
    """
    return mocker.patch("serial.Serial", autospec=Serial, side_effect=SerialException)


@pytest.fixture
def mock_send_command(mocker):
    """
    Mocks the send_command function which contains a Serial connection.
    Tests using this fixture only require its return value.

    Use mock_serial to test lower level functionality.
    """
    return mocker.patch("gridfanapi.GridFanAPI.send_command")


@pytest.fixture
def mock_send_command_exception(mocker):
    """
    Mocks an exception raised by the send_command function.
    Tests using this fixture should handle this exception appropriately.
    """
    return mocker.patch("gridfanapi.GridFanAPI.send_command", side_effect=GridFanError)


@pytest.fixture
def mock_fan_voltage(mocker):
    return mocker.patch("gridfanapi.GridFanAPI.get_fan_voltage")


@pytest.fixture
def mock_fan_wattage(mocker):
    return mocker.patch("gridfanapi.GridFanAPI.get_fan_wattage")


def test_connect_success(mock_serial):
    """Just a quick check that the connect function does in fact return correctly"""
    assert isinstance(
        GridFanAPI(device_name="mock_device", dir="/dev").connect(), Serial
    )
    mock_serial.assert_called_once_with(
        port="/dev/mock_device", baudrate=4800, timeout=2, write_timeout=4
    )


def test_connect_disconnected(mock_serial_exception):
    """
    If the controller doesn't exist, we should expect an exception from Serial.
    Said exception should be handled and re-raised with GridFanError as code 1.
    """
    gridfan = GridFanAPI("nonexistent_device", "~")
    with pytest.raises(GridFanError) as exc_info:
        gridfan.connect()

    assert exc_info.value.code == 1


def test_send_command_success(mock_serial):
    """Simulate a request to get fan speed from channel 1."""
    gridfan = GridFanAPI()
    controller = gridfan.connect()

    command = Command(hex_str="8A", in_size=2, out_size=5)
    data = "01"

    expected_write = bytes.fromhex(command.hex_str + data)
    mock_response = b"\xc0\x00\x00\x01\xc2"

    controller.write.return_value = command.in_size
    controller.read.return_value = mock_response

    response = gridfan.send_command(command, data)

    controller.write.assert_called_once_with(expected_write)
    controller.read.assert_called_once_with(command.out_size)

    assert response == mock_response


def test_send_command_error(mock_serial):
    """
    If the controller responds to a command with its error code "02",
    an exception should raise with error code 2
    """
    gridfan = GridFanAPI()
    controller = gridfan.connect()

    command = Command(hex_str="8A", in_size=2, out_size=5)
    data = "01"

    mock_response = b"\x02"

    controller.write.return_value = command.in_size
    controller.read.return_value = mock_response

    with pytest.raises(GridFanError) as exc_info:
        gridfan.send_command(command, data)

    assert exc_info.value.code == 2


def test_send_command_no_response(mock_serial):
    """
    If the controller doesn't respond or the response is unexpected,
    an exception should raise with error code 2
    """
    gridfan = GridFanAPI()
    controller = gridfan.connect()

    command = Command(hex_str="8A", in_size=2, out_size=5)
    data = "01"

    mock_response = b""

    controller.write.return_value = command.in_size
    controller.read.return_value = mock_response

    with pytest.raises(GridFanError) as exc_info:
        gridfan.send_command(command, data)

    assert exc_info.value.code == 2


def test_send_command_invalid_command(mock_serial):
    """Test that the command function raises on an invalid command with code 3"""
    invalid_command = "invalid"
    data = "01"

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().send_command(invalid_command, data)  # type: ignore

    assert exc_info.value.code == 3


def test_send_command_serial_error(mock_serial_exception):
    """
    Test whether the command function fails successfuly with the correct code
    when the device is not connected and Serial raises an exception
    """
    command = Command(hex_str="8A", in_size=2, out_size=5)
    data = "01"

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().send_command(command, data)

    assert exc_info.value.code == 1


def test_ping_success(mock_send_command):
    """The controller responds with "21" on a successful hello command."""

    mock_send_command.return_value = b"\x21"

    assert GridFanAPI().ping() is True


def test_ping_error(mock_send_command):
    """
    The controller responds with "02" if an error occured.
    We return True because the controller is alive and will
    respond correctly to the next command

    The only difference is the log message which warns about the error code.
    """
    mock_send_command.return_value = b"\x02"
    assert GridFanAPI().ping() is True


def test_ping_no_response(mock_send_command):
    """Sometimes the controller doesn't respond."""
    mock_send_command.return_value = b""
    assert GridFanAPI().ping() is False


def test_get_fan_rpm_success(mock_send_command):
    """Make sure we return an int of an expected value."""
    mock_send_command.return_value = b"\xc0\x00\x00\x01\xc2"

    assert GridFanAPI().get_fan_rpm(1) == 450


def test_get_fan_rpm_all_success(mock_send_command):
    """Make sure we return an array of ints as expected and the loop runs without obstruction"""
    mock_send_command.return_value = b"\xc0\x00\x00\x01\xc2"

    assert GridFanAPI().get_fan_rpm_all() == [450, 450, 450, 450, 450, 450]


def test_get_fan_rpm_invalid_response(mock_send_command):
    """If the controller doesn't respond as expected, an exception should be raised"""
    mock_send_command.return_value = b""

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().get_fan_rpm(1)

    assert exc_info.value.code == 2


def test_get_fan_voltage_success(mock_send_command):
    """Test that the voltage is correctly converted and returned."""
    # I'm unsure why the last byte is text, but we'll roll with it
    mock_send_command.return_value = b"\xc0\x00\x00\x079"

    assert GridFanAPI().get_fan_voltage(1) == 7.6


def test_get_fan_voltage_all_success(mock_send_command):
    """Make sure we return an array of floats as expected."""
    mock_send_command.return_value = b"\xc0\x00\x00\x079"

    assert GridFanAPI().get_fan_voltage_all() == [
        7.6,
        7.6,
        7.6,
        7.6,
        7.6,
        7.6,
    ]


def test_get_fan_percent_success(mock_send_command):
    """Test that the voltage is correctly converted and returned."""
    mock_send_command.return_value = b"\xc0\x00\x00\x079"

    assert GridFanAPI().get_fan_percent(1) == 56


def test_get_fan_percent_all_success(mock_send_command):
    """Make sure we return an array of ints as expected."""
    mock_send_command.return_value = b"\xc0\x00\x00\x079"

    assert GridFanAPI().get_fan_percent_all() == [
        56,
        56,
        56,
        56,
        56,
        56,
    ]


def test_get_fan_wattage_success(mock_send_command):
    """Test that the wattage is correctly returned."""
    mock_send_command.return_value = b"\xc0\x00\x00\x00\x14"

    assert GridFanAPI().get_fan_wattage(1) == 1.4


def test_get_fan_wattage_all_success(mock_send_command):
    """Make sure we return an array of floats as expected."""
    mock_send_command.return_value = b"\xc0\x00\x00\x00\x14"

    assert GridFanAPI().get_fan_wattage_all() == [
        1.4,
        1.4,
        1.4,
        1.4,
        1.4,
        1.4,
    ]


def test_set_fan_success(mock_send_command):
    """A simple test to make sure we get the expected result."""
    mock_send_command.return_value = b"\01"

    assert GridFanAPI().set_fan(1, 55) is True


def test_set_fan_all_success(mock_send_command):
    """A simple test to make sure we correctly iterate over all the fans."""
    mock_send_command.return_value = b"\01"

    assert GridFanAPI().set_fan_all(55) is True


def test_invalid_channel_input(mock_send_command):
    """
    If an invalid channel is passed to a get/set function,
    we should raise an arg error code 3 exception.
    """
    # If a controller doesn't recognise a request,
    # we will likely timeout before it sends its error code
    # and recieve an empty response from Serial
    mock_send_command.return_value = b""

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().get_fan_rpm(7)

    assert exc_info.value.code == 3
    assert not mock_send_command.called


def test_invalid_channel_input_negative(mock_send_command):
    """The same test as above but with a negative int."""
    mock_send_command.return_value = b""

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().get_fan_rpm(-1)

    assert exc_info.value.code == 3
    assert not mock_send_command.called


def test_invalid_channel_input_type(mock_send_command):
    """The same test as above but with an incorrect type."""
    mock_send_command.return_value = b""

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().get_fan_rpm(False)  # type: ignore

    assert exc_info.value.code == 3
    assert not mock_send_command.called


def test_invalid_speed_input(mock_send_command):
    """
    A speed value outside of the range of 0-100 should cause
    an exception to be raised with code 3
    """
    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().set_fan(1, 150)

    assert exc_info.value.code == 3
    assert not mock_send_command.called


def test_invalid_speed_input_negative(mock_send_command):
    """
    A speed value outside of the range of 0-100 should cause
    an exception to be raised with code 3
    """
    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().set_fan(1, -1)

    assert exc_info.value.code == 3
    assert not mock_send_command.called


def test_invalid_speed_input_type(mock_send_command):
    """
    A speed value outside that isn't an int should cause
    an exception to be raised with code 3
    """
    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().set_fan(1, False)  # type: ignore

    assert exc_info.value.code == 3
    assert not mock_send_command.called


def test_is_connected(mock_fan_voltage, mock_fan_wattage):
    """Fan connected condition"""
    mock_fan_voltage.return_value = 6
    mock_fan_wattage.return_value = 0.4

    assert GridFanAPI().is_fan_connected(1) is True


def test_is_connected_no_fan(mock_fan_voltage, mock_fan_wattage):
    """Fan not connected condition"""
    mock_fan_voltage.return_value = 11.8
    mock_fan_wattage.return_value = 0

    assert GridFanAPI().is_fan_connected(1) is False


def test_is_connected_off(mocker, mock_fan_voltage, mock_fan_wattage):
    """
    Make sure that if the fan was off before,
    it gets turned on and back off during the check.
    """
    mock_set_fan = mocker.patch("gridfanapi.GridFanAPI.set_fan")

    def voltage_side_effect(*args, **kwargs):
        if mock_fan_voltage.call_count == 1:
            return 0
        elif mock_fan_voltage.call_count == 2:
            return 6
        else:
            pytest.fail("Unexpected call to get_fan_voltage")

    def wattage_side_effect(*args, **kwargs):
        if mock_fan_wattage.call_count == 1:
            return 0
        elif mock_fan_wattage.call_count == 2:
            return 0.4
        else:
            pytest.fail("Unexpected call to get_fan_wattage")

    mock_fan_voltage.side_effect = voltage_side_effect
    mock_fan_wattage.side_effect = wattage_side_effect
    mock_set_fan.return_value = b"\x01"

    assert GridFanAPI().is_fan_connected(1) is True
    assert mock_set_fan.call_count == 2


def test_is_connected_off_no_fan(mocker, mock_fan_voltage, mock_fan_wattage):
    mock_set_fan = mocker.patch(
        "gridfanapi.GridFanAPI.set_fan",
    )

    def voltage_side_effect(*args, **kwargs):
        if mock_fan_voltage.call_count == 1:
            return 0
        elif mock_fan_voltage.call_count == 2:
            return 11.8
        else:
            pytest.fail("Unexpected call to get_fan_voltage")

    def wattage_side_effect(*args, **kwargs):
        if mock_fan_wattage.call_count == 1:
            return 0
        elif mock_fan_wattage.call_count == 2:
            return 0
        else:
            pytest.fail("Unexpected call to get_fan_wattage")

    mock_fan_voltage.side_effect = voltage_side_effect
    mock_fan_wattage.side_effect = wattage_side_effect

    assert GridFanAPI().is_fan_connected(1) is False
    assert mock_set_fan.call_count == 2


def test_is_connected_no_response(mocker, mock_send_command):
    """Make sure this function retries 3 times, attempting error recovery."""
    mock_init = mocker.patch("gridfanapi.GridFanAPI.init")
    mock_send_command.return_value = b""

    with pytest.raises(GridFanError) as exc_info:
        GridFanAPI().is_fan_connected(1)

    assert mock_init.call_count == 2
    assert mock_send_command.call_count == 3
    assert exc_info.value.code == 2
