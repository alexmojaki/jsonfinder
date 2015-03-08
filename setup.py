from setuptools import setup

description = """\
Easily handle JSON contained within strings
Includes a command-line tool to format JSON within the input, similar to the builtin json.tool."""

setup(name='jsonfinder',
      version='0.2',
      description=description,
      author='Alex Hall',
      author_email='alex.mojaki@gmail.com',
      license='MIT',
      packages=['jsonfinder'],
      zip_safe=False)