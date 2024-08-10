#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2019, Kovid Goyal <kovid at kovidgoyal.net>

import argparse
import os
import re
import sys

args = list(sys.argv)
remove = []
for i, arg in enumerate(tuple(args)):
    m = re.match('([A-Z_]+)=(.+)', arg)
    if m is not None:
        remove.append(i)
        os.environ[m.group(1)] = m.group(2)
for r in reversed(remove):
    del args[r]


try:
    from bypy.export import setup_parser as export_setup_parser
    from bypy.linux import setup_parser as linux_setup_parser
    from bypy.macos import setup_parser as macos_setup_parser
    from bypy.main import setup_build_deps_parser, setup_program_parser, setup_shell_parser, setup_worker_status_parser, setup_reconnect_parser
    from bypy.windows import setup_parser as windows_setup_parser
    from virtual_machine.run import setup_parser as vm_setup_parser
except ImportError:
    raise  # this is here just to silence pyflakes

try:
    import certifi
except ImportError:
    pass
else:
    os.environ['SSL_CERT_FILE'] = certifi.where()


attr = None
if sys.stdout.isatty():
    try:
        import termios
    except ImportError:
        pass
    else:
        attr = termios.tcgetattr(sys.stdout.fileno())

def chroot(args):
    if os.geteuid():
        evars = [f'CHROOT_UID={os.geteuid()}', f'CHROOT_GID={os.getgid()}', f'PATH={os.environ["PATH"]}']
        if os.environ.get('TERMINFO'):
            evars.append(f'TERMINFO={os.environ["TERMINFO"]}')
        os.execlp('sudo', 'sudo', *evars, sys.executable, os.path.dirname(__file__), *sys.argv[1:])
    import importlib
    m = importlib.import_module(args.module)
    func = getattr(m, args.function)
    func(*args.func_args)


def setup_chroot_parser(p):
    p.set_defaults(func=chroot)
    p.add_argument('module', help='Module from which to import function to execute')
    p.add_argument('function', help='The name of the function to execute')
    p.add_argument('func_args', nargs='*', help='Extra arguments to pass to the function')


try:
    p = argparse.ArgumentParser(prog='bypy')
    s = p.add_subparsers(required=True)
    vm_setup_parser(s.add_parser('vm', help='Control the building and running of Virtual Machines'))
    linux_setup_parser(s.add_parser('linux', help='Build in a Linux VM'))
    macos_setup_parser(s.add_parser('macos', help='Build in a macOS VM'))
    windows_setup_parser(s.add_parser('windows', help='Build in a Windows VM', aliases=['win']))
    export_setup_parser(s.add_parser('export', help='Export built deps to a CI server'))
    setup_worker_status_parser(s.add_parser('worker-status', help='Check the status of the bypy dependency build worker'))
    setup_program_parser(s.add_parser('program', help='Build the program'))
    setup_build_deps_parser(s.add_parser('dependencies', aliases=['deps'], help='Build the dependencies'))
    setup_shell_parser(s.add_parser('shell', help='Run a shell with a completely initialized environment'))
    setup_reconnect_parser(s.add_parser('__reconnect__', help='For internal use'))
    setup_chroot_parser(s.add_parser('__chroot__', help='For internal use'))
    parsed_args = p.parse_args(args[1:])
    parsed_args.func(parsed_args)
finally:
    if attr is not None:
        termios.tcsetattr(sys.stdout.fileno(), termios.TCSANOW, attr)
