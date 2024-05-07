# GridFanAPI

A python module that exposes a set of methods for communicating with the NZXT Grid+ V2 fan controller on Linux.

## About

This is a simple module designed to be imported into other scripts or projects that involve the use of the Grid+ V2 fan controller by NZXT on Linux systems.
The controller is a simple serial device that does very little on its own and requires additional software to be useful. The controller has an official utility for windows, CAM (although versions later than `3.5.90` remove a lot of features from anything but the latest NZXT devices). However, on Linux the Grid+ cannot be controlled natively with readily available applications.

The module exposes some methods to initialise and ping the controller if neccessary and to control and monitor fans.

## Usage

To use GridFanAPI in your project, simply import the module and call the class.

Example:

```
from gridfanapi import GridFanAPI

gridfan = GridFanAPI()

print(gridfan.get_fan_rpm(1))
```

With alternative controller location:

```
from gridfanapi import GridFanAPI

gridfan = GridFanAPI("ttyACM0")  # /dev/ttyACM0
```

Change log level:

```
from gridfanapi import GridFanAPI

gridfan = GridFanAPI(log_level="DEBUG")
```

## Configuration

The module requires no additional configuration after setup, however, if you are unable to create a udev rule as the setup details, or simply don't feel the need, you can pass your controllers's path with `device_name=` and `dir=` when calling the class.

## Setup

### Confirm the controller

Plug in the controller and run `lsusb`. The controller should report as `04d8:00df Microchip Technology, Inc. MCP2200 USB Serial Port Emulator`. It should show up in `/dev` as `ttyACM0`. If it exists under a different name, like `ttyACM1`, take note.

**Please note**: The controller doesn't report uniquely identifiable product or vendor information, so it's useful to take note of the serial number.

### Get the serial number of the controller

Run the following command and take note of the result. If your controller doesn't exist at `/dev/ttyACM0`, modify the command with your controller's location.

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

## Notes

For whatever reason, when a fan stops moving or stops reporting its speed, if the controller cannot get it to spin back up again, it will simply report its last known speed. If you change the speed of a fan and the RPM stays the same, it is a good indication that the fan has died.

There is a known issue with PWM fans where below a certain voltage, not far from 12v, they will fail and stop reporting speeds causing the controller to kick back up to 12v then reduce the voltage again. This causes an issue where the fan will cyclically slow down, or stop, and ramp back up to full speed. Some PWM fans may still work, and many will require power higher than the default 40%, but it is recommended to use 3-pin fans as they do not suffer from this issue as often.

If a fan isn't plugged in, the RPM and wattage will always read 0. This is the basis for the `is_fan_connected` method.

When using this module, since speeds below 20% aren't supported by the controller, any value below 20 passed to `set_fan` will be corrected to 20. The same goes for values outside of increments of 5, as the controller only supports values in increments of 5. This makes it safe and easy to create scripts that poll system telemetrics and maps values to corresponding fan speeds.

## Special Thanks

This module was inspired by the shell script [gridfan](https://github.com/CapitalF/gridfan).
