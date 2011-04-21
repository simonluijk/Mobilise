#!/usr/bin/env python
#-*- coding:utf-8 -*-
from __future__ import with_statement

import os
import sys
import time
import subprocess

from os import path
from signal import SIGTERM, SIGHUP
from optparse import OptionParser
from ConfigParser import NoSectionError, NoOptionError

from mobilise.config import Config, ConfigError


__USAGE__ = """%prog [OPTIONS] deamon action"""


class BaseDaemon(object):
    """
    Base deamon to be inherated from
    """

    def __init__(self, conf):
        self.conf = conf
        self.pid_file = path.join(self.conf.pid_dir, "%s-%s.pid" % (
            self.conf.project_name, self.name.lower()
        ))
        self._setup_environ()
            
    def _print(self, message):
        """
        Print message
        """

        print(message % self.name)
 
    def _pid(self):
        """
        Get pid from file
        """

        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except IOError:
            pass

    def _setup_environ(self):
        """
        Setup the project environment
        """

        os.environ["VIRTUAL_ENV"] = self.conf.virtual_env
        os.environ["PATH"] = "%s/bin:%s" % (os.environ["VIRTUAL_ENV"], os.environ["PATH"])
        os.chdir(self.conf.project_path)

    def start(self):
        """
        Start deamon
        """

        if self._pid():
            self._print("%s already running!")
            sys.exit(1)

        self._start()
        self._print("%s started!")

    def _start(self):
        """
        Start hock
        """

        raise NotImplementedError

    def stop(self):
        """
        Stop deamon
        """
 
        if not self._pid():
            self._print("%s not running!")
            sys.exit(1)
 
        self._stop()
        self._print("%s stopped!")

    def _stop(self):
        """
        Stop hock
        """

        try:
            pid = self._pid()
            while True:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process"):
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
            else:
                self._print("'%%s' %s!" % err)
                sys.exit(1)

    def reload(self):
        """
        Reload deamon
        """

        if self._pid():
            self._reload()
            self._print("%s reloaded!")
        else:
            self._start()
            self._print("%s started!")

    def _reload(self):
        """
        Reload hock. Default to restarting deamon
        """

        self._stop()
        self._start()

    def restart(self):
        """
        Stop and restart deamon
        """

        if self._pid():
            self._stop()
            self._start()
            self._print("%s restarted!")
        else:
            self._start()
            self._print("%s started!")


class GunicornDeamon(BaseDaemon):
    """
    Gunicorn deamon class
    """

    name = "Gunicorn"

    def _reload(self):
        """
        Reload Gunicorn
        """

        try:
            os.kill(self._pid(), SIGHUP)
        except OSError, err:
            self._print("'%%s' %s!" % err)
            sys.exit(1)

    def _start(self):
        """
        Start Gunicorn
        """

        executable = path.join(self.conf.virtual_env, "bin", "python")
        command = [executable, "manage.py", "run_gunicorn", "--pid", self.pid_file]

        try:
            for option in self.conf.conf.get("gunicorn", "options").split(" "):
                command.append(option)
        except (NoSectionError, NoOptionError):
            pass

        subprocess.Popen(command)


class CeleryDeamon(BaseDaemon):
    """
    Celery deamon class
    """

    name = "Celery"

    def _start(self):
        """
        Start Celery
        """

        executable = path.join(self.conf.virtual_env, "bin", "python")
        command = [executable, "manage.py",  "celeryd", "--pidfile", self.pid_file]

        try:
            for option in self.conf.conf.get("celery", "options").split(" "):
                command.append(option)
        except (NoSectionError, NoOptionError):
            pass

        subprocess.Popen(command)


_actions = ["start", "stop", "restart", "reload"]
_daemons = {
    "gunicorn": GunicornDeamon,
    "celery": CeleryDeamon,
}


def main():
    parser = OptionParser(usage=__USAGE__, version="%prog 1.0")
    parser.add_option("-p", "--project", action="store", dest="project",
        help="path to project directory [PWD]")    
    (options, args) = parser.parse_args()

    try:
        conf = Config(options.project)
    except (ConfigError), err:
        parser.error(err)
  
    try:
        deamon = args[0]
        deamon = _daemons[deamon](conf)
    except IndexError:
        parser.error("You must specify a deamon to run!")
    except KeyError:
        parser.error("Deamon '%s' not recognised!" % deamon)

    try:
        action = args[1]
    except IndexError:
        parser.error("You must specify an action!")
    if action not in _actions:
        parser.error("Action '%s' not recognised!" % action)

    getattr(deamon, action)()


if __name__ == "__main__":
    main()
