# -*- coding: utf-8 -*-

from invoke import task


@task
def run(c):
    """Run local version of the application"""
    c.run("flask run")
