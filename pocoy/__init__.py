import gi, traceback
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk, GLib, Gtk
from typing import Dict, List, Tuple
from pocoy import state, wm


class Monitor:

	def __init__(self, _id: Tuple[int, str]):
		self.id: Tuple[int, str] = _id
		self.workspace: int = _id[0]
		self.model: str = _id[1]
		self.primary = False
		self.lt: str = state.DEFAULTS['lt']
		self.last_lt: str = None
		self.nmaster: int = state.DEFAULTS['nmaster']
		self.mfact: float = state.DEFAULTS['mfact']
		self.wx = self.wy = self.ww = self.wh = 0
		self.clients: List[int] = []
		self.target_work_area: List[int] = [0, 0, 0, 0]

	def is_available(self):
		return not wm.is_workspaces_only_on_primary() or self.primary or self.workspace == 0
	
	def toogle(self, options):
		self.set_layout(options[(options.index(self.lt) + 1) % len(options)] if self.lt in options else options[0])

	def set_layout(self, new_key):
		if self.lt != new_key:
			self.last_lt = self.lt
			self.lt = new_key

	def arrange(self, unmaximize: bool = False):
		if not self.lt: return
		if unmaximize:
			for window in root.window_by_xid.values():
				window.unmaximize()
				window.set_fullscreen(False)
		import pocoy.layout
		pocoy.layout.tile_monitor(root, self)

	def set_rectangle(self, rectangle: Gdk.Rectangle):
		self.target_work_area = [rectangle.x, rectangle.y, rectangle.width, rectangle.height]
		self.update_work_area()

	def update_work_area(self):
		outer_gap = state.get_outer_gap()
		self.wx = self.target_work_area[0] + outer_gap
		self.wy = self.target_work_area[1] + outer_gap
		self.ww = self.target_work_area[2] - outer_gap * 2
		self.wh = self.target_work_area[3] - outer_gap * 2

	def from_json(self, monitor_json):
		self.nmaster = state.get_and_fallback('nmaster', monitor_json)
		self.mfact = state.get_and_fallback('mfact', monitor_json)
		self.lt = state.get_and_fallback('lt', monitor_json)
		self.last_lt = state.get_and_fallback('last_lt', monitor_json)
		self.clients = state.get_and_fallback('clients', monitor_json)
		return self

	def to_json(self):
		return {
			'workspace': self.id[0],
			'model': self.id[1],
			'nmaster': self.nmaster,
			'mfact': self.mfact,
			'lt': self.lt,
			'last_lt': self.last_lt,
			'clients': self.clients
		}


