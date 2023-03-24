#!/usr/bin/env python

import argparse
import os
import re
import subprocess
import sys
import time


DEFAULT_WAKEUP_PORT = 40000
DEFAULT_WAKEUP_DELAY = 60 # seconds

DEFAULT_TUNNEL_ARG = '65535'
DEFAULT_RTUNNEL_ARG = DEFAULT_TUNNEL_ARG + ':localhost:22'

DEFAULT_LOCAL_PATH = './'
DEFAULT_REMOTE_PATH = '~/'

STATUS_TIMEOUT = 5 # seconds

DEFAULT_SSH_TERM = 'xterm-256color'


OP_URL = 'url'
OP_STATUS = 'stat'
OP_SSH = 'ssh'
OP_TUNNEL = 'tunnel'
OP_RTUNNEL = 'rtunnel'
OP_SSHFS = 'mount'
OP_DOWNLOAD = 'download'
OP_UPLOAD = 'upload'


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def host_addr_str(value: str) -> str:
    """Check host address for validity.
    Raise ValueError in case of invalid value.
    Return the unchanged value.
    """
    if re.fullmatch('^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$', value):
        return value
    else:
        raise ValueError

def user_name_str(value: str) -> str:
    """Check user name for validity.
    Raise ValueError in case of invalid value.
    Return the unchanged value.
    """
    if re.fullmatch('^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$', value):
        return value
    else:
        raise ValueError

def mac_addr_str(value: str) -> str:
    """Check MAC address for validity.
    Raise ValueError in case of invalid value.
    Return the unchanged value.
    """
    if re.fullmatch('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', value):
        return value
    else:
        raise ValueError

def port_int(value: str) -> int:
    """Check host port for validity.
    Raise ValueError in case of invalid value.
    Return the unchanged value.
    """
    port = int(value)
    if port > 0 and port < 65536:
        return port
    else:
        raise ValueError

def seconds_int(value: str) -> int:
    """Check number of seconds for validity.
    Raise ValueError in case of invalid value.
    Return the unchanged value.
    """
    seconds = int(value)
    if seconds >= 0:
        return seconds
    else:
        raise ValueError

def parse_args() -> dict:
    """Parse command line arguments.
    Return dict of parsed values.
    """
    formatter = lambda prog: argparse.HelpFormatter(prog, width=100, max_help_position=40)

    arg_parser = argparse.ArgumentParser(description="Remote host control",
                                         add_help=False, formatter_class=formatter)

    arg_parser.add_argument('--help', action='help',
                            help="show this help message and exit")
    arg_parser.add_argument('-n', '--dry-run', action='store_true', dest='dry_run',
                            help="don't do anything, only print commands to be executed")

    args_registry = arg_parser.add_argument_group(title="host registry")

    args_registry.add_argument('-L', '--lan', action='store_true', dest='lan',
                              help="access remote host using local address and port")

    args_registry.add_argument('-h', '--host', type=host_addr_str, dest='host',
                              metavar="HOST", help="registered name of known remote host")

    args_address = arg_parser.add_argument_group(title="address")

    args_address.add_argument('-s', '--addr', type=host_addr_str, dest='address',
                              metavar="ADDR", help="address (IP or domain name) of remote host")
    args_address.add_argument('-p', '--port', type=port_int, dest='port',
                              metavar="PORT", help="port of remote host")

    args_address.add_argument('-u', '--user', type=user_name_str, dest='user',
                              metavar="USER", help="remote user name")

    args_wakeup = arg_parser.add_argument_group(title="wakeup")

    args_wakeup.add_argument('-w', '--wakeup', action='store_true', dest='wakeup',
                             help="wake up remote host")
    args_wakeup.add_argument('-m', '--wakeup-mac', type=mac_addr_str, dest='wakeup_mac',
                             metavar="MAC", help="MAC address to wake up")
    args_wakeup.add_argument('-P', '--wakeup-port', type=port_int, dest='wakeup_port',
                             metavar="PORT", help="port to send magic packet to")
    args_wakeup.add_argument('-d', '--wakeup-delay', type=seconds_int, dest='wakeup_delay',
                             metavar="SECONDS", help="time for remote host to wake up")

    args_operation = arg_parser.add_argument_group(title="operation")

    operations = [OP_URL, OP_STATUS, OP_SSH, OP_TUNNEL, OP_RTUNNEL, OP_SSHFS, OP_DOWNLOAD, OP_UPLOAD]
    args_operation.add_argument('-o', '--op', choices=operations, dest='operation',
                                metavar="OP_TYPE", help=f"operation type ({', '.join(operations)})")

    args_operation.add_argument('--cmd', nargs='+', default=[], dest='ssh_command',
                                metavar="CMD", help="ssh command to execute remotely")
    args_operation.add_argument('-t', '--tunnel', dest='ssh_tunnel_arg',
                                metavar="TUNNEL_ARG", help="ssh tunnel argument (port and/or binding address)")

    args_path = arg_parser.add_argument_group(title="operation paths")

    args_path.add_argument('-l', '--lpath', dest='local_path',
                           metavar="PATH", help="local path")
    args_path.add_argument('-r', '--rpath', dest='remote_path',
                           metavar="PATH", help="remote path")

    args_opts = arg_parser.add_argument_group(title="operation options")

    args_opts.add_argument('--ssh-opts', action='extend', nargs='*', default=[], dest='ssh_opts',
                           metavar="OPTIONS", help="ssh options")
    args_opts.add_argument('--sshfs-opts', action='extend', nargs='*', default=[], dest='sshfs_opts',
                           metavar="OPTIONS", help="sshfs options")
    args_opts.add_argument('--rsync-opts', action='extend', nargs='*', default=[], dest='rsync_opts',
                           metavar="OPTIONS", help="rsync options")

    return arg_parser.parse_args()


