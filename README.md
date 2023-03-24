# remote.py

`remote.py` is a Python reimplementation of `remote-control`,
a Common Lisp helper script allowing easy manipulation of remote computers running Linux.

## Usage
```
usage: remote.py [--help] [-n] [-L] [-h HOST] [-s ADDR] [-p PORT] [-u USER] [-w] [-m MAC] [-P PORT]
                 [-d SECONDS] [-o OP_TYPE] [--cmd CMD [CMD ...]] [-t TUNNEL_ARG] [-l PATH] [-r PATH]
                 [--ssh-opts [OPTIONS ...]] [--sshfs-opts [OPTIONS ...]]
                 [--rsync-opts [OPTIONS ...]]

Remote host control

options:
  --help                              show this help message and exit
  -n, --dry-run                       don't do anything, only print commands to be executed

host registry:
  -L, --lan                           access remote host using local address and port
  -h HOST, --host HOST                registered name of known remote host

address:
  -s ADDR, --addr ADDR                address (IP or domain name) of remote host
  -p PORT, --port PORT                port of remote host
  -u USER, --user USER                remote user name

wakeup:
  -w, --wakeup                        wake up remote host
  -m MAC, --wakeup-mac MAC            MAC address to wake up
  -P PORT, --wakeup-port PORT         port to send magic packet to
  -d SECONDS, --wakeup-delay SECONDS  time for remote host to wake up

operation:
  -o OP_TYPE, --op OP_TYPE            operation type (url, stat, ssh, tunnel, rtunnel, mount,
                                      download, upload)
  --cmd CMD [CMD ...]                 ssh command to execute remotely
  -t TUNNEL_ARG, --tunnel TUNNEL_ARG  ssh tunnel argument (port and/or binding address)

operation paths:
  -l PATH, --lpath PATH               local path
  -r PATH, --rpath PATH               remote path

operation options:
  --ssh-opts [OPTIONS ...]            ssh options
  --sshfs-opts [OPTIONS ...]          sshfs options
  --rsync-opts [OPTIONS ...]          rsync options
```

## Advanced usage

`remote.py` can use `pass` password manager to obtain IP address, SSH port,
Wake-on-Lan port, MAC address and wakeup delay from the store
using `--host` parameter only. Refer to the source code for the details.

## Author

Ivan Podmazov (ivanpzv8@gmail.com)

## [License](LICENSE)

