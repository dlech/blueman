# coding=utf-8
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

from gi.repository import GObject
from blueman.Functions import dprint
from blueman.bluez.PropertiesBase import PropertiesBase
from blueman.bluez.Device import Device
import dbus


class Adapter(PropertiesBase):
    _interface_name = 'org.bluez.Adapter1'

    def _init(self, obj_path=None):
        super(Adapter, self)._init(interface_name=self._interface_name, obj_path=obj_path)
        proxy = dbus.SystemBus().get_object('org.bluez', '/', follow_name_owner_changes=True)
        self.manager_interface = dbus.Interface(proxy, 'org.freedesktop.DBus.ObjectManager')

    def find_device(self, address):
        devices = self.list_devices()
        for device in devices:
            if device.get_properties()['Address'] == address:
                return device

    def list_devices(self):
        objects = self._call('GetManagedObjects', interface=self.manager_interface)
        devices = []
        for path, interfaces in objects.items():
            if 'org.bluez.Device1' in interfaces:
                if path.startswith(self.get_object_path()):
                    devices.append(path)
        return [Device(device) for device in devices]

    def start_discovery(self):
        self._call('StartDiscovery')

    def stop_discovery(self):
        self._call('StopDiscovery')

    def remove_device(self, device):
        self._call('RemoveDevice', device.get_object_path())

    # FIXME in BlueZ 5.31 getting and setting Alias appears to never fail
    def get_name(self):
        props = self.get_properties()
        try:
            return props['Alias']
        except KeyError:
            return props['Name']

    def set_name(self, name):
        try:
            return self.set('Alias', name)
        except dbus.exceptions.DBusException:
            return self.set('Name', name)
