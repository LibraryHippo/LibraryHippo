# -*- coding: utf-8 -*-

from invoke import task


@task
def run(c):
    """Run local version of the application"""
    c.run("flask run")


@task
def deploy(c):
    """Deploy the application to Heroku"""
    c.run("git push heroku lh2020:master")
