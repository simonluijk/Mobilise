#!/usr/bin/env python
#-*- coding:utf-8 -*-
from __future__ import with_statement

import os

from fabric.api import run, sudo, local, cd, lcd, prefix, runs_once
from fabric.contrib import files, project

from mobilise.config import Config


@runs_once
def build_pybundle(post_setup=None):
    """
    Bundle requirements into a pybundle
    """

    st = Config()
    local('pip -qE "$WORKON_HOME/%s" bundle "%s" -r "%s"' % (
        st.project_name, st.pybundle, st.requirements))

    if post_setup:
        post_setup(st)


@runs_once
def build_venv(post_setup=None):
    """
    Build local vitualenv from pybundle
    """

    st = Config()
    local('rm -rf "$WORKON_HOME/%s"' % st.project_name)
    local('virtualenv "$WORKON_HOME/%s"' % st.project_name)
    local('pip -qE "$WORKON_HOME/%s" install "%s"' % (st.project_name, st.pybundle))

    if post_setup:
        post_setup(st)


def reset_database(post_reset=None):
    """
    Reset the local database
    """

    st = Config()
    with lcd(st.project_path):
        with prefix('. "$WORKON_HOME/%s/bin/activate"' % st.project_name):
            local('rm -f dev.db')
            local('python manage.py syncdb --noinput')
            local('python manage.py migrate')

    if post_reset:
        post_reset(st)


_configs = {
    'nginx.conf': [
        '/etc/nginx/sites-enabled/',
        'service nginx reload'
    ],
    'monit.conf': [
        '/etc/monit/conf.d/',
        'monit reload'
    ],
}

def deploy(test=None, post_setup=None):
    """
    Deploy project to remote host
    """

    st = Config()

    if test:
        try:
            test(st)
        except:
            print('Local tests failed. Aborting deploy')
            raise

    project.rsync_project(
        remote_dir=os.path.dirname(st.remote_path),
        local_dir=st.project_path,
        exclude=[
            '*settings\_local\.py',
            'fabfile\.py',
            '*celerybeat\-schedule',
            '\.git*', '*\.db','*\.pyc'],
        delete=True
    )

    with cd(st.remote_path):
        run('rm -rf "$WORKON_HOME/%s"' % st.project_name)
        run('virtualenv "$WORKON_HOME/%s"' % st.project_name)
        run('pip -qE "$WORKON_HOME/%s" install "%s"' % (st.project_name, st.pybundle))

        for config in _configs.keys():
            dest_dir, command = _configs[config]
            source_path = os.path.join(st.conf_dir, config)
            if files.exists(source_path):
                dest_path = os.path.join(dest_dir, '%s.conf' % st.project_name)
                if not files.exists(dest_path):
                    source_path = os.path.join(st.remote_path, source_path)
                    sudo('ln -sf %s %s' % (source_path, dest_path))
                if command:
                    sudo(command)

        if post_setup:
            post_setup(st)

        with prefix('. "$WORKON_HOME/%s/bin/activate"' % st.project_name):
            run('echo "from settings_production import *" > settings_local.py')
            try:
                run('python manage.py syncdb --noinput')
            except:
                pass
            try:
                run('python manage.py migrate')
            except:
                pass

        if st.conf.has_section('gunicorn'):
            run('dj-daemon gunicorn reload')

        if st.conf.has_section('celery'):
            run('dj-daemon celery reload')
