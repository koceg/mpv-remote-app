#!/usr/bin/python3

import os
import psutil
import logging
import argparse
import subprocess
from media_server import MediaServer
from media_controllers import MpvController
from os.path import abspath, realpath, isdir

# Usage message
help_string = (
    "Listens on PORT for UDP commands to send to mpv."
    " PASSWORD sets the password of this server and must be used"
    " by the client to alter the state of mpv."
    " Note: mpv must be started with the --input-ipc-server flag."
)

def parse_args():
    parser = argparse.ArgumentParser(
            description=help_string,
            usage="%(prog)s [OPTIONS] password")
    parser.add_argument("-p", "--port", metavar="PORT_NUMBER", type=int,
                        default=28899,
                        help="Port number on which to listen (default: 28899)")
    parser.add_argument("-s", "--mpv-socket", metavar="SOCK", type=str,
                        default=None,
                        help="Unix socket that mpv is listening on (default: auto detect)")
    parser.add_argument("-r", "--root", metavar="ROOT_DIR", type=str,
                        default=os.environ.get('HOME', None),
                        help="Root directory for file browsing (default: $HOME)")
    parser.add_argument("--hidden", action='store_true',
                        help="Send hidden filenames (default: false)")
    parser.add_argument("-f", "--filetypes", metavar="FILETYPES", type=str,
                        default="",
                        help="Only send filetypes "
                              "in the comma separated list FILETYPES. "
                              "Blank means no filter.")
    parser.add_argument("password", help="The password for this server")
    return parser.parse_args()

def set_root(args):
    args.root = abspath(realpath((args.root)))
    if not isdir(args.root):
        print("%s is not a directory or does not exist." % root)
        args.root = os.environ.get('HOME', None)
        if args.root is None:
            print("Cannot find a suitable root directory")
            exit(1)
        print("Using default root directory: %s" % args.root)
    args.filetypes = [x for x in args.filetypes.split(',') if len(x) > 0]

def set_mpv_socket(args):
    # returns whether an mpv instance was found or not
    for pid in psutil.pids():
        try:
            p = psutil.Process(pid)
            cmdline = p.cmdline()
            if p.name() == "mpv" and "--input-ipc-server" in cmdline:
                ipc_server = cmdline[cmdline.index("--input-ipc-server") + 1]
                if args.mpv_socket is None:
                    args.mpv_socket = ipc_server
                    return True
                elif args.mpv_socket == ipc_server:
                    return True
        except: pass
    return False

def spawn_mpv(unix_socket):
    print("No running mpv instance found. Starting mpv...")
    subprocess.Popen(["mpv", "--no-terminal",
        "--input-ipc-server", unix_socket, "--idle"])

def main():
    args = parse_args()

    set_root(args)
    # set mpv_socket to currently running instance
    # or spawn if not running
    if not set_mpv_socket(args):
        if args.mpv_socket is None:
            args.mpv_socket = "/tmp/mpvsocket"
        spawn_mpv(args.mpv_socket)

    ms = MediaServer(args.port, args.password, root=args.root,
            no_hidden=not args.hidden, filetypes=args.filetypes,
            controller=MpvController(args.mpv_socket))
    ms.run()

if __name__ == "__main__": main()
