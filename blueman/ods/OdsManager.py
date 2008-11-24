# Copyright (C) 2008 Valmantas Paliksa <walmis at balticum-tv dot lt>
# Copyright (C) 2008 Tadas Dailyda <tadas at dailyda dot com>
#
# Licensed under the GNU General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
import gobject
import os
from blueman.ods.OdsBase import OdsBase
from blueman.ods.OdsServer import OdsServer
from blueman.ods.OdsSession import OdsSession
from blueman.main.SignalTracker import SignalTracker


class OdsManager(OdsBase):
	__gsignals__ = {
		'server-created' : (gobject.SIGNAL_NO_HOOKS, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_STRING,)),
		'server-destroyed' : (gobject.SIGNAL_NO_HOOKS, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
		'session-created' : (gobject.SIGNAL_NO_HOOKS, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
		'session-destroyed' : (gobject.SIGNAL_NO_HOOKS, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
	}
	
	def __init__(self):
		OdsBase.__init__(self, "org.openobex.Manager", "/org/openobex")
		
		self.Servers = {}
		self.Sessions = {}
		
		self.Handle("SessionClosed", self.on_session_closed)
		self.Handle("SessionConnectError", self.on_session_error)
		self.Handle("SessionConnected", self.on_session_connected)
		
	def on_session_closed(self, session_path):
		print "__Session Closed__"
		self.Sessions[os.path.basename(session_path)].DisconnectAll()
		del self.Sessions[os.path.basename(session_path)]
		self.emit("session-destroyed", session_path)
	
	def on_session_connected(self, session_path):
		print "session_connected"
		session = self.Sessions[os.path.basename(session_path)]
		session.emit("connected")
	
	def on_session_error(self, session_path, err_name, err_msg):
		print "__error__"
		session = self.Sessions[os.path.basename(session_path)]
		session.emit("error-occurred", err_name, err_msg)
		
		#self.on_session_closed(session_path)

		
	def DisconnectAll(self, *args):
		for k,v in self.Servers.iteritems():
			v.DisconnectAll()
		self.Servers = {}
		OdsBase.DisconnectAll(self, *args)
		
		
	def get_server(self, pattern):
		try:
			return self.Servers[pattern]
		except KeyError:
			return None
	
	
	def create_session(self, dest_addr, source_addr="00:00:00:00:00:00", pattern="opp"):
		def reply(session_path):
			session = OdsSession(session_path)
			self.Sessions[os.path.basename(session_path)] = session
			self.emit("session-created", session)
		def err(*args):
			print "session err", args
	
	
		self.CreateBluetoothSession(dest_addr, source_addr, pattern, reply_handler=reply, error_handler=err)
	
	
	def create_server(self, source_addr="00:00:00:00:00:00", pattern="opp", require_pairing=False):
		def reply(path):
			server = OdsServer(path)
			self.Servers[pattern] = server
			self.emit("server-created", server, pattern)
			
			
		def err(*args):
			print "Couldn't create %s server" % pattern, args
		
		self.CreateBluetoothServer(source_addr, pattern, require_pairing, reply_handler=reply, error_handler=err)
		
	def destroy_server(self, pattern="opp"):
		print "Destroy %s server" % pattern
		def on_stopped(server):
			print "server stopped"
			server.Close()
		
		def on_closed(server):
			print "server closed"
			self.emit("server-destroyed", self.Servers[pattern].object_path)
			del self.Servers[pattern]
		
		try:
			self.Servers[pattern].GHandle("stopped", on_stopped)
			self.Servers[pattern].GHandle("closed", on_closed)
			self.Servers[pattern].Stop()

		except KeyError:
			pass
		
		

