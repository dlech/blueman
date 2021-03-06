# coding=utf-8
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import dbus
from gi.repository.GObject import GObject
from blueman.bluez.errors import parse_dbus_error


class Base(GObject):
    connect_signal = GObject.connect
    disconnect_signal = GObject.disconnect

    __bus = dbus.SystemBus()
    __bus_name = 'org.bluez'

    def __new__(cls, *args, **kwargs):
        instances = cls.__dict__.get("__instances__")
        if instances is None:
            cls.__instances__ = instances = {}

        # ** Below argument parsing has to be kept in sync with _init **
        path = None
        interface_name = None

        if kwargs:
            interface_name = kwargs.get('interface_name')
            path = kwargs.get('obj_path')

        if args:
            for arg in args:
                if args is None:
                    continue
                elif '/' in arg:
                    path = arg
                elif '.' in arg:
                    interface_name = arg

        if not interface_name:
            interface_name = cls._interface_name

        if interface_name in instances:
            if path in instances[interface_name]:
                return instances[interface_name][path]

        instance = super(Base, cls).__new__(cls)
        instance._init(*args, **kwargs)
        cls.__instances__[interface_name] = {path: instance}

        return instance

    def __init__(self, *args, **kwargs):
        pass

    def _init(self, interface_name, obj_path):
        self.__signals = []
        self.__obj_path = obj_path
        self.__interface_name = interface_name
        super(Base, self).__init__()
        if obj_path:
            self.__dbus_proxy = self.__bus.get_object(self.__bus_name, obj_path, follow_name_owner_changes=True)
            self.__interface = dbus.Interface(self.__dbus_proxy, interface_name)

    def __del__(self):
        for args in self.__signals:
            self.__bus.remove_signal_receiver(*args)

    def _call(self, method, *args, **kwargs):
        def ok(*args, **kwargs):
            if callable(reply_handler):
                reply_handler(*args, **kwargs)

        def err(e):
            exception = parse_dbus_error(e)
            if callable(error_handler):
                error_handler(exception)
            else:
                raise exception

        if 'interface' in kwargs:
            interface = kwargs.pop('interface')
        else:
            interface = self.__interface

        if 'reply_handler' in kwargs:
            reply_handler = kwargs.pop('reply_handler')
        else:
            reply_handler = None

        if 'error_handler' in kwargs:
            error_handler = kwargs.pop('error_handler')
        else:
            error_handler = None

        # Make sure we have an error handler if we do async calls
        if reply_handler: assert(error_handler is not None)

        try:
            if reply_handler or error_handler:
                return getattr(interface, method)(reply_handler=ok, error_handler=err, *args, **kwargs)
            else:
                return getattr(interface, method)(*args, **kwargs)
        except dbus.DBusException as exception:
            raise parse_dbus_error(exception)

    def _handle_signal(self, handler, signal, interface_name=None, object_path=None, path_keyword=None):
        args = (handler, signal, interface_name or self.__interface_name, self.__bus_name,
                object_path or self.__obj_path)
        self.__bus.add_signal_receiver(*args, path_keyword=path_keyword)
        self.__signals.append(args)

    def get_object_path(self):
        return self.__obj_path

    @property
    def _interface_name(self):
        return self.__interface_name

    @property
    def _dbus_proxy(self):
        return self.__dbus_proxy
