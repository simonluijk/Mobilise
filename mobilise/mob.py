#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys

from optparse import OptionParser
from fabric.network import normalize as _normalize
from fabric.utils import indent

from mobilise.commands import build_pybundle, build_venv, deploy, reset_database
from mobilise.config import Config


def _interpret_host_string(host_string):
    """
    Apply given host string to the env dict.

    Split it into hostname, username and port (using
    `~fabric.network.normalize`) and store the full host string plus its
    constituent parts into the appropriate env vars.

    Returns the parts as split out by ``normalize`` for convenience.
    """
    from fabric.state import env
    username, hostname, port = _normalize(host_string)
    env.host_string = host_string
    env.host = hostname
    env.user = username
    env.port = port
    return username, hostname, port


__USAGE__ = """%prog [OPTIONS] [command]"""


def main():
    """
    Entry point for mob, a dumb fab replacement
    """

    _commands = {
        'build_pybundle': build_pybundle,
        'build_venv': build_venv,
        'deploy': deploy,
        'reset_database': reset_database,
    }

    parser = OptionParser(usage=__USAGE__)
    parser.add_option('-l', '--list', action='store_true', dest='list_commands',
        help='list avaliable commands')
    
    (options, args) = parser.parse_args()
    st = Config()    

    # Print list (Taken from fabric)
    if options.list_commands:
        print("Available commands:\n")
        # Want separator between name, description to be straight col
        max_len = reduce(lambda a, b: max(a, len(b)), _commands.keys(), 0)
        sep = ' '
        trail = '...'
        for name in sorted(_commands.keys()):
            output = None
            # Print first line of docstring
            func = _commands[name]
            if func.__doc__:
                lines = filter(None, func.__doc__.splitlines())
                first_line = lines[0].strip()
                # Truncate it if it's longer than N chars
                size = 75 - (max_len + len(sep) + len(trail))
                if len(first_line) > size:
                    first_line = first_line[:size] + trail
                output = name.ljust(max_len) + sep + first_line
            # Or nothing (so just the name)
            else:
                output = name
            print(indent(output))
        sys.exit(0)

    # Make sure a command is supplied
    try:
        args[0]
    except IndexError:
        sys.stderr.write('You must specify an command!\n')
        sys.exit(1)

    # Make sure all commands are valied
    try:
        commands = [[i, _commands[i]] for i in args]
    except KeyError, e:
        sys.stderr.write('Command %s not found!\n' % e)
        sys.exit(1)
  
    for command_name, command in commands:
        for host in st.conf.get('remote', 'hosts').split(','):
            print("[%s] Executing task '%s'" % (host, command_name))
            username, hostname, port = _interpret_host_string(host)
            command()

if __name__ == "__main__":
    main()
