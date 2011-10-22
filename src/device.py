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


import dbus
import ntmtools
import sqlite3

## + Device ##
class Device:

    ## + __init__ ##
    def __init__(self):
        self.device_path = ""
        self.udi = ""
        self.interface = ""
        self.ip_interface = ""
        self.driver = ""
        self.capabilities = 0
        self.ip4Address = 0
        self.state = 0
        self.ip4Config = ""
        self.dhcp4Config = ""
        self.ip6Config = ""
        self.managed = 0
        self.deviceType = 0
        self.modem = False
    ## - __init__ ##


    ## + __init__ ##
    def __init__(self, bus, device_path, modems_list):
        self.device_path = device_path
        dev_proxy = bus.get_object("org.freedesktop.NetworkManager", device_path)
        prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
        
        self.udi = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Udi")
        self.interface = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Interface")
        self.ip_interface = prop_iface.Get("org.freedesktop.NetworkManager.Device", "IpInterface")
        self.driver = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Driver")
        self.capabilities = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Capabilities")
        self.ip4Address = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Ip4Address")
        self.state = prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
        self.ip4Config = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Ip4Config")
        self.dhcp4Config = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Dhcp4Config")
        self.ip6Config = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Ip6Config")
        self.managed = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Managed")
        self.deviceType = prop_iface.Get("org.freedesktop.NetworkManager.Device", "DeviceType")
        self.modem = False
        
        ntmtools.dbg_msg("@@@ self.deviceType: {0}".format(self.deviceType))
        
        # +++ Stub ++++
        """
        self.modem = True
        self.modem_equipment_identifier = "353274372364527364"
        self.modem_enabled = 1
        self.modem_op_id = '22299'
        self.modem_imei = "imei765465365"
        self.modem_imsi = "Imsi64536543453"
        self.modem_mcc = 222
        self.modem_mcc_iso_3166_1 = "IT"
        self.modem_mcc_name = "Italy"
        self.modem_mnc = 99
        self.modem_mnc_net_name = "3 Italia"
        """
        #--- Stub ---
        
        """
        try:
            for modem_path in modems_list:
                modem_obj = bus.get_object("org.freedesktop.ModemManager", modem_path)
                prop_iface = dbus.Interface(modem_obj, "org.freedesktop.DBus.Properties")
                modem_dbus_i = dbus.Interface(modem_obj, "org.freedesktop.ModemManager.Modem")
                modem_iface = prop_iface.Get("org.freedesktop.ModemManager.Modem", "Device")
                ntmtools.dbg_msg("@@@@ {0} - {1}".format(modem_iface, self.interface))
                if modem_iface == self.interface:
                    ntmtools.dbg_msg("@@@ MODEM ")
                    self.modem = True
                    self.modem_equipment_identifier = prop_iface.Get("org.freedesktop.ModemManager.Modem", "EquipmentIdentifier")
                    self.modem_enabled = prop_iface.Get("org.freedesktop.ModemManager.Modem", "Enabled")
    
                    ntmtools.dbg_msg("@@@ modem_equipment_identifier:{0}".format(self.modem_equipment_identifier))
                    ntmtools.dbg_msg("@@@ modem_enabled:{0}".format(self.modem_enabled))
        
                    if self.modem_enabled:
                        self.mode_info = modem_dbus_i.GetInfo()
                        prop_iface_gsm_card = dbus.Interface(modem_obj, "org.freedesktop.ModemManager.Modem.Gsm.Card")
                        self.modem_op_id = prop_iface_gsm_card.GetOperatorId()  # '22299'
                        self.modem_imei = prop_iface_gsm_card.GetImei()
                        self.modem_imsi = prop_iface_gsm_card.GetImsi()
                        
                        (mcc, mnc) = self.decode_op_id(self.modem_op_id)
                        self.modem_mcc = mcc[0] # 222
                        self.modem_mcc_iso_3166_1 = mcc[1]  # IT
                        self.modem_mcc_name = mcc[2]    # Italy
    
                        self.modem_mnc = mnc[1] # 99
                        self.modem_mnc_net_name = mnc[5]    # 3 Italia
                        if self.modem_mnc_net_name == "":
                            self.modem_mnc_net_name = mnc[4]    # Hutchison 3G
                            if self.modem_mnc_net_name == "":
                                self.modem_mnc_net_name = mnc[6]    # Hi3G
                                if self.modem_mnc_net_name == "":
                                    self.modem_mnc_net_name = "mnc=" + self.modem_mnc
        except:
            ntmtools.dbg_msg("@@@ except ")
            self.modem = False
        """
    ## - __init__ ##

    ## + ##
    def decode_op_id(self, op_id):
        mcc = int(op_id[0:2])
        mnc = int(op_id[2:3])
        db_mnc_conn = sqlite3.connect("./mnc.sqlite", check_same_thread = False)
        c = db_mnc_conn.cursor()
        c.execute("select * from mcc where mcc=?", (mcc,))
        r1 = c.fetchone()

        c.execute("select * from mnc where mcc=? AND mnc=?", (mcc, mnc,))
        r2 = c.fetchone()

        return (r1, r2)
    ## end-def ##


## - Device ##

