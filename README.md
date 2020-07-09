# remote-control

remote-control is a helper script allowing easy manipulation of remote computers running Linux.

## Installation

1. Install [Roswell](https://github.com/roswell/roswell) to your system.

If you use Arch-based Linux distro, there is a package available in AUR: [roswell](https://aur.archlinux.org/packages/roswell/).

2. Install *remote-control*:

```sh
$ ros install ivanp7/remote-control
```

## Usage

Run program with

```sh
$ ros exec remote OPTIONS
```

If you add `$HOME/.roswell/bin` to your `$PATH`, 
you won't need to call Roswell explicitly:

```sh
$ remote OPTIONS
```

For usage help, run

```sh
$ ros exec remote --help
```

```
remote computer handling utility
(C) Ivan Podmazov, 2020

Usage: remote [--help] [-n|--dry-run] [-u|--user USERNAME]
              [-h|--host HOSTNAME] [-L|--lan] [-a|--address ADDRESS] [-p|--port PORT]
              [-m|--mac MAC-ADDR] [-P|--wakeup-port PORT] [-d|--delay DELAY] [-w|--wakeup]
              [-o|--op OPERATION] [-c|--cmd ARG] [-t|--tunnel ARGUMENT] [-l|--path PATH]
              [-r|--rpath PATH] [--ssh-opts OPTIONS] [--sshfs-opts OPTIONS]
              [--rsync-opts OPTIONS] [--args ARGUMENTS]

Available options:
  --help                   show usage help
  -n, --dry-run            don't do anything, only print commands to be executed
  -u, --user USERNAME      remote user name
  -h, --host HOSTNAME      registered name of known remote host
  -L, --lan                access remote host using local address and port
  -a, --address ADDRESS    address of remote host
  -p, --port PORT          port of remote host
  -m, --mac MAC-ADDR       MAC address to wake up
  -P, --wakeup-port PORT   port to send magic packet to
  -d, --delay DELAY        time for remote host to wake up
  -w, --wakeup             wake up remote computer before operation
  -o, --op OPERATION       operation type
  -c, --cmd ARG            ssh command
  -t, --tunnel ARGUMENT    ssh tunnel argument (port and/or binding address)
  -l, --path PATH          local path
  -r, --rpath PATH         remote path
  --ssh-opts OPTIONS       ssh options
  --sshfs-opts OPTIONS     sshfs options
  --rsync-opts OPTIONS     rsync options
  --args ARGUMENTS         ssh command arguments

--ssh-opts, --sshfs-opts, --rsync-opts, --args act as a option lists delimiters:
options after them are passed into a corresponding program instead of remote-control

Supported operations:
  url print-url
  status check-status
  ssh cmd command
  tnl tunnel ssh-tunnel
  rntl rtunnel reverse-ssh-tunnel
  mnt mount sshfs
  up upload
  down download
  remotely run-remotely
```

## Advanced usage

remote-control can use `pass` password manager to obtain IP address, SSH port,
Wake-on-Lan port, MAC address and wakeup delay from the store 
using `--host` parameter only. Refer to the "Customizable parameters" section
in the source code for details and customization.

## Author

Ivan Podmazov (ivanpzv8@gmail.com)

## [License](LICENSE)

