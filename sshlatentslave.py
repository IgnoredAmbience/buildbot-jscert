# -*- python -*-
# ex: set syntax=python:
# vim: set expandtab ts=4 sw=4 softtabstop=4:

from twisted.internet import defer, threads
from twisted.python import log

from buildbot.buildslave.base import AbstractLatentBuildSlave

from paramiko import SSHClient


class SSHLatentBuildSlave(AbstractLatentBuildSlave):

    """
    Build slave that runs a command over SSH to start and stop the build slave.
    """

    def __init__(self, name, password, hostname, username,
                 command, key_path=None, **kwargs):
        """
        Creates a new SSH latent build slave with the given parameters.
        """
        AbstractLatentBuildSlave.__init__(self, name, password, **kwargs)
        self.client = SSHClient()
        self.client.load_system_host_keys()

        self.hostname = hostname
        self.username = username
        self.command = command
        self.key_path = key_path

        self.started = False

    def _connect(self):
        if not self._is_connected():
            log.msg("connecting to SSH server")
            self.client.connect(self.hostname, username=self.username,
                                key_filename=self.key_path)

    def _is_connected(self):
        return self.client.get_transport() is not None \
            and self.client.get_transport().is_active()

    def _exec_command(self, action):
        """Executes a given command, returns True if stderr is empty."""
        self._connect()

        cmd = self.command.format(name=self.slavename, host=self.hostname,
                                  action=action)
        log.msg("executing command: " + cmd)
        stdin, stdout, stderr = self.client.exec_command(cmd)

        for line in stdout:
            log.msg("ssh stdout on ", self.hostname, ": ", line)
        for line in stderr:
            failed = True
            log.msg("ssh stderr on ", self.hostname, ": ", line)

        return not failed

    def start_instance(self, build):
        if self.started:
            raise ValueError('already started')
        return threads.deferToThread(self._start_instance)

    def _start_instance(self):
        self.started = self._exec_command('start')
        return self.started

    def stop_instance(self, fast=False):
        if not self.started:
            return defer.succeed(None)
        return threads.deferToThread(self._stop_instance)

    def _stop_instance(self):
        self._exec_command('stop')
        self.client.close()
        log.msg("finished")
        self.started = False
