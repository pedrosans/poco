# MIT/X Consortium License
# 
# © 2006-2009 Anselm R Garbe <garbeam at gmail dot com>
# © 2006-2007 Sander van Dijk <a dot h dot vandijk at gmail dot com>
# © 2006-2009 Jukka Salmi <jukka at salmi dot ch>
# © 2007-2009 Premysl Hruby <dfenze at gmail dot com>
# © 2007-2009 Szabolcs Nagy <nszabolcs at gmail dot com>
# © 2007-2009 Christof Musik <christof at sendfax dot de>
# © 2007-2008 Enno Gottox Boland <gottox at s01 dot de>
# © 2007-2008 Peter Hartlich <sgkkr at hartlich dot com>
# © 2008 Martin Hurton <martin dot hurton at gmail dot com>
# © 2008 Neale Pickett <neale dot woozle dot org>
# © 2009 Mate Nagy <mnagy@port70.net>
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from gi.repository import Wnck
from functools import reduce
from typing import List
from pocoy import state, Window, Monitor
from pocoy.wm import resize


# https://git.suckless.org/dwm/file/dwm.c.html#l1674
def tile(clients: List[Wnck.Window], m: Monitor):
	n = len(clients)

	if n > m.nmaster:
		mw = m.ww * m.mfact if m.nmaster else 0
	else:
		mw = m.ww
	my = ty = 0
	padding = state.get_inner_gap()

	for i in range(len(clients)):
		window = clients[i]
		if i < m.nmaster:
			h = (m.wh - my) / (min(n, m.nmaster) - i) - padding * 2
			w, h = resize(
				window, x=m.wx + padding, y=m.wy + my + ty + padding, w=mw - padding * 2, h=h)
			my += h + padding * 2
		else:
			h = (m.wh - ty) / (n - i) - padding * 2
			w, h = resize(
				window, x=m.wx + mw + padding, y=m.wy + ty + padding, w=m.ww - mw - padding * 2, h=h)
			ty += h + padding * 2


# https://git.suckless.org/dwm/file/dwm.c.html#l1104
def monocle(clients, monitor):
	padding = state.get_inner_gap()
	for window in clients:
		resize(
			window,
			x=monitor.wx + padding, y=monitor.wy + padding,
			w=monitor.ww - padding * 2, h=monitor.wh - padding * 2)
	import pocoy.wm as wm
	wm.gdk_window_for(clients[0].get_xid()).focus(0)


# https://dwm.suckless.org/patches/centeredmaster/
def centeredmaster(clients: List[Wnck.Window], m: Monitor):
	tw = mw = m.ww
	mx = my = 0
	oty = ety = 0
	n = len(clients)
	padding = state.get_inner_gap()

	if n > m.nmaster:
		mw = int(m.ww * m.mfact) if m.nmaster else 0
		tw = m.ww - mw

		if n - m.nmaster > 1:
			mx = int((m.ww - mw) / 2)
			tw = int((m.ww - mw) / 2)

	for i in range(len(clients)):
		window = clients[i]
		if i < m.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((m.wh - my) / (min(n, m.nmaster) - i)) - padding * 2
			w, h = resize(
				window, x=m.wx + mx + padding, y=m.wy + my + padding, w=mw - padding * 2, h=h)
			my += h + padding * 2
		else:
			# stack clients are stacked vertically
			if (i - m.nmaster) % 2:
				h = int((m.wh - ety) / int((1 + n - i) / 2)) - padding * 2
				w, h = resize(
					window, x=m.wx + padding, y=m.wy + ety + padding, w=tw - padding * 2, h=h)
				ety += h + padding * 2
			else:
				h = int((m.wh - oty) / int((1 + n - i) / 2)) - padding * 2
				w, h = resize(
					window, x=m.wx + mx + mw + padding, y=m.wy + oty + padding, w=tw - padding * 2, h=h)
				oty += h + padding * 2


def centeredfloatingmaster(clients: List[Wnck.Window], m: Monitor):
	padding = state.get_inner_gap()
	# i, n, w, mh, mw, mx, mxo, my, myo, tx = 0
	tx = mx = 0

	# count number of clients in the selected monitor
	n = len(clients)

	# initialize nmaster area
	if n > m.nmaster:
		# go mfact box in the center if more than nmaster clients
		if m.ww > m.wh:
			mw = m.ww * m.mfact if m.nmaster else 0
			mh = m.wh * 0.9 if m.nmaster else 0
		else:
			mh = m.wh * m.mfact if m.nmaster else 0
			mw = m.ww * 0.9 if m.nmaster else 0
		mx = mxo = (m.ww - mw) / 2
		my = myo = (m.wh - mh) / 2
	else:
		# go fullscreen if all clients are in the master area
		mh = m.wh
		mw = m.ww
		mx = mxo = 0
		my = myo = 0

	for i in range(len(clients)):
		c = clients[i]
		if i < m.nmaster:
			# nmaster clients are stacked horizontally, in the center of the screen
			w = (mw + mxo - mx) / (min(n, m.nmaster) - i)
			w, h = resize(
				c,
				x=m.wx + mx + padding, y=m.wy + my + padding,
				w=w, h=mh - padding * 2)
			mx += w + padding * 2
		else:
			# stack clients are stacked horizontally
			w = (m.ww - tx) / (n - i) - (padding * 2)
			w, h = resize(
				c,
				x=m.wx + tx + padding, y=m.wy + padding,
				w=w, h=m.wh - padding * 2)
			tx += w + padding * 2


