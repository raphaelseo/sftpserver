###############################################################################
#
# Copyright (c) 2011-2017 Ruslan Spivak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

import time
import socket
import argparse
import sys
import os
import textwrap

import paramiko

from thinknum_sftpserver.stub_sftp import (
    NewSFTPServer,
    StubServer, 
    StubSFTPServer
)


HOST, PORT = 'localhost', 22
BACKLOG = 10


def start_server(host, port, keyfile, level, basedir):
    print (host, port, keyfile, level)
    paramiko_level = getattr(paramiko.common, level)
    paramiko.common.logging.basicConfig(level=paramiko_level)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server_socket.bind((host, port))
    server_socket.listen(BACKLOG)

    while True:
        conn, addr = server_socket.accept()

        host_key = paramiko.RSAKey.from_private_key_file(keyfile)
        transport = paramiko.Transport(conn)
        transport.add_server_key(host_key)
        StubSFTPServer.ROOT = basedir
        transport.set_subsystem_handler(
            'sftp', 
            # paramiko.SFTPServer,
            NewSFTPServer,
            StubSFTPServer
        )

        server = StubServer()
        server.ROOT = basedir
        transport.start_server(server=server)

        channel = transport.accept()
        while transport.is_active():
            time.sleep(1)


def main():
    usage = """\
    usage: sftpserver [options]
    -k/--keyfile should be specified
    """
    parser = argparse.ArgumentParser(usage=textwrap.dedent(usage))
    parser.add_argument(
        '--host', dest='host', default=HOST,
        help='listen on HOST [default: %(default)s]'
    )
    parser.add_argument(
        '-p', '--port', dest='port', type=int, default=PORT,
        help='listen on PORT [default: %(default)d]'
    )
    parser.add_argument(
        '-l', '--level', dest='level', default='INFO',
        help='Debug level: WARNING, INFO, DEBUG [default: %(default)s]'
    )
    parser.add_argument(
        '-k', '--keyfile', dest='keyfile', metavar='FILE',
        help='Path to private key, for example /tmp/test_rsa.key'
    )
    parser.add_argument(
        '-b',  '--basedir', dest='basedir',
        help='Base directory path'
    )

    args = parser.parse_args()

    if args.keyfile is None:
        parser.print_help()
        sys.exit(-1)

    if args.basedir is None or not os.path.isdir(args.basedir):
        parser.print_help()
        sys.exit(-1)

    start_server(args.host, args.port, args.keyfile, args.level, args.basedir)


if __name__ == '__main__':
    # readme.io file should be in root folder
    main()



'''
ssh-keygen -t rsa -b 4096

sudo python sftp_server.py --basedir /Users/sangwonseo/historical --keyfile /Users/sangwonseo/dev_projects/sftpserver/id_rsa

openssl req -out CSR.csr -new -newkey rsa:2048 -nodes -keyout /Users/sangwonseo/dev_projects/sftpserver/test_rsa.key

python sftp_server.py --keyfile /Users/sangwonseo/dev_projects/sftpserver/test_rsa.key

python sftp_server.py --keyfile /Users/sangwonseo/dev_projects/sftpserver/id_rsa --basedir /Users/sangwonseo/dev_projects/sftpserver/history/
'''