# coding=utf-8
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

from blueman.Functions import dprint
from blueman.bluez.obex.Base import Base
from gi.repository import GObject


class ObjectPush(Base):
    __gsignals__ = {
        str('transfer-started'): (GObject.SignalFlags.NO_HOOKS, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT,)),
        str('transfer-failed'): (GObject.SignalFlags.NO_HOOKS, None, (GObject.TYPE_PYOBJECT,)),
    }

    _interface_name = 'org.bluez.obex.ObjectPush1'

    def _init(self, session_path):
        super(ObjectPush, self)._init(interface_name=self._interface_name, obj_path=session_path)

    def send_file(self, file_path):
        def on_transfer_started(transfer_path, props):
            dprint(self.get_object_path(), file_path, transfer_path)
            self.emit('transfer-started', transfer_path, props['Filename'])

        def on_transfer_error(error):
            dprint(file_path, error)
            self.emit('transfer-failed', error)

        self._call('SendFile', file_path, reply_handler=on_transfer_started, error_handler=on_transfer_error)

    def get_session_path(self):
        return self.get_object_path()
