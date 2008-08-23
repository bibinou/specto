# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_system_process.py
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

type = "Watch_system_process"
type_desc = "Process"
icon = 'applications-system'
category = _("System") 

def get_add_gui_info():
    return [
            ("process", spectlib.gtkconfig.Entry("Process"))
           ]


class Watch_system_process(Watch):
    """ 
    Watch class that will check if a process is running or not. 
    """
    
    def __init__(self, specto, id, values):
        
        watch_values = [ 
                        ( "process", spectlib.config.String(True) )
                       ]
        
        self.icon = icon
        self.open_command = ''
        self.type_desc = type_desc
        self.status = ""
                
        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)

        self.running = self.check_process()


    def update(self):
        """ See if a file was modified or created. """        
        try:
            process = self.check_process()
            if self.running and process == False:
                self.running = False
                self.updated = True
                self.actually_updated = True
                self.status = "Not running"
            elif self.running == False and process == True:
                self.running = True 
                self.actually_updated = True
                self.status = "Running"
            else: 
                self.actually_updated=False
                self.status = "Unknown"
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has an error") % self.name, "error", self.__class__)
        
        Watch.timer_update(self)
        
    def check_process(self):
        """ see if the process is running or not """
        p = ProcessList()
        pid = p.named(self.process)
        if pid:
            return True
        else:
            return False
        
    def get_gui_info(self):
        return [ 
                ('Name', self.name),
                ('Last updated', self.last_updated),
                ('Process', self.process),
                ('Status', self.status)
                ]
        


"""
Nick Craig-Wood <nick at craig-wood.com> -- http://www.craig-wood.com/nick

Manage Processes and a ProcessList under Linux.
"""

import os
import signal

class Process(object):
    """Represents a process"""
    def __init__(self, pid):
        """Make a new Process object"""
        self.proc = "/proc/%d" % pid
        pid,command,state,parent_pid = file(os.path.join(self.proc, "stat")).read().strip().split()[:4]
        command = command[1:-1]
        self.pid = int(pid)
        self.command = command
        self.state = state
        self.parent_pid = int(parent_pid)
        self.parent = None
        self.children = []
    def kill(self, sig = signal.SIGTERM):
        """Kill this process with SIGTERM by default"""
        os.kill(self.pid, sig)
    def __repr__(self):
        return "Process(pid = %r)" % self.pid
    def getcwd(self):
        """Read the current directory of this process or None for can't"""
        try:
            return os.readlink(os.path.join(self.proc, "cwd"))
        except OSError:
            return None
    
class ProcessList(object):
    """Represents a list of processes"""
    def __init__(self):
        """Read /proc and fill up the process lists"""
        self.by_pid = {}
        self.by_command = {}
        for f in os.listdir("/proc"):
            if f.isdigit():
                process = Process(int(f))
                self.by_pid[process.pid] = process
                self.by_command.setdefault(process.command, []).append(process)
        for process in self.by_pid.values():
            try:
                parent = self.by_pid[process.parent_pid]
                parent.children.append(process)
                process.parent = parent
            except KeyError:
                pass
    def named(self, name):
        """Returns a list of processes with the given name"""
        return self.by_command.get(name, [])