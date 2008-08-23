# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_system_port.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from spectlib.watch import Watch
import spectlib.config
from spectlib.i18n import _

import os

type = "Watch_system_port"
type_desc = "Port"
icon = 'network-transmit-receive'
category = _("System") 

def get_add_gui_info():
    return [
            ("port", spectlib.gtkconfig.Spinbutton("Port", value=21))
           ]

class Watch_system_port(Watch):
    """ 
    Watch class that will check if a connection was established on a certain port 
    """
        
    def __init__(self, specto, id, values):
        watch_values = [ 
                        ( "port", spectlib.config.Integer(True) )
                       ]
        
        self.icon = icon
        self.open_command = ''
        self.type_desc = type_desc
        self.status = ""
                
        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)
        
        self.running = self.check_port()

    def update(self):
        """ See if a socket was opened or closed. """        
        try:
            established = self.check_port()
            if self.running and established == False:
                self.running = False
                self.actually_updated = True
                self.status = "Closed"
            elif self.running == False and established == True:
                self.running = True 
                self.actually_updated = True
                self.status = "Open"
            else: 
                self.actually_updated = False
                self.status = "Unknown"
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has an error") % self.name, "error", self.__class__)
        
        Watch.timer_update(self)
        
    def check_port(self):
        """ see if there is a connection on the port or not """
        conn = False
        y=os.popen( 'netstat -nt','r').read().splitlines()
        del y[0]
        del y[0]
        for k in y:
            k = k.split(' ')
            while True:
                try:
                    k.remove('')
                except:
                    break
            try:
                port = int(k[3][k[3].rfind(':')+1:])
            except:
                port = -1
            if port == int(self.port):
                conn = True

        if conn:
            return True
        else:
            return False
        
    def get_gui_info(self):
        return [ 
                ('Name', self.name),
                ('Last updated', self.last_updated),
                ('Port', self.port),
                ('Status', self.status)
                ]
        
