#!/usr/bin/env python
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



__author__="Luigi Tullio"
#__date__ ="$Jul 9, 2009 5:52:10 PM$"

import locale
import gettext
import ntmtools

## + i18n ##
i18n_APP_NAME = "ntm"
i18n_DIR = "/usr/share/locale"
i18n_ok = False

err_code = 0
err_msg = ""

try:
    locale.setlocale(locale.LC_ALL, '')
except:
    err_code = 1
    err_msg = "locale.setlocale({0}, {1}) Error!".format(locale.LC_ALL, '')

try:
    locale.bindtextdomain(i18n_APP_NAME, i18n_DIR)
    gettext.bindtextdomain(i18n_APP_NAME, i18n_DIR)
    gettext.textdomain(i18n_APP_NAME)
    i18n_ok = True
except:
    err_code = 2
    err_msg = "locale.setlocale({0}, {1}) Error!".format(locale.LC_ALL, '')


if i18n_ok:
    try:
        i18n_lang = gettext.translation(i18n_APP_NAME, i18n_DIR)
    except:            
        err_code = 3
        err_msg = "Warning: error in gettext.translation({0}, {1}). Try with '../i18n/locale' directory.".format(i18n_APP_NAME, i18n_DIR)
        # i18n_DIR = os.getcwd() + "/../i18n/locale" # for no deb install
        i18n_DIR = "../i18n/locale" # for no deb install
        try:
            i18n_lang = gettext.translation(i18n_APP_NAME, i18n_DIR)
        except:
            err_code = 4
            err_msg = "gettext.translation({0}, {1}) : Error!".format(i18n_APP_NAME, i18n_DIR)
            i18n_ok = False

if i18n_ok:  
    _ = i18n_lang.gettext
    err_msg = _("i18n setup: done!")

import sys
import globaldef

# + options
from optparse import OptionParser

parser = OptionParser()
parser.add_option(
    "-v", "--version",
    action="store_true", dest="version", default=False,
    help= _("print the version number and exit")
)
parser.add_option(
    "-d", "--debug",
    action="store_true", dest="debug", default=False,
    help= _("show all debug messages")
)
(options, args) = parser.parse_args()

if (options.version):
    print(globaldef.VERSION)
    sys.exit(0)

if (options.debug):
    globaldef.DBGMSG_LEVEL = 10
# - options



from gtk import glade

gettext.install(i18n_APP_NAME, i18n_DIR)

for module in glade, gettext :
    module.bindtextdomain(i18n_APP_NAME, i18n_DIR)
    module.textdomain(i18n_APP_NAME)
## - i18n ##


print(_("NTM - Hello!"))

import os

##+ debug
ntmtools.dbg_msg('Environment settings:')
for env_name in [ 'LC_ALL', 'LC_CTYPE', 'LANG', 'LANGUAGE' ]:
    ntmtools.dbg_msg('\t%s = %s' % (env_name, os.environ.get(env_name, '')))
ntmtools.dbg_msg("ntm - locale.LC_ALL={0}".format(locale.LC_ALL))
ntmtools.dbg_msg("ntm - working dir = {0}".format(os.getcwd()))

ntmtools.dbg_msg("ntm - i18n : {0}".format(err_msg))
##- debug


import gobject
import sqlite3
import gtk
import string
import urllib2
import datetime
import time
import sys
import atexit

from event import Event
from mtraffic import MTraffic
from mtimeslot import MTimeSlot
from mtime import MTime
import ntmgui
import ntminfo
import netman
import pinger


