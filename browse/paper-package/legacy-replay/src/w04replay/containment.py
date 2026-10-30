"""Accidental I/O containment for trusted replay code, not a hostile-code sandbox."""
import os
from pathlib import Path
import sys


def install(root, output, stdlib_roots, executable):
    readable = [root.resolve(), *[Path(p).resolve() for p in stdlib_roots]]
    if output is not None:
        readable.append(output.resolve())
    executable = executable.resolve()
    report = {'denied': [], 'read_scope': 'workbench, output and Python standard library only',
              'network': 'denied', 'child_processes': 'denied',
              'limitation': 'CPython audit hook for trusted code; not an OS security boundary'}

    def under(path, directory):
        return path == directory or directory in path.parents

    def access(path, write=False):
        if isinstance(path, int):
            return path in (0, 1, 2)
        path = Path(os.fsdecode(path)).resolve()
        if write:
            return output is not None and under(path, output)
        return path == executable or any(under(path, base) for base in readable)

    def deny(event):
        report['denied'].append(event)
        raise PermissionError('replay I/O policy: ' + event)

    def hook(event, args):
        if event.startswith(('socket.', 'subprocess.', 'ctypes.')) or event in (
                'os.system', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.posix_spawnp',
                'os.exec', 'os.spawn', 'os.kill', 'os.killpg'):
            deny(event)
        if event == 'open':
            path, mode, flags = args
            write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if not access(path, write):
                deny('open_write' if write else 'open_read')
        elif event in ('os.listdir', 'os.scandir'):
            if not access(args[0] if args else '.'):
                deny(event)
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime', 'os.truncate'):
            if not access(args[0], True):
                deny(event)
        elif event in ('os.rename', 'os.link', 'os.symlink'):
            deny(event)
    sys.addaudithook(hook)
    return report


def controls(root):
    import socket
    import subprocess
    checks = []
    actions = {
        'external_read_blocked': lambda: open('/etc/hosts', 'rb'),
        'input_write_blocked': lambda: open(root / 'data/cases.json', 'w'),
        'socket_creation_blocked': lambda: socket.socket(),
        'child_process_blocked': lambda: subprocess.run(['/usr/bin/true'], check=True),
    }
    for name, action in actions.items():
        try:
            resource = action()
            if hasattr(resource, 'close'):
                resource.close()
        except PermissionError:
            checks.append({'check': name, 'passed': True})
        else:
            raise ValueError('I/O containment failed: ' + name)
    return checks