def pass_value_exists(key: str) -> bool:
    """Check pass value for existence.
    """
    return subprocess.run(['pass', key], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def pass_value(key: str) -> str:
    """Get value from pass store.
    """
    proc = subprocess.run(['pass', key], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return (proc.stdout.rstrip(), proc.returncode == 0)

def host_pass_key(host: str, subkey: str = '') -> str:
    """Get pass key prefix for specified host.
    """
    return f"computers/{host}/net/{subkey}"

def is_host_known(host: str) -> bool:
    """Check if host is in pass store.
    """
    return pass_value_exists(host_pass_key(host))

def get_host_ip_address(host: str, lan: bool) -> str:
    """Get host IP address.
    """
    prefix = 'local' if lan else 'global'
    value, exists = pass_value(host_pass_key(host, prefix + '/ip-address'))
    return value if exists else None

def get_host_ssh_port(host: str, lan: bool) -> int:
    """Get host ssh port.
    """
    prefix = 'local' if lan else 'global'
    value, exists = pass_value(host_pass_key(host, prefix + '/port-ssh'))
    return int(value) if exists else None

def get_host_mac_address(host: str) -> str:
    """Get host MAC address.
    """
    value, exists = pass_value(host_pass_key(host, 'mac-address'))
    return value if exists else None

def get_host_wakeup_port(host: str, lan: bool) -> int:
    """Get host wakeup port.
    """
    prefix = 'local' if lan else 'global'
    value, exists = pass_value(host_pass_key(host, prefix + '/port-wakeup'))
    return int(value) if exists else None

def get_host_wakeup_delay(host: str) -> int:
    """Get host wakeup delay.
    """
    value, exists = pass_value(host_pass_key(host, 'wakeup-delay'))
    return int(value) if exists else None

def generate_host_url(user: str, address: str, port: int, prefix: bool=False) -> str:
    """Generate host URL.
    """
    ssh_prefix = 'ssh://' if prefix else ''
    user_prefix = f'{user}@' if user is not None else ''
    port_postfix = f':{port}' if port is not None else ''
    return f'{ssh_prefix}{user_prefix}{address}{port_postfix}'

def execute_command(command: list[str], dry_run: bool=False) -> int:
    """Execute generic command.
    """
    if dry_run:
        print(" ".join(command))
    else:
        eprint("$ " + " ".join(command))
        eprint()

    return subprocess.run(command).returncode if not dry_run else 0

def check_host_status(address: str, port: int, dry_run: bool=False) -> int:
    """Check whether host is online and port is open.
    """
    command = ['nc', '-w', str(STATUS_TIMEOUT), '-z', address, str(port)]

    return execute_command(command, dry_run)

def wakeup_host(mac_address: str, port: int, address: str=None, dry_run: bool=False) -> int:
    """Send magic packet to host.
    """
    command = ['wol', '-p', str(port)]
    if address is not None:
        command += ['-i', address]
    command.append(mac_address)

    return execute_command(command, dry_run)

def ssh_session(address: str, user: str=None, port: int=None, opts: list=[],
                cmd: list=[], dry_run: bool=False) -> int:
    """Establish ssh session.
    """
    if 'TERM' not in os.environ:
        os.environ['TERM'] = DEFAULT_SSH_TERM

    command = ['ssh', *opts]
    if port is not None:
        command += ['-p', str(port)]
    command += [generate_host_url(user, address, None), *cmd]

    return execute_command(command, dry_run)

def sshfs_mount(address: str, user: str=None, port: int=None, local_path: str=None,
                remote_path: str=None, opts: list=[], dry_run: bool=False) -> int:
    """Mount remote directory locally.
    """
    if local_path is None:
        local_path = DEFAULT_LOCAL_PATH

    target = generate_host_url(user, address, None) + ':'
    if remote_path is not None:
        target += remote_path

    command = ['sshfs', target, local_path, *opts]

    return execute_command(command, dry_run)

def rsync_copy(address: str, user: str=None, port: int=None, ssh_opts: list=[],
               upload: bool=False, local_path: str=None, remote_path: str=None,
               opts: list=[], dry_run: bool=False) -> int:
    """Download/upload files from/to remote host.
    """
    ssh_subcommand = 'ssh '
    if port is not None:
        ssh_subcommand += f'-p {port} '
    ssh_subcommand += ' '.join(ssh_opts)

    if local_path is None:
        local_path = DEFAULT_LOCAL_PATH

    if remote_path is None:
        remote_path = DEFAULT_REMOTE_PATH
    remote_path = generate_host_url(user, address, None) + ':' + remote_path

    command = ['rsync', '-vP', *opts, '-e', ssh_subcommand]
    command += [local_path, remote_path] if upload else [remote_path, local_path]

    return execute_command(command, dry_run)


if __name__ == "__main__":
    try:
        args = parse_args()

        if not args.wakeup and args.operation is None:
            sys.exit(0)

        if args.host is not None and not is_host_known(args.host):
            eprint("Error: unknown host")
            sys.exit(1)

        if args.address is None:
            if args.host is not None:
                args.address = get_host_ip_address(args.host, args.lan)

            if args.address is None:
                eprint("Error: no address known for host")
                sys.exit(1)

        if args.port is None:
            if args.host is not None:
                args.port = get_host_ssh_port(args.host, args.lan)

        if args.operation == OP_URL:
            print(generate_host_url(args.user, args.address, args.port, prefix=True))
            sys.exit(0)

        if args.wakeup:
            code = check_host_status(args.address, args.port, args.dry_run)

            if not args.dry_run:
                if code == 0:
                    eprint("Host is online, wakeup is cancelled")
                    args.wakeup = False
                else:
                    eprint("Host is offline")

                eprint()

        if args.wakeup:
            if args.wakeup_mac is None:
                if args.host is not None:
                    args.wakeup_mac = get_host_mac_address(args.host)

                if args.wakeup_mac is None:
                    eprint("Error: no MAC address known for host")
                    sys.exit(1)

            if args.wakeup_port is None:
                if args.host is not None:
                    args.wakeup_port = get_host_wakeup_port(args.host, args.lan)

                if args.wakeup_port is None:
                    args.wakeup_port = DEFAULT_WAKEUP_PORT

            if args.wakeup_delay is None:
                if args.host is not None:
                    args.wakeup_delay = get_host_wakeup_delay(args.host)

                if args.wakeup_delay is None:
                    args.wakeup_delay = DEFAULT_WAKEUP_DELAY

            code = wakeup_host(args.wakeup_mac, args.wakeup_port, address=args.address, dry_run=args.dry_run)
            if not args.dry_run:
                eprint(f"  finished with code {code}")

                if args.operation is None:
                    sys.exit(code)

                eprint()
                eprint(f"Waiting {args.wakeup_delay} seconds for host to wake up...")
                time.sleep(args.wakeup_delay)
                eprint("Remote host must be awake now.")
                eprint()

        if args.operation is None:
            sys.exit(0)
        elif args.operation == OP_STATUS:
            code = check_host_status(args.address, args.port, dry_run=args.dry_run)
            if not args.dry_run:
                eprint(f"Host is {'online' if code == 0 else 'offline'}")
            sys.exit(code)
        elif args.operation == OP_SSH:
            sys.exit(ssh_session(args.address, user=args.user, port=args.port, opts=args.ssh_opts,
                                cmd=args.ssh_command, dry_run=args.dry_run))
        elif args.operation == OP_TUNNEL:
            if args.ssh_tunnel_arg is None:
                args.ssh_tunnel_arg = DEFAULT_TUNNEL_ARG
            tunnel_opts = args.ssh_opts + ['-ND', args.ssh_tunnel_arg]
            sys.exit(ssh_session(args.address, user=args.user, port=args.port, opts=tunnel_opts,
                                dry_run=args.dry_run))
        elif args.operation == OP_RTUNNEL:
            if args.ssh_tunnel_arg is None:
                args.ssh_tunnel_arg = DEFAULT_RTUNNEL_ARG
            tunnel_opts = args.ssh_opts + ['-NR', args.ssh_tunnel_arg]
            sys.exit(ssh_session(args.address, user=args.user, port=args.port, opts=tunnel_opts,
                                dry_run=args.dry_run))
        elif args.operation == OP_SSHFS:
            sys.exit(sshfs_mount(args.address, user=args.user, port=args.port,
                                 local_path=args.local_path, remote_path=args.remote_path, opts=args.sshfs_opts,
                                 dry_run=args.dry_run))
        elif args.operation == OP_DOWNLOAD:
            sys.exit(rsync_copy(args.address, user=args.user, port=args.port, ssh_opts=args.ssh_opts,
                                upload=False, local_path=args.local_path, remote_path=args.remote_path,
                                opts=args.rsync_opts, dry_run=args.dry_run))
        elif args.operation == OP_UPLOAD:
            sys.exit(rsync_copy(args.address, user=args.user, port=args.port, ssh_opts=args.ssh_opts,
                                upload=True, local_path=args.local_path, remote_path=args.remote_path,
                                opts=args.rsync_opts, dry_run=args.dry_run))
        else:
            eprint("Error: unknown operation")
            sys.exit(1)
    except KeyboardInterrupt:
        eprint()
        eprint("Operation is interrupted by user")

