# -*- coding: utf-8 -*-

from invoke import task


@task
def run(c):
    """Run local version of the application"""
    c.run("flask run")


@task
def deploy(c):
    """Deploy the application to Heroku"""
    c.run("git push --force-with-lease heroku HEAD:master")


@task
def test(c):
    """Run tests like we would on the CI server"""
    c.run("pytest --color=yes")
