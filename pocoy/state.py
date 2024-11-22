import json
import os
from typing import Dict
from xdg import BaseDirectory as Base


def read_from_disk(file):
	if os.path.exists(file):
		with open(file, 'r') as f:
			try:
				return json.load(f)
			except json.decoder.JSONDecodeError:
				return {}
	return {}


def write_to_disk():
	with open(display_file, 'w') as f:
		json.dump(memory, f, indent=True)


def get_decorations() -> Dict:
	if 'decorations' not in memory:
		memory['decorations'] = {}
	return memory['decorations']


def is_remove_decorations() -> bool:
	return get_and_fallback('remove_decorations', memory)


def get_inner_gap() -> int:
	return get_and_fallback('inner_gap', memory)


def get_outer_gap() -> int:
	return get_and_fallback('outer_gap', memory)


def get_and_fallback(name, _dict):
	return _dict.get(name, DEFAULTS[name] if name in DEFAULTS else None)


def set_remove_decorations(remove: bool):
	memory['remove_decorations'] = remove


def set_inner_gap(gap: int):
	memory['inner_gap'] = gap


def set_outer_gap(gap: int):
	memory['outer_gap'] = gap
	write_to_disk()


cache_dir = Base.save_cache_path('pocoy')
display_file = cache_dir + '/display.json'
memory = read_from_disk(display_file)
DEFAULTS = {
	'inner_gap': 5,
	'outer_gap': 5,
	'remove_decorations': False,
	'nmaster': 1,
	'mfact': 0.55,
	'lt': '><>',
}
