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


import globaldef

import math
import time
import datetime
import platform
import os
import string
from monthdelta import monthdelta
import commands
import sys


## get the bytes value then return a string with a compact representation (ex.
##  '123 bytes', '12.34 KB', '1254.1 MB')
def format_bytes(val):
    tv = 1024.0
    if (val < tv): return "{0} bytes".format(int(val))
    tv *= 1024.0
    if (val < tv): return "{0:.3} KiB".format(1024.0 * val / tv)
    tv *= 1024.0
    if (val < tv): return "{0:.3} MiB".format(1024.0 * val / tv)
    tv *= 1024.0
    return "{0:.3} GiB".format(1024.0 * val / tv)
## end-def ##


## get the seconds then return a string with a compact representation (ex.
##  ' 13" ', ' 2'34" ', ' 3h2'1" ')
def format_time(tot_sec):
    ival = int(round(tot_sec))
    if ival < 0:
        ival = -ival
        sign = "-"
    else:
        sign = ""
    (h, m, s) = sec_to_hms(ival)
    if h>0: return "{0}{1}h{2}\'{3}\"".format(sign, h, m, s)
    elif m>0: return "{0}{1}'{2}\"".format(sign, m, s)
    else: return "{0}{1}\"".format(sign, s)
## end-def ##


## get the timedelta then return a string with a compact representation (ex.
##  ' 13" ', ' 2'34" ', ' 3h2'1" ')
def format_time_td(timedelta_val):
    return format_time(timedelta2sec(timedelta_val))
## end-def ##


## get the seconds then return (hour, minute, sec)
def sec_to_hms(tot_sec):
    ival = int(round(tot_sec))
    s = ival % 60
    ival = math.trunc(ival / 60)
    m = ival % 60
    ival = math.trunc(ival / 60)
    h = ival
    return (h, m, s)
## end-def ##


## + ##
def timedelta2sec(val):
    return val.days * (24*60*60) + val.seconds + int(round(0.000001*val.microseconds))
## end-def ##


## + ##
def read_db_var(conn, name):
    c = conn.cursor()
    c.execute("select * from vars where name=?", (name,))
    r = c.fetchone()
    if r != None: return r[1]
    else: return None
## end-def ##


## + ##
def set_db_var(conn, name, val, commit=True):
    if read_db_var(conn, name) == None:
        conn.execute("insert into vars values (?, ?)", (name, val) )
    else:
        conn.execute("update vars set value=? where name=?", (val, name) )
    if commit: conn.commit()
## end-def ##

## + ##
# str ex. "2010-06-19"
def str_to_date(str):
    ris = time.strptime(str, "%Y-%m-%d")
    return datetime.date(ris.tm_year, ris.tm_mon, ris.tm_mday)
## - ##


## + ##
# str ex. "2010-06-19 16:42:02.123456"
def str_to_date_time(str):
    return datetime.datetime.strptime(str, "%Y-%m-%d %H:%M:%S.%f")
## - ##


## + ##
def str_to_int(str, defVal):
    if str == None: return defVal
    else: return int(str)
## end-def ##


## + ##
def get_env_info():
    ctime = str(datetime.datetime.today())
    pyVer = platform.python_version()
    plat = platform.platform()
    osi = os.uname()
    arc = platform.architecture()
    return "{0}\t{1}\t{2}\t{3}\t{4}".format(ctime, pyVer, plat, osi[3], arc[0], arc[1])
## - ##


### return = 0:ugual; 1:ver1>ver2; -1:ver1<ver2 ###
# ex: 1.2.1 > 1.2 > 1.2.b > 1.2.a
def version_compare(ver1, ver2):
    sv1 = string.split(ver1, '.')
    sv2 = string.split(ver2, '.')

    if len(sv2) > len(sv1):
        min = len(sv1)
    else:
        min = len(sv2)

    i = 0
    while i < min:
        try:
            val1 = int(sv1[i])
            int1 = True
        except:
            int1 = False
            
        try:
            val2 = int(sv2[i])
            int2 = True
        except:
            int2 = False

        if (int1 and int2):
            if val1 > val2: return 1
            if val1 < val2: return -1
        elif (int1 and not int2):
            return 1;
        elif (not int1 and int2):
            return -1;
        elif (sv1[i] > sv2[i]):
            return 1;
        elif (sv1[i] < sv2[i]):
            return -1;
        i += 1

    if len(sv1) > len(sv2): 
        try:
            val1 = int(sv1[i])
            return 1
        except:
            return -1
    elif len(sv1) < len(sv2):   
        try:
            val2 = int(sv2[i])
            return -1
        except:
            return 1
    else: return 0
### - ###


### + ###
def prop2dic(properties_string):
    linelist = string.split(properties_string, '\n')
    dic = {}

    for l in linelist:
        sl = string.split(l, ':', 1)
        if len(sl) == 2:
            if sl[0] != '':
                dic[string.strip(sl[0])] = string.strip(sl[1])
    return dic
### - ###


### + ###
def dbg_msg(str, lev=10):
    if (lev >= globaldef.DBGMSG_LEVEL):
        sys.stderr.write("[ntm] {0}\n".format(str))
### - ###


### + ###
def get_desktop_environment():
    desktop_environment = 'generic'
    if os.environ.get('KDE_FULL_SESSION') == 'true':
        desktop_environment = 'kde'
    elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
        desktop_environment = 'gnome'
    else:
        try:
            info = commands.getoutput('xprop -root _DT_SAVE_MODE')
            if ' = "xfce4"' in info:
                desktop_environment = 'xfce'
        except (OSError, RuntimeError):
            pass
    return desktop_environment
### - ###


### + ###
def bool_to_str_int(val):
    if val: return '1'
    else: return '0'
### - ###


### + ###
# first_day: datetime.date
# period: 0->Custom Days; 1->Day; 2->Week; 3->Month; 4->Year;
def get_last_day(first_day, period, custom_days):
    if period == 0:
        return (first_day + datetime.timedelta(custom_days-1))
    elif period == 1:
        return first_day
    elif period == 2:
        return (first_day + datetime.timedelta(7-1))
    elif period == 3:
        return (first_day + monthdelta(1) - datetime.timedelta(1))
    elif period == 4:
        return (first_day + monthdelta(12) - datetime.timedelta(1))
    else: return None
### - ###


### + ###
# date: (datetime.date)
# return: the start of the day date (datetime.datetime). 
# ex. date=2000.2.15 >> return=2000.2.15 0h0'0"
def date_to_datetime_start(date):
    return datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
### - ###


### + ###
# date: (datetime.date)
# return: the end of the day date (datetime.datetime). 
# ex. date=2000.2.15 >> return=2000.2.15 23h59'59"
def date_to_datetime_end(date):
    return datetime.datetime(date.year, date.month, date.day, 23, 59, 59)
### - ###

### + ###
# for control with set/get text: label
def translate_control_text(control):
    control.set_text(_(control.get_text()))
### - ###

### + ###
# for control with set markup: label
def translate_control_markup(control):
    control.set_markup(_(control.get_label()))
### - ###

### + ###
# for control with set/get label: button
def translate_control_label(control):
    control.set_label(_(control.get_label()))
### - ###

### + ###
# for control with set/get title: window
def translate_control_title(control):
    control.set_title(_(control.get_title()))
### - ###