# https://dwm.suckless.org/patches/fibonacci/
def fibonacci(mon: Monitor, clients: List[int], s: int):
	n = len(clients)
	nx = mon.wx
	ny = 0
	nw = mon.ww
	nh = mon.wh
	padding = state.get_inner_gap()

	for i in range(n):
		c = clients[i]
		c.bw = 0
		if (i % 2 and nh / 2 > 2 * c.bw) or (not (i % 2) and nw / 2 > 2 * c.bw):
			if i < n - 1:
				if i % 2:
					nh /= 2
				else:
					nw /= 2
				if (i % 4) == 2 and not s:
					nx += nw
				elif (i % 4) == 3 and not s:
					ny += nh
			if (i % 4) == 0:
				if s:
					ny += nh
				else:
					ny -= nh
			elif (i % 4) == 1:
				nx += nw
			elif (i % 4) == 2:
				ny += nh
			elif (i % 4) == 3:
				if s:
					nx += nw
				else:
					nx -= nw
			if i == 0:
				if n != 1:
					nw = mon.ww * mon.mfact
				ny = mon.wy
			elif i == 1:
				nw = mon.ww - nw
		resize(
			c,
			x=nx + padding, y=ny + padding,
			w=nw - padding * 2, h=nh - padding * 2)


def dwindle(clients: List[Wnck.Window], monitor: Monitor):
	fibonacci(monitor, clients, 1)


def spiral(clients: List[Wnck.Window], monitor: Monitor):
	fibonacci(monitor, clients, 0)


def frezze(clients: List[Wnck.Window], monitor: Monitor):
	pass

def flow(clients: List[Wnck.Window], monitor: Monitor):
	n = len(clients)
	if n == 1:
		resize(
			clients[0],
			x=monitor.wx + monitor.ww * 0.15, y=monitor.wy + monitor.wh * 0.1, w=monitor.ww * 0.7, h=monitor.wh * 0.86)
		return
	oty = 0
	mw = int(monitor.ww * monitor.mfact) if monitor.nmaster else 0
	mx = tw = int((monitor.ww - mw) / 2)
	my = 0
	padding = state.get_inner_gap()

	for i in range(n):
		window: Wnck.Window = clients[i]
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((monitor.wh - my) / (min(n, monitor.nmaster) - i))
			resize(
				window,
				x=monitor.wx + mx + padding, y=monitor.wy + my + padding,
				w=mw - padding * 2, h=h - padding * 2)
			my += h
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) == 0:
				resize(
					window,
					x=monitor.wx + padding, y=monitor.wy + padding,
					w=tw - padding * 2, h=monitor.wh - padding * 2)
			else:
				tw = monitor.ww - mw - tw
				h = int((monitor.wh - oty) / (n - i))
				w, h = resize(
					window,
					x=monitor.wx + mx + mw + padding, y=monitor.wy + oty + padding,
					w=tw - padding * 2, h=h - padding * 2)
				oty += h + padding * 2


def tile_monitor(d:Window, m:Monitor):
	FUNCTION_BY_LT[m.lt](list(map(lambda xid: d.window_by_xid[xid], m.clients)), m)


def is_laid_out(d:Window, m:Monitor):
	if m.lt in ['><>', '[f]']:
		return True

	class Mock:
		def __init__(self, xid):
			self.xid = xid

		def get_xid(self):
			return self.xid

		def get_geometry(self):
			return d.window_by_xid[self.xid].get_geometry()

		def get_client_window_geometry(self):
			return d.window_by_xid[self.xid].get_client_window_geometry()

		def set_geometry(self, gravity, mask, x, y, w, h):
			self.destination = (x, y, w, h)

		def is_tiled(self):
			tolerance = 200
			origin = d.window_by_xid[self.xid].get_geometry()
			return reduce(lambda b, i: b and self.destination[i] - tolerance < origin[i] < self.destination[i] + tolerance, [0, 1, 2, 3], True)

	mocks = list(map(lambda xid: Mock(xid), m.clients))

	FUNCTION_BY_LT[m.lt](mocks, m)

	return reduce(lambda b, mock: b and mock.is_tiled(), mocks, True)


FUNCTION_BY_LT = {
	'><>': lambda *a: None,
	'[M]': monocle,
	'[T]': tile,
	'[C]': centeredmaster,
	'[c]': centeredfloatingmaster,
	'[@]': spiral,
	'[D]': dwindle,
	'[F]': flow,
	'[f]': frezze
}
