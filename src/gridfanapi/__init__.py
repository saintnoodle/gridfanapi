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


from importlib.metadata import version

__version__ = version("gridfanapi")

from gridfanapi.gridfanapi import GridFanAPI, GridFanError
from gridfanapi import util
