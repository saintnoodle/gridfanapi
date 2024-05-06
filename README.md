# GridFanAPI

A python module that exposes a set of methods for communicating with the NZXT Grid+ V2 fan controller on Linux.

## About

This is a simple module designed to be imported into other scripts or projects that involve the use of the Grid+ V2 fan controller by NZXT on Linux systems.
The controller is a simple serial device that does very little on its own and requires additional software to be useful. The controller has an official utility for windows, CAM (although versions later than `3.5.90` remove a lot of features from anything but the latest NZXT devices). However, on Linux the Grid+ cannot be controlled natively with readily available applications.

The module exposes some methods to initialise and ping the device if neccessary and to control and monitor fans.

## Usage

To use GridFanAPI in your project, simply import the module and call the class.

Example:

Default:

```
from gridfanapi import GridFanAPI

gridfan = GridFanAPI()

print(gridfan.get_fan_rpm(1))
```

With alternative device location:

```
from gridfanapi import GridFanAPI

gridfan = GridFanAPI("ttyACM0")
```

Debug:

```
from gridfanapi import GridFanAPI

gridfan = GridFanAPI(log_level="DEBUG")
```

## Configuration

The module requires no configuration, however, if for whatever reason you are unable to create a udev rule as the setup details, or simply don't feel the need, the device's path can be set by passing it as an argument to the class or by specifying with `device_name=`. The log level can also be adjusted by passing `log_level=`.

## Setup

### Confirm the controller

Plug in the controller and run `lsusb`. The controller should report as `04d8:00df Microchip Technology, Inc. MCP2200 USB Serial Port Emulator`. The controller should show up in `/dev` as `ttyACM0`. If it doesn't, take note of its name.

**Please note**: The controller doesn't report uniquely identifiable information so it's useful to take note of the serial number.

### Get the serial number of the controller

Run the following command and take note of the result.

`udevadm info -a -p $(udevadm info -q path -n /dev/ttyACM0) | egrep "ATTRS{serial}==\"[0-9]{10}\""`

### Create a udev rule

If you don't already have a group for running commands or accessing files with elevated permissions, create one now and asign only users you trust with controlling fans as misuse could cause the system to overheat potentially leading to failure.
Make sure to replace the serial in this command with the serial you got from the previous command. Also replace the group with the group on your system you want to give permissions to the controller to.
Run the following command as root making sure to replace the placeholders:

`echo 'ACTION=="add", SUBSYSTEMS=="usb", ATTRS{product}=="MCP2200 USB Serial Port Emulator", ATTRS{serial}=="<MY_SERIAL>", SUBSYSTEM=="tty", GROUP="<MY_GROUP>" MODE="0660" SYMLINK+="GridPlus0"' > /etc/udev/rules.d/90-NZXT-Grid+_v2.rules`

### Reset the controller

You will need to unplug and plug the controller back in to apply the new rule.

### Initialise the controller

On the first time the controller is used after a boot, the controller will need to be initialised. Ensure your script or application uses or exposes the init method and can initialise the controller before usage.

## Troubleshooting

If the controller appears to be unresponsive, first check the controller exists by running `ls /dev/GridPlus0`. If it exists and you are not root, it is important to ensure your user account has read and write permissions to the controller.

If the controller is responding with empty bytes or with `0x02`, which is an error code, try again or run the init function.

## Special Thanks

This module was inspired by the shell script [gridfan](https://github.com/CapitalF/gridfan).