class Window:

	def __init__(self):
		self.active_xid = None
		self.top_client_xid = None
		self.selected_monitor: Monitor = None
		self.monitor_by_id: Dict[Tuple, Monitor] = {}
		self.window_by_xid: Dict[int, Wnck.Window] = {}
		self.monitors_by_workspace: Dict[int, List[Monitor]] = {}

	def load_from(self, serializable):
		if 'workspaces' not in serializable:
			return
		try:
			for workspace_json in serializable['workspaces']:
				for monitor_json in workspace_json['monitors']:
					monitor = Monitor((monitor_json['workspace'], monitor_json['model']))
					monitor.from_json(monitor_json)
					self.add_monitor(monitor)
		except (KeyError, TypeError):
			traceback.print_stack()
			traceback.print_exc()

	def unload_to(self, serializable):
		serializable['workspaces'] = [
			{
				'monitors': [monitor.to_json() for monitor in self.monitors_by_workspace[i]]
			} for i in self.monitors_by_workspace.keys()
		]

	def read(self, gdk_display: Gdk.Display, screen: Wnck.Screen):
		by_model = {m.get_model(): m for m in map(lambda i: gdk_display.get_monitor(i), range(gdk_display.get_n_monitors()))}
		by_number = {w.get_number(): w for w in screen.get_workspaces()}
		primary_monitor_model = gdk_display.get_primary_monitor().get_model()

		def read_monitors():
			def read_workspace_monitor_pairs(wnck_workspace, gdk_monitor):
				id = (wnck_workspace.get_number(), gdk_monitor.get_model())
				if id not in self.monitor_by_id:
					self.add_monitor(Monitor(id))
				self.monitor_by_id[id].primary = gdk_monitor.is_primary()
				self.monitor_by_id[id].set_rectangle(gdk_monitor.get_workarea())
			for wnck_workspace in by_number.values():
				for gdk_monitor in by_model.values():
					read_workspace_monitor_pairs(wnck_workspace, gdk_monitor)

		def read_windows():
			def read_clients(monitor):
				if not monitor.is_available() or monitor.workspace not in by_number or monitor.model not in by_model:
					del monitor.clients[:]
					return

				monitor_filter = lambda xid: xid and xid in self.window_by_xid and wm.is_client(self.window_by_xid[xid]) \
						and wm.is_visible(self.window_by_xid[xid], by_number[monitor.workspace], by_model[monitor.model])

				monitor.clients = list(filter(
					monitor_filter,
					[w.get_xid() for w in screen.get_windows_stacked() if w.get_xid() not in monitor.clients] + monitor.clients
				))
			self.window_by_xid = {w.get_xid(): w for w in screen.get_windows()}
			for monitor in self.monitor_by_id.values():
				read_clients(monitor)

		def read_selection():
			top_client= wm.get_the_most_recent(lambda w: wm.is_client(w) and wm.is_visible(w, screen.get_active_workspace()))
			workspace_number = top_client.get_workspace().get_number() if top_client else screen.get_active_workspace().get_number()
			model = wm.monitor_of(top_client.get_xid()).get_model() if top_client else primary_monitor_model
			self.active_xid = screen.get_active_window().get_xid()
			self.top_client_xid = top_client.get_xid() if top_client else None
			self.selected_monitor = self.monitor_by_id[(workspace_number, model)]

		read_monitors()
		read_windows()
		read_selection()

	def add_monitor(self, monitor: Monitor):
		if monitor.id in self.monitor_by_id:
			return
		self.monitor_by_id[monitor.id] = monitor
		if monitor.workspace not in self.monitors_by_workspace:
			self.monitors_by_workspace[monitor.workspace] = []
		self.monitors_by_workspace[monitor.workspace].append(monitor)

	def focus(self, xid: int):
		wm.gdk_window_for(xid).focus(0)

	def monitors(self) -> List[Monitor]:
		return list(self.monitor_by_id.values())

	def apply_decoration_config(self):
		memory = state.get_decorations()

		def remove_decoration(windows_xid: List[int]):
			for xid in windows_xid:

				key = str(xid)
				gdk_w = wm.gdk_window_for(xid)

				is_decorated, decorations = gdk_w.get_decorations()
				has_title = Gdk.WMDecoration.TITLE & decorations or Gdk.WMDecoration.ALL & decorations
				ssd = not is_decorated and not decorations

				if has_title or ssd:
					if key not in memory:
						memory[key] = decorations if not ssd else Gdk.WMDecoration.ALL
					gdk_w.set_decorations(Gdk.WMDecoration.BORDER)

		def restore_decoration(windows_xid: List[int]):
			for xid in windows_xid:
				key = str(xid)
				if key in memory:
					wm.gdk_window_for(xid).set_decorations(Gdk.WMDecoration(memory[key]))
					del memory[key]

		if state.is_remove_decorations():
			tiled = []
			floating = []
			for monitor in self.monitors():
				(tiled if monitor.lt != '><>' else floating).extend(monitor.clients)
			tiled.extend(filter(lambda xid: self.window_by_xid[xid].is_maximized(), self.window_by_xid.keys()))
			remove_decoration(tiled)
			restore_decoration(floating)
		else:
			restore_decoration(self.window_by_xid.keys())

		for key in list(memory):
			if int(key) not in root.window_by_xid: del memory[key]


def gtk(persist: bool = False):
	def decorator(command):
		def read_write_state(*args, **kwargs):

			root.load_from(state.memory)

			GLib.idle_add(_inside_main, command, *args, **kwargs, priority=GLib.PRIORITY_HIGH)

			Gtk.main()

			if persist:
				root.unload_to(state.memory)
				state.write_to_disk()

		return read_write_state
	return decorator


def _inside_main(command,  *args, **kwargs):
	try:
		gdk_display = Gdk.Display.get_default()
		wnck_screen = Wnck.Screen.get_default()
		wnck_screen.force_update()
		root.read(gdk_display, wnck_screen)

		command(*args, **kwargs)

		gdk_display.sync()

	except Exception as e:
		traceback.print_stack()
		traceback.print_exc()
	finally:
		gdk_display.close()
		Gtk.main_quit()
		return False


root = Window()
