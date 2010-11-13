# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       trayicon.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
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

import gtk
import os
from spectlib.i18n import _


def gettext_noop(s):
    return s


class Tray:
    """
    Display a tray icon in the notification area.
    """

    def __init__(self, specto, notifier):
        self.specto = specto
        self.notifier = notifier

        self.ICON_PATH = os.path.join(self.specto.PATH, "icons/specto_tray_1.svg")
        self.ICON2_PATH = os.path.join(self.specto.PATH, "icons/specto_tray_2.svg")
        # Create the tray icon object
        self.tray = gtk.StatusIcon()
        self.tray.set_from_file(self.ICON_PATH)
        self.tray.connect("activate", self.show_notifier)
        self.tray.connect("popup-menu", self.show_popup)
        if self.specto.specto_gconf.get_entry("always_show_icon") == True:
            self.tray.set_visible(True)
            self.notifier.builder.get_object("close").set_sensitive(True)
        else:
            self.tray.set_visible(False)
            self.notifier.builder.get_object("close").set_sensitive(False)
            self.specto.specto_gconf.set_entry("show_notifier", True)
            self.notifier.restore_size_and_position()            
            self.notifier.notifier.show()

        while gtk.events_pending():
            gtk.main_iteration(True)

    def set_icon_state_excited(self):
        """ Change the tray icon to "changed". """
        if self.specto.specto_gconf.get_entry("always_show_icon") == False:
            self.tray.set_from_file(self.ICON2_PATH)
            self.tray.set_visible(True)#we need to show the tray again
        else:
            self.tray.set_from_file(self.ICON2_PATH)

    def set_icon_state_normal(self):
        """ Change the tray icon to "not changed". If the user requested to always show the tray, it will change its icon but not disappear. Otherwise, it will be removed."""
        if self.specto.specto_gconf.get_entry("always_show_icon") == False:
            self.tray.set_visible(False)
        else:
            self.tray.set_from_file(self.ICON_PATH)

    def show_tooltip(self):
        """ Create the tooltip message and show the tooltip. """
        global _
        show_return = False
        changed_messages = self.specto.watch_db.count_changed_watches()
        message = ""

        z = 0
        y = 0
        for i in changed_messages.values():
            if i > 0:
                y += 1
                if show_return == True:
                    message += "\n"
                message += str(i) + " " + changed_messages.keys()[z]
                #message += i18n._translation.ungettext(_("watch"), _("watches"), i) #disabled, because it is redundant and not properly translatable
                show_return = True
            z += 1

        if y > 0:
            self.set_icon_state_excited()
        else:
            message = _("No changed watches.")
            self.set_icon_state_normal()

        self.tray.set_tooltip(message)

    def show_preferences(self, widget):
        """ Call the main function to show the preferences window. """
        self.notifier.show_preferences()

    def show_help(self, widget):
        """ Call the main function to show help. """
        self.notifier.show_help()

    def show_about(self, widget):
        """ Call the main function to show the about window. """
        self.notifier.show_about()

    def refresh(self, widget):
        self.notifier.refresh_all_watches()

    def show_notifier(self, widget):
        """ Call the main function to show the notifier window. """
        if self.specto.specto_gconf.get_entry("always_show_icon") == True:
            self.specto.toggle_notifier()
        else:
            self.specto.notifier.notifier.present()

    def show_popup(self, status_icon, button, activate_time):
        """
        Create the popupmenu
        """
        ## From the PyGTK 2.10 documentation
        # status_icon : the object which received the signal
        # button :      the button that was pressed, or 0 if the signal is not emitted in response to a button press event
        # activate_time :       the timestamp of the event that triggered the signal emission

        # Create menu items
        def create_menu_item(label, callback=None, icon=None):
            menuItem = gtk.MenuItem(label, True)
            if icon:
                menuItem = gtk.ImageMenuItem(label)
                image = gtk.Image()
                image.set_from_stock(icon, gtk.ICON_SIZE_MENU)
                menuItem.set_image(image)
                image.show()
            if callback:
                menuItem.connect('activate', callback)
            return menuItem

        if self.specto.specto_gconf.get_entry("always_show_icon") \
                and self.specto.notifier.get_state():
            self.item_show = create_menu_item(_("Hide window"), self.show_notifier, None)
        else:
            self.item_show = create_menu_item(_("Show window"), self.show_notifier, None)

        self.item_pref = create_menu_item(gtk.STOCK_PREFERENCES, self.show_preferences, gtk.STOCK_PREFERENCES)
        self.item_help = create_menu_item(gtk.STOCK_HELP, self.show_help, gtk.STOCK_HELP)
        self.item_about = create_menu_item(gtk.STOCK_ABOUT, self.show_about, gtk.STOCK_ABOUT)
        self.item_quit = create_menu_item(gtk.STOCK_QUIT, self.quit, gtk.STOCK_QUIT)
        self.item_clear = create_menu_item(_("Mark as read"), None, None)
        self.item_refresh = create_menu_item(_("Refresh All"), self.refresh, gtk.STOCK_REFRESH)

        #create submenu for changed watches
        self.sub_menu = gtk.Menu()

        self.sub_item_clear = create_menu_item(_("_Mark all read"),
                self.specto.notifier.mark_all_as_read, gtk.STOCK_CLEAR)
        self.sub_menu.append(self.sub_item_clear)

        self.sub_menu.append(gtk.SeparatorMenuItem())

        for watch in self.specto.watch_db:
            if watch.changed == True:
                image = gtk.image_new_from_pixbuf(self.notifier.get_icon(watch.icon, 0, False))
                self.sub_item_clear = create_menu_item(watch.name, None, image)
                self.sub_item_clear.connect('activate', self.specto.notifier.mark_watch_as_read, watch.id)
                self.sub_menu.append(self.sub_item_clear)

        self.sub_menu.show_all()
        self.item_clear.set_submenu(self.sub_menu)

        # Create the menu
        self.menu = gtk.Menu()

        # Append menu items to the menu
        self.menu.append(self.item_show)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.item_refresh)
        self.menu.append(self.item_clear)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.item_pref)
        self.menu.append(self.item_help)
        self.menu.append(self.item_about)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.item_quit)
        self.menu.show_all()
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, self.tray)#the last argument is to tell gtk.status_icon_position_menu where to grab the coordinates to position the popup menu correctly

    def get_x(self):
        if self.tray.get_visible()==True:
            x = self.tray.get_geometry()[1][0]
            x += int(self.tray.get_size() / 2) #add half the icon's width
        else:
            x = 0 #remove half the icon's width
            #FIXME: I don't know why that one does not work
        return x

    def get_y(self):
        if self.tray.get_visible()==True:
            y = self.tray.get_geometry()[1][1]
            y += int(self.tray.get_size() / 2) #add half the icon's height
        else:
            y = 0 #remove half the icon's height
            #FIXME: I don't know why that one does not work
        return y

    def destroy(self):
        self.tray.set_visible(False)

    def quit(self, widget):
        """ Call the main function to quit specto. """
        self.specto.quit()
