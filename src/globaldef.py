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

import os, sys

VERSION = "2.0.alpha.b16"
VERSION_NN = "Implacable Sloth"

LICENSE = """NTM Copyright (C) 2009-2011 by Luigi Tullio <tluigi@gmail.com>.

  NTM is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option)
any later version.

  NTM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

GPL version 2 or later, see /usr/share/common-licenses/GPL-2"""


NTM_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

NTM_ICON = "./stf/ntm_nk.svg"
DEFAULT_NTM_ICON_OFF = "./stf/ntm_nk_w.svg"
DEFAULT_NTM_ICON_ON = "./stf/ntm_nk_g.svg"
REPORT_ICON = "./stf/report.svg"

NTM_PROFILE_RELPATH = ".ntm"

NTM_DB_NAME = "ntmdb_2"

DBGMSG_LEVEL = 0

