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
def freeze(c):
    """Freeze pip's requirements.txt. Does not commit the file."""
    import pip

    result = c.run("pip freeze")
    with open("requirements.txt", mode="w") as requirements:
        requirements.write(result.stdout)
