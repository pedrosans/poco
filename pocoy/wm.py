import re
from gi.repository import Wnck, GdkX11, Gdk, Gio, GLib
from typing import Callable


# WORKSPACE
def is_workspaces_only_on_primary():
	return 'org.gnome.mutter' in Gio.Settings.list_schemas() and Gio.Settings.new('org.gnome.mutter').get_value('workspaces-only-on-primary')


# MONITOR
def monitor_of(xid) -> Gdk.Monitor:
	gdk_window: GdkX11.X11Window = gdk_window_for(xid=xid)
	gdk_display: GdkX11.X11Display = gdk_window.get_display()
	return gdk_display.get_monitor_at_window(gdk_window)


def intersect(window: Wnck.Window, monitor: Gdk.Monitor):
	m = monitor.get_geometry()
	w = window.get_geometry()
	return m.x <= max(0, w.xp) < (m.x + m.width) and m.y <= max(0, w.yp) < (m.y + m.height)


# WINDOW
def gdk_window_for(xid: int) -> GdkX11.X11Window:
	display = GdkX11.X11Display.get_default()
	return GdkX11.X11Window.foreign_new_for_display(display, xid)


def get_the_most_recent(window_filter: Callable = None):
	for stacked in reversed(Wnck.Screen.get_default().get_windows_stacked()):
		if not window_filter or window_filter(stacked):
			return stacked
	return None


def is_client(window: Wnck.Window):
	return not window.is_skip_tasklist() and not window.is_maximized()


def is_visible(window: Wnck.Window, workspace: Wnck.Workspace, monitor: Gdk.Monitor = None) -> bool:
	return (
			(not monitor or intersect(window, monitor))
			and (
				window.is_visible_on_workspace(workspace)
				or (is_workspaces_only_on_primary() and not monitor_of(window.get_xid()).is_primary())
			)
	)


# LAYOUT
def resize(window: Wnck.Window, x=None, y=None, w=None, h=None):

	if not w and not h:
		geometry = window.get_geometry()
		w = geometry.widthp
		h = geometry.heightp

	hints, flags = get_normal_hints(window.get_xid())

	if flags:
		w, h = Gdk.Window.constrain_size(hints, Gdk.WindowHints(flags), w, h)

	xc, yc, wc, hc = compensate_decoration(window)
	x, y, w, h = int(x + xc), int(y + yc), int(w + wc), int(h + hc)
	window.set_geometry(Wnck.WindowGravity.STATIC, RESIZE_MASK, x, y, w, h)

	return w, h


def get_normal_hints(xid: int):
	flags = 0
	hints = Gdk.Geometry()
	hints_str = GLib.spawn_command_line_sync('xprop -id %d WM_NORMAL_HINTS' % xid)
	for line in hints_str.standard_output.splitlines():
		m= re.match(r'^.*?program specified (.*?):\s*(\d+)\D*(\d+)', str(line))
		if not m:
			continue
		if m.group(1) == 'minimum size':
			hints.min_width = int(m.group(2))
			hints.min_height = int(m.group(3))
			flags = flags | Gdk.WindowHints.MIN_SIZE
		if m.group(1) == 'resize increment':
			hints.width_inc = int(m.group(2))
			hints.height_inc = int(m.group(3))
			flags = flags | Gdk.WindowHints.RESIZE_INC
		if m.group(1) == 'minimum aspect ratio':
			hints.min_aspect = int(m.group(2)) / int(m.group(3))
			flags = flags | Gdk.WindowHints.ASPECT
		if m.group(1) == 'maximum aspect ratio':
			hints.max_aspect = int(m.group(2)) / int(m.group(3))
			flags = flags | Gdk.WindowHints.ASPECT
		if m.group(1) == 'base size':
			hints.base_width = int(m.group(2))
			hints.base_height = int(m.group(3))
			flags = flags | Gdk.WindowHints.BASE_SIZE
	return hints, flags


def compensate_decoration(window: Wnck.Window):
	is_decorated, decorations = gdk_window_for(window.get_xid()).get_decorations()
	dx, dy = decoration_delta(window)
	client_side_decoration = is_decorated and not decorations and dx < 0 and dy < 0
	has_title = (
			Gdk.WMDecoration.TITLE & decorations
			or Gdk.WMDecoration.ALL & decorations
			or (not is_decorated and not decorations)  # assume server side decoration
	)

	if has_title or client_side_decoration:
		return 0, 0, 0, 0

	return -dx, -dy, dx, dy


def decoration_delta(window: Wnck.Window):
	wx, wy, ww, wh = window.get_geometry()
	cx, cy, cw, ch = window.get_client_window_geometry()

	return cx - wx, cy - wy


RESIZE_MASK = \
	Wnck.WindowMoveResizeMask.HEIGHT | \
	Wnck.WindowMoveResizeMask.WIDTH  | \
	Wnck.WindowMoveResizeMask.X      | \
	Wnck.WindowMoveResizeMask.Y
