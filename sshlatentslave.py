# -*- python -*-
# ex: set syntax=python:
# vim: set expandtab ts=4 sw=4 softtabstop=4:

from twisted.internet import defer, threads
from twisted.python import log

from buildbot.buildslave.base import AbstractLatentBuildSlave
from buildbot import interfaces

from paramiko import SSHClient, PKey

import os
import os.path

class SSHLatentBuildSlave(AbstractLatentBuildSlave):
    """
    Build slave that runs a command over SSH to start and stop the build slave.
    """

    def __init__(self, name, password, hostname, username, command, **kwargs):
        """
        Creates a new SSH latent build slave with the given parameters.
        """
        AbstractLatentBuildSlave.__init__(self, name, password, **kwargs)
        self.client = SSHClient()
        self.client.load_system_host_keys()

        self.hostname = hostname
        self.username = username
        self.command = command
        self.started = False

    def _connect(self):
        if not self._is_connected():
            log.msg("connecting to SSH server")
            self.client.connect(self.hostname, username=self.username, key_filename=self.key_path)

    def _is_connected(self):
        self.client.get_transport() != None and self.client.get_transport().is_active()

    def start_instance(self, build):
        if self.started:
            raise ValueError('already started')
        return threads.deferToThread(self._start_instance)

    def _start_instance(self):
        self._connect()
        cmd = self.command.format(name=self.slavename, host=self.hostname, cmd='start')
        log.msg("executing start command: " + cmd)
        stdin, stdout, stderr = self.client.exec_command(cmd)
        self.started = True
        return True


    def stop_instance(self, fast=False):
        if not self.started:
            return defer.succeed(None)
        return threads.deferToThread(self._stop_instance)

    def _stop_instance(self):
        self._connect()
        cmd = self.command.format(name=self.slavename, host=self.hostname, cmd='stop')
        log.msg("stopping build slave: " + cmd)
        self.client.exec_command(cmd)
        log.msg("closing connection")
        self.client.close()
        log.msg("finished")
        self.started = False
