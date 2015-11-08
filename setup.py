#!/usr/bin/env python

# Copyright 2012-2015 Tinyarray authors.
#
# This file is part of Tinyarray.  It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution and at
# http://git.kwant-project.org/tinyarray/about/LICENSE.  A list of Tinyarray
# authors can be found in the README file at the top-level directory of this
# distribution and at http://git.kwant-project.org/tinyarray/about/.

import subprocess
import os
import sys
from setuptools import setup, Extension, Command
from sysconfig import get_platform
from distutils.errors import DistutilsError, DistutilsModuleError
from setuptools.command.build_ext import build_ext
from setuptools.command.sdist import sdist

README_FILE = 'README'
SAVED_VERSION_FILE = 'version'
VERSION_HEADER = ['src', 'version.hh']

CLASSIFIERS = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Programming Language :: Python :: 2
Programming Language :: Python :: 3
Programming Language :: C++
Topic :: Software Development
Topic :: Scientific/Engineering
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
Operating System :: Microsoft :: Windows"""

distr_root = os.path.dirname(os.path.abspath(__file__))

def get_version_from_git():
    try:
        p = subprocess.Popen(['git', 'rev-parse', '--show-toplevel'],
                             cwd=distr_root,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return
    if p.wait() != 0:
        return
    if not os.path.samefile(p.communicate()[0].decode().rstrip('\n'), distr_root):
        # The top-level directory of the current Git repository is not the same
        # as the root directory of the source distribution: do not extract the
        # version from Git.
        return

    # git describe --first-parent does not take into account tags from branches
    # that were merged-in.
    for opts in [['--first-parent'], []]:
        try:
            p = subprocess.Popen(['git', 'describe', '--long'] + opts,
                                 cwd=distr_root,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            return
        if p.wait() == 0:
            break
    else:
        return
    description = p.communicate()[0].decode().strip('v').rstrip('\n')

    release, dev, git = description.rsplit('-', 2)
    version = [release]
    labels = []
    if dev != "0":
        version.append(".dev{}".format(dev))
        labels.append(git)

    try:
        p = subprocess.Popen(['git', 'diff', '--quiet'], cwd=distr_root)
    except OSError:
        labels.append('confused') # This should never happen.
    else:
        if p.wait() == 1:
            labels.append('dirty')

    if labels:
        version.append('+')
        version.append(".".join(labels))

    return "".join(version)


with open(os.path.join(SAVED_VERSION_FILE), 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        else:
            version = line
            break
    else:
        raise RuntimeError("Saved version file does not contain version.")
version_is_from_git = (version == "__use_git__")
if version_is_from_git:
    version = get_version_from_git()
    if not version:
        version = "unknown"


def long_description():
    text = []
    skip = True
    try:
        with open(README_FILE) as f:
            for line in f:
                if line == "\n":
                    if skip:
                        skip = False
                        continue
                    elif text[-1] == '\n':
                        text.pop()
                        break
                if not skip:
                    text.append(line)
    except:
        return ''
    text[-1] = text[-1].rstrip()
    return ''.join(text)


class our_build_ext(build_ext):
    def run(self):
        with open(os.path.join(*VERSION_HEADER), 'w') as f:
            f.write("// This file has been generated by setup.py.\n")
            f.write("// It is not included in source distributions.\n")
            f.write('#define VERSION "{}"\n'.format(version))
        build_ext.run(self)


class our_sdist(sdist):
    def make_release_tree(self, base_dir, files):
        sdist.make_release_tree(self, base_dir, files)

        fname = os.path.join(base_dir, SAVED_VERSION_FILE)
        # This could be a hard link, so try to delete it first.  Is there any way
        # to do this atomically together with opening?
        try:
            os.remove(fname)
        except OSError:
            pass
        with open(fname, 'w') as f:
            f.write("# This file has been generated by setup.py.\n{}\n"
                    .format(version))


module = Extension('tinyarray',
                   language='c++',
                   sources=['src/arithmetic.cc', 'src/array.cc',
                            'src/functions.cc'],
                   depends=['src/arithmetic.hh', 'src/array.hh',
                            'src/conversion.hh', 'src/functions.hh'])


def main():
    setup(name='tinyarray',
          version=version,
          author='Christoph Groth (CEA) and others',
          author_email='christoph.groth@cea.fr',
          description="Arrays of numbers for Python, optimized for small sizes",
          long_description=long_description(),
          url="http://git.kwant-project.org/tinyarray/about/",
          download_url="http://downloads.kwant-project.org/tinyarray/",
          license="Simplified BSD license",
          platforms=["Unix", "Linux", "Mac OS-X", "Windows"],
          classifiers=CLASSIFIERS.split('\n'),
          cmdclass={'build_ext': our_build_ext,
                    'sdist': our_sdist},
          ext_modules=[module],
          test_suite = 'nose.collector',
          setup_requires=['nose >= 1.0'])


if __name__ == '__main__':
    main()
