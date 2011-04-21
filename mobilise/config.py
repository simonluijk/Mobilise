#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os

from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError


class ConfigError(Exception):
    pass


class Config(object):
    def __init__(self, project_path=None):
        self.conf = None

        if not project_path:
            project_path = os.getcwd()
            while True:
                if os.path.exists(os.path.join(project_path, "project.conf")):
                    break
                if project_path == "/":
                    break
                project_path = os.path.dirname(project_path)
        self.project_path = project_path

        config_path = os.path.join(self.project_path, "project.conf")
        if os.path.exists(config_path):
            self.conf = SafeConfigParser()
            self.conf.read(config_path)

    @property
    def project_name(self):
        try:
            return self.conf.get("core", "project_name")
        except (NoSectionError, NoOptionError):
            raise ConfigError("project_name must be set in project.conf!")

    @property
    def requirements(self):
        try:
            return self.conf.get("core", "requirements")
        except (NoSectionError, NoOptionError):
            return u"requirements.txt"

    @property
    def pybundle(self):
        try:
            return self.conf.get("core", "pybundle")
        except (NoSectionError, NoOptionError):
            return u"%s.pybundle" % os.path.splitext(self.requirements)[0]

    @property
    def conf_dir(self):
        try:
            return self.conf.get("core", "conf_dir")
        except (NoSectionError, NoOptionError):
            return u"conf.d"

    @property
    def pid_dir(self):
        try:
            return self.conf.get("core", "pid_dir")
        except (NoSectionError, NoOptionError):
            return u"/var/run/django"

    @property
    def virtual_env(self):
        try:
            workon_home = os.environ["WORKON_HOME"]
        except KeyError:
            workon_home = os.path.expanduser(u"~/.virtualenvs")
        return os.path.join(workon_home, self.project_name)

    @property
    def remote_path(self):
        try:
            return self.conf.get("remote", "path")
        except (NoSectionError, NoOptionError):
            raise ConfigError("remote path not set")

    @property
    def remote_hosts(self):
        try:
            return self.conf.get("remote", "hosts")
        except (NoSectionError, NoOptionError):
            raise ConfigError("remote hosts not set")
