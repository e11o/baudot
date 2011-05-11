from paver.easy import *
import paver.doctools
from paver.setuputils import setup

setup(
    name="Baudot",
    packages=['baudot'],
    version="0.1",
    url="http://www.baudot.org/",
    author="Esteban Sancho",
    author_email="esteban.sancho@gmail.com"
)

@task
@needs('setuptools.command.sdist')
def sdist():
    """Main build"""
    pass
