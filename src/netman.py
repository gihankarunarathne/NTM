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

import gobject
import dbus
import re
import sys
import subprocess

from event import Event
import ntmtools
import nettools
from device import Device


# dbus_interface="org.freedesktop.NetworkManager", signal_name="StateChanged"
NM_STATE_UNKNOWN = 0
NM_STATE_ASLEEP = 1
NM_STATE_CONNECTING = 2
NM_STATE_CONNECTED = 3 
NM_STATE_DISCONNECTED = 4

# dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged"
NM_DEVICE_STATE_UNKNOWN = 0 
NM_DEVICE_STATE_UNMANAGED = 1
NM_DEVICE_STATE_UNAVAILABLE = 2
NM_DEVICE_STATE_DISCONNECTED = 3
NM_DEVICE_STATE_PREPARE = 4
NM_DEVICE_STATE_CONFIG = 5
NM_DEVICE_STATE_NEED_AUTH = 6
NM_DEVICE_STATE_IP_CONFIG = 7
NM_DEVICE_STATE_ACTIVATED = 8
NM_DEVICE_STATE_FAILED = 9


### + ###
class NetMan():


    ## + ##
    # mode: 0-> NetworkManager; 1-> Ping
    def __init__(self, mode, interface):
        self.mode = None
        self.interface = interface

        self.online_event = Event()
        self.offline_event = Event()

        self.deviceAdded_event = Event()
        self.deviceRemoved_event = Event()

        self.state = -1

        # Active mainloop
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)

        # Create object for using system bus from d-bus
        self.bus = dbus.SystemBus()

        (self.device_path, prop_iface) = nettools.get_obj_path(self.bus, interface)
        if (self.device_path == ""):
            self.state = -1
            self.device_info = None
        else:
            self.state = prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
            self.bus.add_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)
            modems = self.get_modems()
            #ntmtools.dbg_msg("Modems:\n{0}\n".format(modems))
            self.device_info = Device(self.bus, self.device_path, modems)

        self.bus.add_signal_receiver(self.nm_h_device_added, dbus_interface="org.freedesktop.NetworkManager", signal_name="DeviceAdded")
        self.bus.add_signal_receiver(self.nm_h_device_removed, dbus_interface="org.freedesktop.NetworkManager", signal_name="DeviceRemoved")

        self.ping_test_url = 'google.com'
        self.check_line = re.compile(r"(\d) received")

        self.set_interface(self.interface)
        self.set_mode(mode)

        self.online = self.get_state()

        self.update_timer_interval = 5;


        gobject.timeout_add(self.update_timer_interval * 1000, self.update_timer_handler)
    ## - ##

    ## + ##
    # mode = 0:NetworkManager; 1:PingMode;
    def set_mode(self, mode):
        ntmtools.dbg_msg("NetMan.setMode({0})".format(mode))

        if self.mode != mode:

            if (self.mode == 0):
                self.bus.remove_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)

            self.mode = mode

            if (mode == 0):
                try:
                    self.bus.add_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)
                except:
                    ntmtools.dbg_msg("Unexpected error: " + str(sys.exc_info()))
            elif (mode == 1):
                gobject.timeout_add(2000, self.ping_test)

        ntmtools.dbg_msg("END - NetMan.setMode")
    ## - ##

    ## + ##
    def set_interface(self, interface):
        ntmtools.dbg_msg("NetMan.setInterface - interface:{0}".format(interface))

        (new_device_path, new_prop_iface) = nettools.get_obj_path(self.bus, interface)
        ntmtools.dbg_msg("NetMan.setInterface - device_path:{0}".format(new_device_path, new_prop_iface))

        if (self.mode == 0):
            if (new_device_path == ""):
                self.set_offline()
            else:
                self.bus.remove_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)
                self.device_path = new_device_path

                try:
                    self.bus.add_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)
                    modems = self.get_modems()
                    self.device_info = Device(self.bus, self.device_path, modems)
                except:
                    ntmtools.dbg_msg("Unexpected error: " + str(sys.exc_info()))
                
                if (self.get_state()):
                    self.set_online()
                else:
                    self.set_offline()
        else: # ping
            None

        self.device_path = new_device_path
        self.interface = interface            

        ntmtools.dbg_msg("END - NetMan.setInterface")
    ## - ##


    ## + ##
    # return true if active (online)
    def get_state(self):
        ntmtools.dbg_msg("NetMan.get_state")

        retVal = None

        if self.mode == 0:
            if (self.device_path != ""):
                dev_proxy = self.bus.get_object("org.freedesktop.NetworkManager", self.device_path)
                prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
                state = prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
                retVal = (state == NM_DEVICE_STATE_ACTIVATED)
            else:
                retVal = False
                '''
                proxy = self.bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
                iface = dbus.Interface(proxy, dbus_interface='org.freedesktop.DBus.Properties')
                active_connections = iface.Get('org.freedesktop.NetworkManager', 'ActiveConnections')
                try:
                    state = self.prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
                    return (state == 8)
                except:
                    ntmtools.dbgMsg(_("Unexpected error: ") + str(sys.exc_info()))
                    return False
                '''
        elif self.mode == 1:
            status = self.get_ping_test()
            retVal = status
        else:
            ntmtools.dbg_msg("Wrong value for online check mode.\n")
            retVal = False

        ntmtools.dbg_msg("END - NetMan.get_state -> {0}".format(retVal))
        return retVal
    ## - ##

    ## + ##
    # handler()
    def add_online_handler(self, handler):
        self.online_event += handler
    ## - ##

    ## + ##
    # handler()
    def add_offline_handler(self, handler):
        self.offline_event += handler
    ## - ##

    ## + ##
    # handler(object_path)
    def add_device_added_handler(self, handler):
        self.deviceAdded_event += handler
    ## - ##

    ## + ##
    # handler(object_path)
    def add_device_removed_handler(self, handler):
        self.deviceRemoved_event += handler
    ## - ##

    ## + ##
    def set_online(self):
        ntmtools.dbg_msg("NetMan.set_online")

        if not self.online:
            self.online = True
            self.online_event()

        ntmtools.dbg_msg("END - NetMan.set_online")
    ## - ##

    ## + ##
    def set_offline(self):
        ntmtools.dbg_msg("NetMan.set_offline")

        if self.online:
            self.online = False
            self.offline_event()

        ntmtools.dbg_msg("END - NetMan.set_offline")
    ## - ##

    ## + ##
    def nm_h_state_changed(self, new_state, old_state, reason):
        ntmtools.dbg_msg("NetMan.nm_h_state_changed")

        if self.mode == 0: 
            if new_state == NM_DEVICE_STATE_ACTIVATED:
                self.set_online()
            else:
                self.set_offline()

        ntmtools.dbg_msg("END - NetMan.nm_h_state_changed")
    ## - ##

    ## + ##
    # for ping mode
    def update_timer_handler(self):
        ntmtools.dbg_msg("NetMan.update_timer_handler")

        if (self.mode == 1):
            if (self.get_ping_test()):
                self.set_online()
            else:
                self.set_offline()

        gobject.timeout_add(self.update_timer_interval * 1000, self.update_timer_handler)

        ntmtools.dbg_msg("END - NetMan.update_timer_handler")
    ## - ##

    ## + ##
    def get_ping_test(self):
        ntmtools.dbg_msg("NetMan.get_ping_test")

        ret = subprocess.call("ping -q -w2 -c1 " + self.ping_test_url,
                        shell=True,
                        stdout=open('/dev/null', 'w'),
                        stderr=subprocess.STDOUT)

        retVal = None
        
        if ret == 0:
            retVal = True # Online
        else:
            retVal = False # Offline

        ntmtools.dbg_msg("END - NetMan.get_ping_test -> {0}".format(retVal))
        return retVal
    ## - ##

    ## + ##
    def ping_test(self):
        if self.mode != 1: return

        status = self.get_ping_test()        

        if status:
            self.set_online()
        else: 
            self.set_offline()
        
        gobject.timeout_add(2000, self.ping_test)
    ## - ##

    ## + ##
    def nm_h_device_added(self, device_path):
        ntmtools.dbg_msg("NetMan.nm_h_device_added : {0}".format(device_path))

        if (self.state == -1):
            dev_proxy = self.bus.get_object("org.freedesktop.NetworkManager", device_path)
            prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
            interface = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Interface")
            if (interface == self.interface):
                self.device_path = device_path
                self.state = prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
                self.bus.add_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)
                self.online = (self.state == NM_DEVICE_STATE_ACTIVATED)
                if self.online:
                    self.set_online()

        ntmtools.dbg_msg("END - NetMan.nm_h_device_added")
    ## - ##

    ## + ##
    def nm_h_device_removed(self, object_path):
        ntmtools.dbg_msg("NetMan.nm_h_device_removed : {0}".format(object_path))

        if (self.state != -1):
            if (self.device_path == object_path):
                self.state = -1
                self.bus.remove_signal_receiver(self.nm_h_state_changed, dbus_interface="org.freedesktop.NetworkManager.Device", signal_name="StateChanged", path = self.device_path)
                self.set_offline()

        ntmtools.dbg_msg("END - NetMan.nm_h_device_removed")
    ## - ##

    ## + disconnect the device  ##
    def disconnect_device(self):
        ntmtools.dbg_msg("NetMan.disconnect_device")

        if ( (self.mode == 0) and (self.device_path != "") ):
            try:
                proxy = self.bus.get_object('org.freedesktop.NetworkManager', self.device_path)
                ifaceNMDev = dbus.Interface(proxy, dbus_interface='org.freedesktop.NetworkManager.Device')
                ifaceNMDev.Disconnect()
            except:
                ntmtools.dbg_msg("NetMan.disconnect_device : Error")

        ntmtools.dbg_msg("END - NetMan.disconnect_device")
    ## - ##

    ## + ##
    def stop(self):
        ntmtools.dbg_msg("NetMan.stop")
        None
    ## - ##

    ## + ##
    ## list of Device
    def device_list(self):
        dev_list = []
        devices = self.get_devices()
        modems = self.get_modems()

        for device_path in devices:
            device = Device(self.bus, device_path, modems)
            dev_list.append(device)
        return dev_list
    ## - ##

    ## + ##
    ## list of dbus object /org/freedesktop/NetworkManager/Devices/*
    def get_devices(self):
        proxy = self.bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        nmi = dbus.Interface(proxy, dbus_interface='org.freedesktop.NetworkManager')
        devices = nmi.GetDevices()
        return devices
    ## - ##

    ## + ##
    ## list of dbus object /org/freedesktop/ModemManager/Modems/*
    def get_modems(self):
        proxy = self.bus.get_object('org.freedesktop.ModemManager', '/org/freedesktop/ModemManager')
        mmi = dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager')
        modems = mmi.EnumerateDevices()
        return modems
    ## - ##
    
### - ###

