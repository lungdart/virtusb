""" Setup script """
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0326

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine
import io
import os
import sys
from shutil import rmtree
from setuptools import find_packages, setup, Command

# Package meta-data.
NAME            = 'virtusb'
DESCRIPTION     = 'Virtual USB devices using USBIP'
URL             = 'https://github.com/lungdart/virtusb'
EMAIL           = 'dev@lungdart.net'
AUTHOR          = 'lungdart'
REQUIRES_PYTHON = '>=2.7.0'
VERSION         = '0.1'
LICENSE         = 'MIT'
REQUIRED        = ['future', 'six', 'packeteer']
EXTRAS          = {}
CLASSIFIERS     = [
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Software Development :: Testing',
    'Topic :: System :: Emulators',
    'Intended Audience :: Developers',
]


def working_directory():
    """ Get the working directory """
    path = os.path.abspath(os.path.dirname(__file__))
    return path

def get_long_description(readme='README.md'):
    """ Generates a long description from README.md """
    working_dir = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(working_dir, readme)
    try:
        with io.open(readme_path, encoding='utf8') as readme_file:
            result = '\n' + readme_file.read()
    except Exception: #pylint: disable=broad-except
        result = DESCRIPTION
    return result

class UploadCommand(Command):
    """Support setup.py upload."""
    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(message):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(message))

    def initialize_options(self):
        """ Not used """

    def finalize_options(self):
        """ Not used """

    def run(self):
        """ Clean, build, tag, push, and upload """
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(working_directory(), 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine...')
        os.system('twine upload dist/*')

        self.status('Pushing git tags...')
        os.system('git tag v{0}'.format(VERSION))
        os.system('git push --tags')

        sys.exit()


# Where the magic happens:
setup(
    name                          = NAME,
    version                       = VERSION,
    description                   = DESCRIPTION,
    long_description              = get_long_description(),
    long_description_content_type = 'text/markdown',
    author                        = AUTHOR,
    author_email                  = EMAIL,
    python_requires               = REQUIRES_PYTHON,
    url                           = URL,
    packages                      = find_packages(exclude=('tests',)),
    install_requires              = REQUIRED,
    extras_require                = EXTRAS,
    include_package_data          = True,
    license                       = LICENSE,
    classifiers                   = CLASSIFIERS,
    cmdclass                      = {'upload': UploadCommand}
)