############################################
#### Nettwork Traffic Monitor ####
class NTM():

    ## + ##
    def __init__(self):
        self.stop = False
        self.session_start = None
        self.last_traffic_in, self.last_traffic_out = None, None
        self.online = False
        self.timeout_changed = False
        self.versionChecked = False
        self.logTraffic = False
        self.discMsgDialog = False
        self.last_update = None

        self.pinger = pinger.Pinger("google.com", self.rtt_callback)
         
        ## db update
        self.db_update_interval = 20 # sec
        self.last_db_update = datetime.datetime.now()
        self.d_rb_db = self.d_tb_db = 0
        
        self.sys_info = ntmtools.getSysInfo()

        #print(self.sys_info)

        self.d_rb, self.d_tb = 0, 0

        self.home_path = os.getenv("HOME")
        self.profile_path = self.home_path + "/" + globaldef.NTM_PROFILE_RELPATH

        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)

        db_file_path = self.profile_path + "/" + globaldef.NTM_DB_NAME
        self.db_conn = sqlite3.connect(db_file_path, check_same_thread = False)

        self.update_event = Event()


        ## Create tables
        self.create_tables(self.db_conn)

        res = ntmtools.read_db_var(self.db_conn, "general.interface")
        if res != None:
            self.interface = res
        else:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.interface' " + _("or is not stored. Default value") + " 'ttyACM0'.")
            ntmtools.set_db_var(self.db_conn, "general.interface", "ttyACM0")
            self.interface = "ttyACM0"

        self.interfaceProcNetDev = self.interface

        res = ntmtools.read_db_var(self.db_conn, "general.update_interval")   # sec
        try:
            self.update_interval = int(float(res))
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.update_interval' " + _("or is not stored. Default value") + " '2'.")
            ntmtools.set_db_var(self.db_conn, "general.update_interval", "2")
            self.update_interval = 2

        res = ntmtools.read_db_var(self.db_conn, "general.last_version_check")   # datetime
        try:
            self.last_version_check = int(float(res))
            self.versionChecked = ((time.time() - self.last_version_check) < (5*24*60*60))
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.last_version_check' " + _("or is not stored. Default value") + " '" + _("now") + "'.")
            ntmtools.set_db_var(self.db_conn, "general.last_version_check", str(int(time.time())))
            self.last_version_check = int(time.time())
            self.versionChecked = False

        res = ntmtools.read_db_var(self.db_conn, "general.keep_above")   # 0 or 1
        try:
            self.ntmMainWindow_keep_above = ( int(float(res)) != 0)
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.keep_above' " + _("or is not stored. Default value") + " '0.")
            ntmtools.set_db_var(self.db_conn, "general.keep_above", "0")
            self.ntmMainWindow_keep_above = False

        res = ntmtools.read_db_var(self.db_conn, "general.opacity")   # 0 to 100
        try:
            self.ntmMainWindow_opacity = int(float(res))
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.opacity' " + _("or is not stored. Default value") + " '100.")
            ntmtools.set_db_var(self.db_conn, "general.opacity", "100")
            self.ntmMainWindow_opacity = 100

        res = ntmtools.read_db_var(self.db_conn, "general.autorun")   # 0 or 1
        try:
            self.general_pref_autorun = ( int(float(res)) != 0)
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.autorun' " + _("or is not stored. Default value") + " '" + _("True") + "'.")
            ntmtools.set_db_var(self.db_conn, "general.autorun", "1")
            self.general_pref_autorun = True
        self.set_autorun(self.general_pref_autorun)

        res = ntmtools.read_db_var(self.db_conn, "general.online_check")   # 0->NetworkManager; 1->Ping
        try:
            self.general_pref_online_check = int(float(res))
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.online_check' " + _("or is not stored. Default value") + " 0 (NetworkManager).")
            self.general_pref_online_check = 0
            ntmtools.set_db_var(self.db_conn, "general.online_check", "0")

        res = ntmtools.read_db_var(self.db_conn, "general.tray_activate_action")   # 0->Show Main Window; 1->Show Nptify;
        try:
            self.general_pref_tray_activate_action = int(float(res))
        except:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.tray_activate_action' " + _("or is not stored. Default value") + " 0 (Show Main Window).")
            self.general_pref_tray_activate_action = 0
            ntmtools.set_db_var(self.db_conn, "general.tray_activate_action", "0")

        res = ntmtools.read_db_var(self.db_conn, "general.trayicon_file")
        if res != None:
            ntmtools.dbg_msg("general.trayicon_file : " + res)
            self.trayicon_file = res
        else:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.trayicon_file' " + _("or is not stored. Default value") + " " + globaldef.DEFAULT_NTM_ICON_OFF)
            ntmtools.set_db_var(self.db_conn, "general.trayicon_file", globaldef.DEFAULT_NTM_ICON_OFF)
            self.trayicon_file = globaldef.DEFAULT_NTM_ICON_OFF

        res = ntmtools.read_db_var(self.db_conn, "general.trayicon_active_file")
        if res != None:
            ntmtools.dbg_msg("general.trayicon_active_file : " + res)
            self.trayicon_active_file = res
        else:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.trayicon_active_file' " + _("or is not stored. Default value") + " " + globaldef.DEFAULT_NTM_ICON_ON)
            ntmtools.set_db_var(self.db_conn, "general.trayicon_active_file", globaldef.DEFAULT_NTM_ICON_ON)
            self.trayicon_active_file = globaldef.DEFAULT_NTM_ICON_ON

        res = ntmtools.read_db_var(self.db_conn, "general.importexport_file")
        if res != None:
            self.importexport_file = res
        else:
            ntmtools.dbg_msg(_("Wrong value for the param") + " 'general.importexport_file' " + _("or is not stored. Default value") + " ''.")
            ntmtools.set_db_var(self.db_conn, "general.importexport_file", "")
            self.importexport_file = ""

        # NetMan
        self.net_man = netman.NetMan(self.general_pref_online_check, self.interface)
        self.net_man.add_online_handler(self.set_online)
        self.net_man.add_offline_handler(self.set_offline)

        # GUI
        self.ntmgui = ntmgui.NtmGui(self)

        self.ntmgui.apply_prop(self.ntmMainWindow_keep_above, self.ntmMainWindow_opacity)
        self.set_autorun(self.general_pref_autorun)

        self.ntmgui.set_general_preferences(
            self.interface, self.update_interval,
            self.ntmMainWindow_keep_above, self.ntmMainWindow_opacity,
            self.general_pref_autorun, self.general_pref_online_check,
            self.general_pref_tray_activate_action,
            self.importexport_file
        )
        self.update_event += self.ntmgui.update_h

        self.session_start = datetime.datetime.now()


        self.info_win_load = True
        if self.net_man.get_state():
            ntmtools.dbg_msg("State : Online")
            self.set_online()
        else: 
            ntmtools.dbg_msg("State : Offline")
            self.set_offline()



        # Traffic Module
        self.mtraffic = MTraffic.make_from_db(self)
        self.update_event += self.mtraffic.update_h
        self.ntmgui.set_traffic_module(self.mtraffic)

        # Time Slot Module
        self.mtimeslot = MTimeSlot.make_from_db(self)
        self.update_event += self.mtimeslot.update_h
        self.ntmgui.set_timeslot_module(self.mtimeslot)

        # Time Module
        self.mtime = MTime.make_from_db(self)
        self.update_event += self.mtime.update_h
        self.ntmgui.set_time_module(self.mtime)


        

        # Info/News
        self.info_win = ntminfo.NtmInfo(self.net_man.get_state())
        self.info_win_load = False

        gobject.timeout_add(self.update_interval*1000, self.update_count)
        self.update_count(True)
        
        self.pinger.start()
    ## end-def ##

    ## + ##
    def rtt_callback(self, caller, rtt):
        self.ntmgui.update_exinfo(rtt)
    ## - ##

    ## + ##
    def quit(self):
        ntmtools.dbg_msg("NTM.quit")

        self.pinger.stop()
        self.update_count(True)
        self.stop = True
        self.net_man.stop()
        sys.exit()

        ntmtools.dbg_msg("END - NTM.quit")
    ## end-def ##


    ## + ##
    # fist_day, fast_day: date
    # all_days: boolean
    def get_report_from_db(self, first_day, last_day, all_days=False):
        ntmtools.dbg_msg("NTM.get_report_from_db")

        ctra = self.db_conn.cursor()

        if all_days:
            ctra.execute("select * from dailytraffic")
        else:
            last_day_t = last_day + datetime.timedelta(1)
            ctra.execute("select * from dailytraffic where (date>=?) AND (date<?)", (first_day, last_day_t))

        t_count = 0
        t_in = 0
        t_out = 0
        tot_min = tot_max = 0
        tra_list = []
        for r in ctra:
            t_in += r[1]
            t_out += r[2]
            tot = r[1] + r[2]
            if (t_count == 0):
                tot_min = tot
                tot_max = tot
            else:
                if tot > tot_max: tot_max = tot
                elif tot < tot_min: tot_min = tot
            t_count += 1
            tra_list += [r]

        cses = self.db_conn.cursor()

        if all_days:
            cses.execute("select * from session")
        else:
            cses.execute("select * from session where (start>=?) AND (start<?)", (first_day, last_day_t))

        s_count = 0
        tot_time = 0
        s_max = s_min = 0
        ses_list = []
        for r in cses:
            tsStart = datetime.datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
            tsEnd = datetime.datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")
            diff = ntmtools.timedelta2sec(tsEnd - tsStart)
            tot_time += diff
            if (s_count == 0):
                s_min = diff
                s_max = diff
            else:
                if diff > s_max: s_max = diff
                elif diff < s_min: s_min = diff
            s_count += 1
            ses_list += [r]

        ntmtools.dbg_msg("END - NTM.get_report_from_db")

        return (tra_list, ses_list, t_count, t_in, t_out, tot_max, tot_min, s_count, tot_time, s_max, s_min)
    ## end-def ##


    ## + ##
    def update_db_daily_traffic(self, datetime, recbytes, trabytes):
        ntmtools.dbg_msg("NTM.update_db_daily_traffic")

        date = datetime.date()

        c = self.db_conn.cursor()
        c.execute("select * from dailytraffic where date=?", (date,) )
        r = c.fetchone()

        if r != None:
            self.db_conn.execute("update dailytraffic set recbytes=?, trabytes=? where date=?", (r[1] + recbytes, r[2] + trabytes, r[0]))
        else:
            self.db_conn.execute("insert into dailytraffic values (?, ?, ?)", (date, recbytes, trabytes))
        self.db_conn.commit()

        ntmtools.dbg_msg("END - NTM.update_db_daily_traffic")
    ## end-def ##


    ## + ##
    def update_db_session(self, commit = True):
        ntmtools.dbg_msg("NTM.update_db_session")

        dtStart = self.session_start.replace(microsecond=0).isoformat(' ')
        dtEnd = self.last_update.replace(microsecond=0).isoformat(' ')

        c = self.db_conn.cursor()
        c.execute("select * from session where start=?", (dtStart,) )
        r = c.fetchone()

        if r != None:
            self.db_conn.execute("update session set end=? where start=?", (dtEnd, dtStart))
        else:
            self.db_conn.execute("insert into session values (?, ?)", (dtStart, dtEnd))

        if commit: self.db_conn.commit()

        ntmtools.dbg_msg("END - NTM.update_db_session")
    ## - ##


    ## + ##
    def remove_all_data(self):
        ntmtools.dbg_msg("NTM.remove_all_data")

        self.db_conn.execute("delete from dailytraffic")
        self.db_conn.execute("delete from session")
        self.db_conn.commit()

        self.mtraffic.reload_traffic()
        self.mtimeslot.reload_sessions()
        self.mtime.reload_time_used()
        self.ntmgui.update_report()

        ntmtools.dbg_msg("END - NTM.remove_all_data")
    ## end-def ##


    ## + ##
    def substitute_data(self, db_conn):
        ntmtools.dbg_msg("NTM.substitute_data")

        self.copy_data(db_conn, self.db_conn)
        self.mtraffic.reload_traffic()
        self.mtimeslot.reload_sessions()
        self.mtime.reload_time_used()
        self.ntmgui.update_report()

        ntmtools.dbg_msg("END - NTM.substitute_data")
    ## end-def ##


    ## + ##
    def copy_data(self, dbc_src, dbc_des):
        ntmtools.dbg_msg("NTM.copy_data")

        dbc_d = dbc_des
        dbc_s = dbc_src

        cs = dbc_s.cursor()
        cd = dbc_d.cursor()

        dbc_d.execute("delete from dailytraffic")
        rows_s = cs.execute("select * from dailytraffic")
        for rs in rows_s:
            cd.execute("insert into dailytraffic values (?, ?, ?)", rs)

        dbc_d.execute("delete from session")
        cs = dbc_s.cursor()
        rows_s = cs.execute("select * from session")
        for rs in rows_s:
            cd.execute("insert into session values (?, ?)", rs)
        dbc_d.commit()

        ntmtools.dbg_msg("END - NTM.copy_data")
    ## end-def ##


    ## + ##
    def create_tables(self, dbconn):
        ntmtools.dbg_msg("NTM.create_tables")

        # Create tables
        try:
            dbconn.execute('create table dailytraffic (date text, recbytes integer, trabytes integer)')
            dbconn.commit()
            ntmtools.dbg_msg("Create dailytraffic table.", 5)
        except:
            ntmtools.dbg_msg("Warning! Create dailytraffic table aborted.", 5)
            pass

        try:
            dbconn.execute("create table vars (name text, value text)")
            dbconn.commit()
            ntmtools.dbg_msg("Create vars table.", 5)
        except:
            ntmtools.dbg_msg("Warning! Create vars table aborted.", 5)
            pass

        try:
            dbconn.execute("create table session (start datetime, end datetime)")
            dbconn.commit()
            ntmtools.dbg_msg("Create session table.", 5)
        except:
            ntmtools.dbg_msg("Warning! Create session table aborted.", 5)
            pass

        ntmtools.dbg_msg("END - NTM.create_tables")
    ## end-def ##


    ## + ##
    def set_preferences( self, interface, updateInterval, keep_above, opacity, autorun,
                        online_check, tray_activate_action, importexport_file, iconfile, iconfile_active):
        ntmtools.dbg_msg("NTM.set_preferences")

        ris = self.get_proc_net_dev(interface)
        if (ris == None) and self.online:
            dia = gtk.Dialog(_('NTM - Interface'),
                              self.ntmgui.statusIconMenu.get_toplevel(),  #the toplevel wgt of your app
                              gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  #binary flags or'ed together
                              (_("Change the interface"), 77, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
            dia.vbox.pack_start(gtk.Label(_('The interface "{0}" is not detected or inactive.\nDo you want to confirm the change?').format(interface)))
            dia.show_all()
            result = dia.run()
            doChangeInterface = (result == 77)
            dia.destroy()
        else:
            doChangeInterface = True

        if doChangeInterface:
            interface_changed = (self.interface != interface)
            if interface_changed & self.online:
                self.set_offline()
                self.interface = interface
                self.interfaceProcNetDev = interface
                self.set_online()
            else:
                self.interface = interface
                self.interfaceProcNetDev = interface
            ntmtools.set_db_var(self.db_conn, "general.interface", interface)
            if interface_changed:
                self.net_man.set_interface(self.interface)

        self.ntmMainWindow_keep_above = keep_above
        if self.ntmMainWindow_keep_above:
            ntmtools.set_db_var(self.db_conn, "general.keep_above", "1")
        else:
            ntmtools.set_db_var(self.db_conn, "general.keep_above", "0")

        self.ntmMainWindow_opacity = opacity
        ntmtools.set_db_var(self.db_conn, "general.opacity", opacity)

        self.timeout_changed = (self.update_interval != updateInterval)
        self.update_interval = int(updateInterval)
        ntmtools.set_db_var(self.db_conn, "general.update_interval", str(int(updateInterval)))

        self.general_pref_autorun = autorun
        if autorun: ntmtools.set_db_var(self.db_conn, "general.autorun", "1")
        else: ntmtools.set_db_var(self.db_conn, "general.autorun", "0")
        self.set_autorun(autorun)

        if self.general_pref_online_check != online_check:
            if online_check==0:
                self.general_pref_online_check = 0
                self.net_man.set_mode(online_check)
                ntmtools.set_db_var(self.db_conn, "general.online_check", "0")
            elif online_check==1:
                self.general_pref_online_check = 1
                self.net_man.set_mode(online_check)
                ntmtools.set_db_var(self.db_conn, "general.online_check", "1")
            else:
                ntmtools.dbg_msg("Error: Invald online_check value.\n")

        if self.general_pref_tray_activate_action != tray_activate_action:
            if tray_activate_action==0:
                self.general_pref_tray_activate_action = 0
                ntmtools.set_db_var(self.db_conn, "general.tray_activate_action", "0")
            elif tray_activate_action==1:
                self.general_pref_tray_activate_action = 1
                ntmtools.set_db_var(self.db_conn, "general.tray_activate_action", "1")
            else:
                ntmtools.dbg_msg("Error: Invald tray_activate_action value.\n")

        if self.importexport_file != importexport_file:            
            self.importexport_file = importexport_file
            ntmtools.set_db_var(self.db_conn, "general.importexport_file", importexport_file)

        if self.trayicon_file != iconfile:
            self.trayicon_file = iconfile
            ntmtools.set_db_var(self.db_conn, "general.trayicon_file", iconfile)
            self.ntmgui.set_trayicon_file(iconfile)
            
        if self.trayicon_active_file != iconfile_active:
            self.trayicon_active_file = iconfile_active
            ntmtools.set_db_var(self.db_conn, "general.trayicon_active_file", iconfile_active)
            self.ntmgui.set_trayicon_active_file(iconfile_active)
            
        ntmtools.dbg_msg("END - NTM.set_preferences")
    ## - ##


    ## + ##
    def get_autorun(self):
        des = self.sys_info["des"]
        autorun = False
        if des in GNOME_AUTORUN_TYPE_DES:
            autorun = os.path.exists(os.getenv("HOME") + "/.config/autostart/ntm.desktop")
        elif des in KDE_AUTORUN_TYPE_DES:
            autorun = os.path.exists(os.getenv("HOME") + "/.kde/Autostart/ntm.sh")
        return autorun
    ## - ##


    ## + ##
    def set_autorun(self, active):
        ntmtools.dbg_msg("NTM.set_autorun")

        try:
            des = self.sys_info["des"]
            if (active):
                if des in GNOME_AUTORUN_TYPE_DES:
                    ar_dir = os.getenv("HOME") + "/.config/autostart"
                    ar_file = ar_dir + "/ntm.desktop"
                    autorun = os.path.exists(ar_file)
                    if not autorun:
                        if not os.path.exists(ar_dir):
                            os.makedirs(ar_dir)
                        src = globaldef.NTM_PATH + "/stf/ntm.desktop"
                        # shutil.copyfile(src, ar_file)
                        os.system("cp {0} {1}".format(src, ar_file))
                elif (des == "kde"):
                    ar_dir = os.getenv("HOME") + "/.kde/Autostart"
                    ar_file = ar_dir + "/ntm.sh"
                    autorun = os.path.exists(ar_file)
                    if not autorun:
                        if not os.path.exists(ar_dir):
                            os.makedirs(ar_dir)
                        src = globaldef.NTM_PATH + "/stf/ntm.sh"
                        # shutil.copyfile(src, ar_file)
                        os.system("cp {0} {1}".format(src, ar_file))
                else:
                    ntmtools.dbg_msg(_("Autostart work only with Gnome, KDE and Xfce."))
            else:
                if des in GNOME_AUTORUN_TYPE_DES:
                    os.remove(os.getenv("HOME") + "/.config/autostart/ntm.desktop")
                elif des in KDE_AUTORUN_TYPE_DES:
                    os.remove(os.getenv("HOME") + "/.kde/Autostart/ntm.sh")
                else: pass
        except: pass

        ntmtools.dbg_msg("END - NTM.set_autorun")
    ## - ##

    ## + ##
    # timestamp : Time of update [datetime.datetime]; session_start:[datetime.datetime]; update_interval : sec
    # last_rec_traffic, last_tra_traffic : Generated traffic from last update in bytes
    # conn_state : 0 -> offline; 1 -> online
    def update_event_th(self, timestamp, session_start, update_interval, last_rec_traffic, last_tra_traffic, conn_state):    
        ntmtools.dbg_msg("NTM.update_event_th")

        self.update_event(timestamp, session_start, update_interval, last_rec_traffic, last_tra_traffic, conn_state)

        #def run_update_event():
        #    self.update_event(timestamp, session_start, update_interval, last_rec_traffic, last_tra_traffic, conn_state)            

        #update_event_thread = threading.Thread(target=run_update_event)

        ntmtools.dbg_msg("END - NTM.update_event_th")
    ## - ##

    ## + ##
    def set_online(self):
        ntmtools.dbg_msg("NTM.set_online")

        self.session_start = datetime.datetime.now()

        self.update_event_th(self.session_start, self.session_start, self.update_interval, 0, 0, 1)

        ris = self.get_proc_net_dev_default()
        if ris != None:
            self.last_traffic_in, self.last_traffic_out = ris
        else:
            ntmtools.dbg_msg(_("The interface") + " " + self.interface + " " +_("is not detected or inactive."))
            self.last_traffic_in, self.last_traffic_out = 0, 0

        self.online = True

        if self.logTraffic:
            print(_('Total\tReceive\tTransm.\tMean Speed of the last {0}"').format(self.update_interval))
            print('KByte\tKByte\tKByte\tKByte/sec')
        
        if not self.versionChecked:
            if not self.check_version("http://luigit.altervista.org/ntm/ntm_update.php", globaldef.VERSION):
                self.versionChecked = True
                ntmtools.set_db_var(self.db_conn, "general.last_version_check", str(int(time.time())))

        if not self.info_win_load:
            self.info_win.load()
            self.info_win_load = True

        ntmtools.dbg_msg("END - NTM.set_online")
    ## end-def ##

    ## + ##
    def set_offline(self):
        ntmtools.dbg_msg("NTM.set_offline")

        self.online = False
        self.update_count(True)
        self.update_event_th(datetime.datetime.now(), self.session_start, self.update_interval, self.d_rb, self.d_tb, 0)

        ntmtools.dbg_msg("END - NTM.set_offline")
    ## end-def ##


    ## + ##
    def update_count(self, force_update_db=False):
        ntmtools.dbg_msg("NTM.update_count")

        if self.stop:
            ntmtools.dbg_msg("END - NTM.update_count -> false")
            return False

        if not self.online:
            ntmtools.dbg_msg("END - NTM.update_count -> true")
            return True

        self.last_update = datetime.datetime.now()

        ris = self.get_proc_net_dev_default()
        if ris != None:
            rb, tb = ris
            self.d_rb = rb - self.last_traffic_in
            self.d_tb = tb - self.last_traffic_out

            ## Update DB
            self.request_update_db(force_update_db)
            ##

            self.last_traffic_in = rb
            self.last_traffic_out = tb
            state = 0
            if self.online:
                state = 1
            self.update_event_th(self.last_update, self.session_start, self.update_interval, self.d_rb, self.d_tb, state)

        if self.timeout_changed:
            gobject.timeout_add(self.update_interval*1000, self.update_count)
            self.timeout_changed = False
            ntmtools.dbg_msg("END - NTM.update_count -> false")
            return False

        ntmtools.dbg_msg("END - NTM.update_count -> true")
        return True
    ## end-def ##


    ## + ##
    def request_update_db(self, force_update=False):
        #print("request_update_db(force_update={0})".format(force_update))
        self.d_rb_db += self.d_rb
        self.d_tb_db += self.d_tb
        datetime_now = datetime.datetime.now()
        diff_last_update_db = ntmtools.timedelta2sec(datetime_now - self.last_db_update)
        if force_update or (diff_last_update_db >= self.db_update_interval):
            self.last_db_update = datetime_now
            diff = self.d_rb_db + self.d_tb_db
            if diff != 0:
                self.update_db_daily_traffic(self.session_start, self.d_rb_db, self.d_tb_db)
                self.d_rb_db = self.d_tb_db = 0
            self.update_db_session(True)
    ## end-def ##
    

    ### + return False for not error ###
    def check_version(self, url, version):
        ntmtools.dbg_msg("NTM.check_version : {0} , {1}".format(url, version))

        itime = ntmtools.read_db_var(self.db_conn, "itime")
        try:
            ntmtools.str_to_date_time(itime)
        except:
            ntmtools.dbg_msg("itime: wrong format or absent. Rigenerate.")
            itime = str(datetime.datetime.today())
            ntmtools.set_db_var(self.db_conn, "itime", itime)

        envInfo = urllib2.quote("{0}\t{1}".format(itime, ntmtools.get_env_info()))

        fullurl = url + "?cver={0}&sys={1}".format(urllib2.quote(version), envInfo)

        dfile = None
        try:
            dfile = urllib2.urlopen(fullurl, timeout=10)
        except:
            ntmtools.dbg_msg(_("Connection Error") + " (" + fullurl + ").")
            ntmtools.dbg_msg("END - NTM.check_version -> True")
            return True

        if dfile != None:
            str_data = dfile.read()
            dic_data = ntmtools.prop2dic(str_data)
            newVer = dic_data["lastversion"]
            compare = ntmtools.version_compare(version, newVer)

            if compare < 0:
                dialog = gtk.Dialog(
                    _("NTM - New Version"), self.ntmgui.statusIconMenu.get_toplevel(),
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_OK, gtk.RESPONSE_OK)
                )
                icon = dialog.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
                dialog.set_icon(icon)

                linkButton = gtk.LinkButton(
                    dic_data["suggestedurl"],
                    _("Your version") + ": {0}.  ".format(version) + _("Last version") + ": {0}\n{1}\n{2}".
                        format(newVer, dic_data["updatemessage"], dic_data["extramessage"] )
                )
                dialog.vbox.pack_start(linkButton)

                dialog.show_all()
                dialog.run()
                dialog.destroy()
        else:
            ntmtools.dbg_msg("END - NTM.check_version -> True")
            return True

        ntmtools.dbg_msg("END - NTM.check_version -> False")
        return False
    ### - ###


    ## + ##
    def deactive_connection(self):
        ntmtools.dbg_msg("NTM.deactive_connection")

        self.net_man.disconnect_device()

        ntmtools.dbg_msg("END - NTM.deactive_connection")
    ## - ##


    ## + ##
    def get_proc_net_dev_default(self):
        ntmtools.dbg_msg("NTM.get_proc_net_dev_default")

        if self.interfaceProcNetDev == None:
            self.interfaceProcNetDev = self.interface

        ret = self.get_proc_net_dev_traffic(self.interfaceProcNetDev)

        if (ret == None):
            self.interfaceProcNetDev = self.get_proc_net_dev_name(self.interface)
            if self.interfaceProcNetDev != None:
                ret = self.get_proc_net_dev_traffic(self.interfaceProcNetDev)

        ntmtools.dbg_msg("END - NTM.get_proc_net_dev_default -> {0}".format(ret))
        return ret
    ## - ##

    ## + ##
    def get_proc_net_dev(self, interface):
        ntmtools.dbg_msg("NTM.get_proc_net_dev : {0}".format(interface))
        ret = self.get_proc_net_dev_traffic(interface)
        if (ret == None):
            interfaceProcNetDev = self.get_proc_net_dev_name(interface)
            if interfaceProcNetDev != None:
                ret = self.get_proc_net_dev_traffic(interfaceProcNetDev)

        ntmtools.dbg_msg("END - NTM.get_proc_net_dev -> {0}".format(ret))
        return ret
    ## - ##

    ## + ##
    def get_proc_net_dev_name(self, interface):
        ntmtools.dbg_msg("NTM.get_proc_net_dev_name : {0}".format(interface))
        ret_iface = None
        for line in open('/var/log/messages','r'):
            if 'pppd' not in line: continue
            if 'Connect: ' not in line: continue
            if interface in line:
                pair = line.split("Connect: ")[1].split(" <--> ")
                if pair[1][5:]:
                    ret_iface = pair[0]
        
        ntmtools.dbg_msg("END - NTM.get_proc_net_dev_name -> {0}".format(ret_iface))
        return ret_iface
    ## - ##


    ## + ##
    def get_proc_net_dev_traffic(self, interface):
        ntmtools.dbg_msg("NTM.get_proc_net_dev_traffic : {0}".format(interface))
        retVal = None
        for line in open('/proc/net/dev','r'):
            # print("line : {0}".format(line))
            if ':' not in line: continue
            splitline = string.split(line, ':', 1)
            if string.strip(splitline[0]) != interface: continue

            x = splitline[1].split()
            rec_bytes = int(x[0])
            tra_bytes = int(x[8])
            retVal = (rec_bytes, tra_bytes)
            break

        ntmtools.dbg_msg("END - NTM.get_proc_net_dev_traffic -> {0}".format(retVal))
        return retVal
    ## - ##

    ## + ##
    ## list of Device
    def device_list(self):
        return self.net_man.device_list()
    ## - ##    
#### end-class ####


@atexit.register
def goodbye():
    print " " + _("See you later! :)") + " "

############################################
#### MAIN
############################################
if __name__ == "__main__":

    ## + i18n ##
    i18n_APP_NAME = "ntm"
    i18n_DIR = "/usr/share/locale"
    i18n_ok = False

    err_code = 0
    err_msg = ""

    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        err_code = 1
        err_msg = "locale.setlocale({0}, {1}) Error!".format(locale.LC_ALL, '')

    try:
        locale.bindtextdomain(i18n_APP_NAME, i18n_DIR)
        gettext.bindtextdomain(i18n_APP_NAME, i18n_DIR)
        gettext.textdomain(i18n_APP_NAME)
        i18n_ok = True
    except:
        err_code = 2
        err_msg = "locale.setlocale({0}, {1}) Error!".format(locale.LC_ALL, '')

    if i18n_ok:
        try:
            i18n_lang = gettext.translation(i18n_APP_NAME, i18n_DIR)
        except:            
            err_code = 3
            err_msg = "Warning: error in gettext.translation({0}, {1}). Try with '../i18n/locale' directory.".format(i18n_APP_NAME, i18n_DIR)
            # i18n_DIR = os.getcwd() + "/../i18n/locale" # for no deb install
            i18n_DIR = "../i18n/locale" # for no deb install
            try:
                i18n_lang = gettext.translation(i18n_APP_NAME, i18n_DIR)
            except:
                err_code = 4
                err_msg = "gettext.translation({0}, {1}) : Error!".format(i18n_APP_NAME, i18n_DIR)
                i18n_ok = False

    if i18n_ok:  
        _ = i18n_lang.gettext
        err_msg = _("i18n setup: done!")

    gettext.install(i18n_APP_NAME, i18n_DIR)

    for module in glade, gettext :
        module.bindtextdomain(i18n_APP_NAME, i18n_DIR)
        module.textdomain(i18n_APP_NAME)
    ## - i18n ##


    # + options
    parser = OptionParser()
    parser.add_option(
        "-v", "--version",
        action="store_true", dest="version", default=False,
        help= _("print the version number and exit")
    )
    parser.add_option(
        "-d", "--debug",
        action="store_true", dest="debug", default=False,
        help= _("show all debug messages")
    )
    (options, args) = parser.parse_args()

    if (options.version):
        print(globaldef.VERSION)
        sys.exit(0)

    if (options.debug):
        globaldef.DBGMSG_LEVEL = 10
    # - options

    print(_("NTM - Hello!"))

    ntmtools.dbg_msg('Environment settings:')
    for env_name in [ 'LC_ALL', 'LC_CTYPE', 'LANG', 'LANGUAGE' ]:
        ntmtools.dbg_msg('\t%s = %s' % (env_name, os.environ.get(env_name, '')))
    ntmtools.dbg_msg("ntm - locale.LC_ALL={0}".format(locale.LC_ALL))
    ntmtools.dbg_msg("ntm - working dir = {0}".format(os.getcwd()))

    ntmtools.dbg_msg("ntm - i18n : {0}".format(err_msg))

    # for webkit
    gobject.threads_init()

    # Network Traffic Monitor
    ntm = NTM()

    try:
        gobject.MainLoop().run()
    except KeyboardInterrupt:
        ntmtools.dbg_msg("Ops! Keyboard interrupt.")
        gobject.MainLoop().quit()


