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

from gridfanapi import util
import pytest


def test_percent_to_voltage_zero():
    """Test percent_to_voltage_hex utility with a value of zero."""

    assert util.percent_to_voltage_hex(0) == "0000"


def test_voltage_to_percent_in_range():
    """Test voltage_to_percent utility with a normal value."""

    assert util.voltage_to_percent(7.6) == 56


def test_voltage_to_percent_zero():
    """Test voltage_to_percent utility with a value of zero."""

    assert util.voltage_to_percent(0) == 0


def test_voltage_to_percent_below_range():
    """Test voltage_to_percent utility with a value below 4v."""

    assert util.voltage_to_percent(3.75) == 20


def test_voltage_to_percent_above_range():
    """Test voltage_to_percent utility with a value above 12v."""

    assert util.voltage_to_percent(12.25) == 100


def test_is_valid_data_invalid_type():
    """
    Test case where data passed to is_valid_data is not type of bytes.

    Only likely to occur if the method is misused.
    """
    with pytest.raises(util.GridFanError) as exc_info:
        util.is_valid_data("invalid data")

        assert exc_info.value.code == 4
