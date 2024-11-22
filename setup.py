#!/usr/bin/env python3
from distutils.core import setup

setup(
	name='pocoy',
	version='0.4.7',
	description='pluggable window management',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/pocoy',
	classifiers=['License :: GPL3'],
	packages=['pocoy'],
	scripts=['bin/pocoy'],
	data_files=
	[
		('/usr/share/man/man1/', ['pocoy.1.gz']),
	],
)

# eof
