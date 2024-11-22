from functools import reduce
from pocoy import state, root, gtk, layout


@gtk(persist=True)
def zoom(argv):
	flags = argv[1] if len(argv) > 1 else ''
	force_active_window = 'f' in flags
	monitor = root.selected_monitor
	clients = monitor.clients

	if len(clients) == 0: return

	if root.active_xid not in clients and force_active_window: return

	if len(clients) > 1 and root.active_xid in clients:
		i = clients.index(root.top_client_xid)
		clients.insert(0 if force_active_window or not layout.is_laid_out(root, monitor) or (i > 0 and monitor.lt != '><>') else 1, clients.pop(i))

	for xid in reversed(clients): root.focus(xid)
	monitor.arrange()
	root.apply_decoration_config()


@gtk(persist=True)
def setmfact(argv):
	monitor = root.selected_monitor
	monitor.mfact = max(min(0.9, monitor.mfact + float(argv[1])), 0.1)
	monitor.arrange()


@gtk(persist=True)
def incnmaster(argv):
	monitor = root.selected_monitor
	monitor.nmaster = max(min(len(monitor.clients), monitor.nmaster + int(argv[1])), 0)
	monitor.arrange()


@gtk(persist=False)
def focusstack(argv):
	if not root.top_client_xid:
		return
	direction = int(argv[1])
	monitor = root.selected_monitor
	clients = monitor.clients

	old_index = clients.index(root.top_client_xid)
	new_index = (old_index + direction) % len(clients)

	root.focus(clients[new_index])


@gtk(persist=True)
def pushstack(argv):
	if not root.top_client_xid:
		return
	direction = int(argv[1])
	monitor = root.selected_monitor
	clients = monitor.clients
	old_index = clients.index(root.top_client_xid)
	new_index = (old_index + direction) % len(clients)

	if new_index != old_index:
		clients.insert(new_index, clients.pop(old_index))
		monitor.arrange()


@gtk(persist=True)
def setlayout(argv):
	if not root.top_client_xid:
		return
	cli = list(map(lambda arg: arg.replace('[', '').replace(']', ''), layout.FUNCTION_BY_LT.keys()))
	if reduce(lambda b, arg: b or arg not in cli and arg.lower() not in ['none', 'last'], argv[1:], False):
		return
	monitor = root.selected_monitor
	symbols = list(map(lambda i: '><>' if argv[i] == 'none' else monitor.last_lt if argv[i] == 'last' else '[%s]' % (argv[i]), range(1, len(argv))))

	monitor.set_layout(symbols[0] if symbols else monitor.lt) if len(symbols) < 2 else monitor.toogle(symbols)
	monitor.arrange()
	root.apply_decoration_config()


@gtk(persist=True)
def gap(argv):
	parameters = argv[1:]
	where = parameters[0]
	pixels = int(parameters[1])
	state.set_outer_gap(pixels) if where == 'outer' else state.set_inner_gap(pixels)
	for monitor in root.monitors():
		if not monitor.is_available():
			continue
		monitor.update_work_area()
		monitor.arrange(unmaximize=True)


@gtk(persist=True)
def decorate(argv):
	arg = argv[1].lower().strip()
	state.set_remove_decorations(not state.is_remove_decorations() if arg == 'toogle' else arg == 'remove')
	root.apply_decoration_config()


@gtk(persist=False)
def print_state(argv):
	print(reduce(
		lambda s, w: "{:}{:10}({:2}) - {}\n".format(s, w.get_xid(), w.get_workspace().get_number() if w.get_workspace() else -1, w.get_name()),
		root.window_by_xid.values(),
		reduce(
			lambda s, kv: "{}{}".format(s, reduce(
				lambda _s, v: '{}{} {:60}\n'.format(_s, v.id, str(v.clients)),
				sorted(kv[1], key=lambda m: m.wx if m.wx else -1), '')),
			root.monitors_by_workspace.items(), '')
	))
