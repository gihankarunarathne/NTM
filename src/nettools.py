# -*- coding: UTF-8 -*-

#
# NTM Copyright (C) 2009-2011 by Luigi Tullio <tluigi@gmail.com>.
#
#   NTM is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
#   NTM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# -*- coding: UTF-8 -*-


import dbus


## + return the device dbus object ##
def get_obj_path(bus, device_interface):
    nm_obj = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
    manager = dbus.Interface(nm_obj, dbus_interface='org.freedesktop.NetworkManager')
    devices = manager.GetDevices()
    
    for d in devices:
        dev_obj = bus.get_object("org.freedesktop.NetworkManager", d)
        prop_iface = dbus.Interface(dev_obj, "org.freedesktop.DBus.Properties")
        interface = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Interface")
        if (interface == device_interface):
            return (d, prop_iface)
    
    return ("", None)
## - ##


## + disconnect the device  ##
def disconnect_device(bus, device_interface):
    device = get_obj_path(bus, device_interface)
    print("device :")
    print(device[0])
    if (device[0] != ""):
        proxy = bus.get_object('org.freedesktop.NetworkManager', device[0])
        ifaceNMDev = dbus.Interface(proxy, dbus_interface='org.freedesktop.NetworkManager.Device')
        ifaceNMDev.Disconnect()
## - ##

