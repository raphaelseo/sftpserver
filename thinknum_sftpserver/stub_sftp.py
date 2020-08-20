# Copyright (C) 2003-2009  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
A stub SFTP server for loopback SFTP testing.
"""

import os
import re
from paramiko import (
    ServerInterface, 
    SFTPServerInterface, 
    SFTPServer, 
    SFTPAttributes,
    SFTPHandle, 
    SFTP_OK, 
    AUTH_SUCCESSFUL, 
    AUTH_FAILED, 
    OPEN_SUCCEEDED
)
import smart_open
from thinknum import History
import shutil
from paramiko.sftp import (
    CMD_NAMES,
    CMD_OPEN,
    CMD_WRITE,
    CMD_REMOVE,
    CMD_RENAME,
    CMD_MKDIR,
    CMD_RMDIR,
    CMD_READDIR,
    CMD_SYMLINK,
    CMD_EXTENDED,
    SFTP_FAILURE
)
from paramiko.common import DEBUG


CLIENT_ID = 'CLIENT_ID'
CLIENT_SECRET = 'CLIENT_SECRET'

class NewSFTPServer(SFTPServer):

    def _process(self, t, request_number, msg):
        print ("NewSFTPServer", CMD_NAMES[t], request_number)
        if t in (
            CMD_WRITE, CMD_REMOVE, CMD_RENAME, CMD_MKDIR, CMD_RMDIR,
            # CMD_READDIR, CMD_SYMLINK, CMD_EXTENDED
        ):
            print ("1")
            raise Exception("Invalid permission")
            # self._send_status(
            #     request_number, SFTP_PERMISSION_DENIED, "Invalid permission"
        #     # )
        # elif t in (CMD_READ,):
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print ("CMD_READ")
        #     print (msg.get_text())
        #     super(NewSFTPServer, self)._process(t, request_number, msg)
        else:
            # if t == CMD_OPEN:
            super(NewSFTPServer, self)._process(t, request_number, msg)


class StubServer(ServerInterface):

    ROOT = os.getcwd()

    def check_auth_password(self, username, password):
        print ("check_auth_password", username, password)
        print ("ROOT", self.ROOT)
        try:
            self.thinknum_history = History(
                client_id=username,
                client_secret=password
            )
            # TODO Delete all sub directories
            print ("Delete all subdirectories")
            print (self.ROOT)
            for subdirectory in os.listdir(self.ROOT):
                subpath = os.path.join(self.ROOT, subdirectory)
                print (subpath)
                if os.path.exists(subpath):
                    shutil.rmtree(subpath)

            # TODO folder create?
            dataset_list = self.thinknum_history.get_dataset_list()
            for item in dataset_list:
                dataset_id = item.get('id')
                print (dataset_id)
                dataset_id_path = os.path.join(self.ROOT, dataset_id)
                if not os.path.exists(dataset_id_path):
                    os.mkdir(dataset_id_path)

                # for filename in self.thinknum_history.get_history_list(dataset_id):
                #     filepath = os.path.join(dataset_id_path, "{dataset_id}_{filename}.csv.gz".format(dataset_id=dataset_id, filename=filename))
                #     if not os.path.exists(filepath):
                #         with open(filepath, 'a'):
                #             pass

            return AUTH_SUCCESSFUL
        except Exception:
            return AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print ("check_auth_publickey", username, key)
        # all are allowed
        return AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        print ("check_channel_request", kind, chanid)
        return OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        print ("get_allowed_auths", username)
        """List availble auth mechanisms."""
        return "password"


class StubSFTPHandle(SFTPHandle):
    def stat(self):
        # TODO 4. folder change
        print ("stat", self.readfile.fileno())
        try:
            return SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def chattr(self, attr):
        print ("chattr", attr)
        # python doesn't have equivalents to fchown or fchmod, so we have to
        # use the stored filename
        try:
            SFTPServer.set_file_attr(self.filename, attr)
            return SFTP_OK
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def close(self):
        print ("close")
        # print (self.__flags)
        # print (self.__name)
        # print (self.__files)
        # print (self.__tell)
        print ("self.filename", self.filename, type(self.filename))
        print ("self.readfile.fileno()", self.readfile)
        readfile = getattr(self, "readfile", None)
        print ("readfile", readfile)
        if readfile is not None:
            readfile.close()
        writefile = getattr(self, "writefile", None)
        if writefile is not None:
            writefile.close()
        print ("writefile", writefile)
        print ("self.filename", self.filename, type(self.filename))
        # print (os.path.exists(self.filename))
        if os.path.exists(self.filename):
            os.remove(self.filename)
            # print ('delete', self.filename)
            with open(self.filename, 'a'):
                pass
            # print ('create', self.filename)


class StubSFTPServer(SFTPServerInterface):
    # assume current folder is a fine root
    # (the tests always create and eventualy delete a subfolder, so there shouldn't be any mess)
    
    # TODO 1. Root Change
    ROOT = os.getcwd()
        
    def _realpath(self, path):
        print ("_realpath", self.ROOT + self.canonicalize(path))
        return self.ROOT + self.canonicalize(path)

    def session_started(self):
        """
        The SFTP server session has just started.  This method is meant to be
        overridden to perform any necessary setup before handling callbacks
        from SFTP operations.
        """
        print ("session_started")
        pass

    def session_ended(self):
        """
        The SFTP server session has just ended, either cleanly or via an
        exception.  This method is meant to be overridden to perform any
        necessary cleanup before this `.SFTPServerInterface` object is
        destroyed.
        """
        # TODO 2 folder delete
        print ("session_ended")
        print ("Delete all subdirectories")
        print (self.ROOT)
        for subdirectory in os.listdir(self.ROOT):
            subpath = os.path.join(self.ROOT, subdirectory)
            print (subpath)
            if os.path.exists(subpath):
                shutil.rmtree(subpath)

    def list_folder(self, path):
        # TODO 3. list
        print ("list_folder", path)
        print ("ROOT", self.ROOT)
        path = self._realpath(path)
        try:
            # if path is direcotry:
            # if re.match(
            #     '^{root}/*$'.format(root=self.ROOT),
            #     path
            # ):
            #     print ("1")
            #     out = [ ]
            #     for dataset_id in ['store', 'job_listings', 'social_facebook']:
            #         attr = SFTPAttributes.from_stat(os.stat(path))
            #         attr.filename = dataset_id
            #         out.append(attr)
            # el
            if re.match(
                '^{root}/[a-z_]+/*$'.format(root=self.ROOT),
                path
            ):
                print ("2")
                # TODO fake csv create
                dataset_id  = path.split('/')[-1]
                thinknum_history = History(
                    client_id='CLIENT_ID',
                    client_secret='CLIENT_SECRET'
                )
                for filename in thinknum_history.get_history_list(dataset_id):
                    print ("filename", filename)
                    filepath = os.path.join(path, "{dataset_id}_{filename}.csv.gz".format(dataset_id=dataset_id, filename=filename))
                    if not os.path.exists(filepath):
                        with open(filepath, 'a'):
                            pass
                # out = [ ]
                # for filename in ['2020-01-01.csv', '2020-01-02.csv', '2020-01-07.csv']:
                #     attr = SFTPAttributes.from_stat(os.stat(os.path.join(self.ROOT, 'readme.io')))
                #     attr.filename = filename
                #     out.append(attr)

            out = [ ]
            flist = os.listdir(path)
            for fname in flist:
                print ("fname", fname, type(fname))
                attr = SFTPAttributes.from_stat(os.stat(os.path.join(path, fname)))
                attr.filename = fname
                print ("attr", attr, type(attr))
                out.append(attr)
            return out
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def stat(self, path):
        print ("stat", path)
        path = self._realpath(path)
        if re.match(
            '^{root}/[a-z_]+/*$'.format(root=self.ROOT),
            path
        ):
            print ("2")
            # TODO fake csv create
            dataset_id  = path.split('/')[-1]
            thinknum_history = History(
                client_id='CLIENT_ID',
                client_secret='CLIENT_SECRET'
            )
            for filename in thinknum_history.get_history_list(dataset_id):
                print ("filename", filename)
                filepath = os.path.join(path, "{dataset_id}_{filename}.csv.gz".format(dataset_id=dataset_id, filename=filename))
                if not os.path.exists(filepath):
                    with open(filepath, 'a'):
                        pass
        # print ("_realpath", path)
        # if re.match(
        #     '^{root}/[a-z_]+/*$'.format(root=self.ROOT),
        #     path
        # ):
        #     path = self.ROOT
        #     # TODO folder create

        # elif re.match(
        #     '^{root}/[a-z_]+/[0-9-]+.csv$'.format(root=self.ROOT),
        #     path
        # ):
        #     # TODO folder csv file create
        #     path = os.path.join(self.ROOT, 'readme.io')
        # print ("_realpath", path)
        # print ("os.stat(path)", os.stat(path))
        try:
            return SFTPAttributes.from_stat(os.stat(path))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def lstat(self, path):
        print ("lstat", path)
        path = self._realpath(path)
        try:
            return SFTPAttributes.from_stat(os.lstat(path))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def open(self, path, flags, attr):
        # TODO 2 download
        print ("open")
        print (path, type(path))
        print (flags, type(flags))
        print (attr, type(attr))
        path = self._realpath(path)
        print ("path", path)

        # print ("open", path, flags, attr)
        dataset_id = path.split('/')[-2]
        print ("dataset_id", dataset_id)
        history_date = path.split('/')[-1].split('.')[0].split('_')[-1]
        print ("history_date", history_date)
        # download
        thinknum_history = History(
            client_id='CLIENT_ID',
            client_secret='CLIENT_SECRET'
        )
        print ("thinknum_history")
        print (dataset_id, history_date, '/'.join(path.split('/')[:-1]) + '/')
        thinknum_history.download(
            dataset_id=dataset_id,
            history_date=history_date,
            download_path='/'.join(path.split('/')[:-1]) + '/',
            is_compressed=True
        )
        print ("download")

        try:
            binary_flag = getattr(os, 'O_BINARY',  0)
            flags |= binary_flag
            mode = getattr(attr, 'st_mode', None)
            if mode is not None:
                fd = os.open(path, flags, mode)
            else:
                # os.open() defaults to 0777 which is
                # an odd default mode for files
                fd = os.open(path, flags, 0o666)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            SFTPServer.set_file_attr(path, attr)
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                fstr = 'ab'
            else:
                fstr = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                fstr = 'a+b'
            else:
                fstr = 'r+b'
        else:
            # O_RDONLY (== 0)
            fstr = 'rb'
        try:
            f = os.fdopen(fd, fstr)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        fobj = StubSFTPHandle(flags)
        fobj.filename = path
        fobj.readfile = f
        fobj.writefile = f
        return fobj

    def remove(self, path):
        print ("remove", path)
        path = self._realpath(path)
        try:
            os.remove(path)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def rename(self, oldpath, newpath):
        print ("rename", oldpath, newpath)
        oldpath = self._realpath(oldpath)
        newpath = self._realpath(newpath)
        try:
            os.rename(oldpath, newpath)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def mkdir(self, path, attr):
        print ("mkdir", path, attr)
        path = self._realpath(path)
        try:
            os.mkdir(path)
            if attr is not None:
                SFTPServer.set_file_attr(path, attr)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def rmdir(self, path):
        print ("rmdir", path)
        path = self._realpath(path)
        try:
            os.rmdir(path)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def chattr(self, path, attr):
        print ("chattr", path, attr)
        path = self._realpath(path)
        try:
            SFTPServer.set_file_attr(path, attr)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def symlink(self, target_path, path):
        print ("symlink", target_path, path)
        path = self._realpath(path)
        if (len(target_path) > 0) and (target_path[0] == '/'):
            # absolute symlink
            target_path = os.path.join(self.ROOT, target_path[1:])
            if target_path[:2] == '//':
                # bug in os.path.join
                target_path = target_path[1:]
        else:
            # compute relative to path
            abspath = os.path.join(os.path.dirname(path), target_path)
            if abspath[:len(self.ROOT)] != self.ROOT:
                # this symlink isn't going to work anyway -- just break it immediately
                target_path = '<error>'
        try:
            os.symlink(target_path, path)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def readlink(self, path):
        print ("readlink", path)
        path = self._realpath(path)
        try:
            symlink = os.readlink(path)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)
        # if it's absolute, remove the root
        if os.path.isabs(symlink):
            if symlink[:len(self.ROOT)] == self.ROOT:
                symlink = symlink[len(self.ROOT):]
                if (len(symlink) == 0) or (symlink[0] != '/'):
                    symlink = '/' + symlink
            else:
                symlink = '<error>'
        return symlink
