#!/bin/bash

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

logfile=~/.ntm/ntm.log
ntmdd=~/.ntm

if [ -d $ntmdd ]; then
    echo
    else
    mkdir ~/.ntm
fi

touch $logfile
echo >> $logfile
echo >> $logfile
echo "<<NEW RUN>>" >> $logfile
python ntm.py -v >> $logfile
date '+%Y-%m-%d %T' >> $logfile
uname -a >> $logfile
lsb_release -d >> $logfile
echo "params: " $@ >> $logfile
echo >> $logfile

activelog=0
for par in $@; do
    if [ "$par" == "-l" ]; then
        activelog=1
    fi
done

if [ "$activelog" == "0" ]; then
    python ntm.py $@ 1> /dev/null 2> /dev/null
else
    python ntm.py $@ 2>&1 | grep "[ntm]" >> $logfile
fi

