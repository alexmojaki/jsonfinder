from setuptools import setup

description = """\
Easily handle JSON contained within strings.
Includes a command-line tool to format JSON within the input, similar to the builtin json.tool."""


def readme():
    with open('README.rst') as readme_file:
        return readme_file.read()


setup(name='jsonfinder',
      version='0.3.0',
      description=description,
      long_description=readme(),
      classifiers=[
          "Programming Language :: Python :: 2 :: Only",
          "Topic :: Utilities"
      ],
      url="https://github.com/alexmojaki/jsonfinder",
      author='Alex Hall',
      author_email='alex.mojaki@gmail.com',
      license='MIT',
      packages=['jsonfinder'],
      include_package_data=True,
      entry_points={'console_scripts': ['jsonfinder=jsonfinder.__main__:main']})