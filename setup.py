from setuptools import setup

import pkgtools


long_desc = '''pkgtools is a Python library that offers some tools to work with Python Packages. It includes two packages:

    * `pkgtools.pypi`: a simple yet powerful interface to `PyPI <http://pypi.python.org/pypi>`_ (Python Package Index)
    * `pkgtools.pkg`: some package utilities, like metadata reading


Hello World!
------------

::

    >>> from pkgtools.pypi import PyPI
    >>> pypi = PyPI()
    >>> pypi.package_releases('pypol_')
    ['0.5']
    >>> pypi.package_releases('pypol_', True)
    ['0.5', '0.4', '0.3', '0.2']
    >>> pypol_egg = pypi.release_urls('pypol_', '0.5')[2]
    >>> pypol_egg
    Object({'has_sig': False, 'upload_time': <DateTime '20110213T09:33:07' at 97d666c>, 'comment_text': '',
    'python_version': '2.6', 'url': 'http://pypi.python.org/packages/2.6/p/pypol_/pypol_-0.5-py2.6.egg',
    'md5_digest': '20e660cef8513f35fdb0afd5390146bc', 'downloads': 46, 'filename': 'pypol_-0.5-py2.6.egg',
    'packagetype': 'bdist_egg', 'size': 116826})
    >>> pypol_egg['python_version']
    '2.6'
    >>> pypol_egg.python_version
    '2.6'
    >>> pypol_egg.filename
    'pypol_-0.5-py2.6.egg'
    >>> pypol_egg.url
    'http://pypi.python.org/packages/2.6/p/pypol_/pypol_-0.5-py2.6.egg'

::

    >>> from pkgtools.pkg import Installed
    >>> i = Installed('sphinx')
    >>> i
    <pkgtools.pkg.Installed object at 0x96f68ec>
    >>> i.file('entry_points.txt')
    {'console_scripts': {'sphinx-autogen': 'sphinx.ext.autosummary.generate:main',
                         'sphinx-build': 'sphinx:main',
                         'sphinx-quickstart': 'sphinx.quickstart:main'},
     'distutils.commands': {'build_sphinx': 'sphinx.setup_command:BuildDoc'}}
    >>> i.file('requires.txt')
    ['Pygments>=0.8', 'Jinja2>=2.2', 'docutils>=0.5']
    >>> i.file('depencency_links.txt')
    Traceback (most recent call last):
      File "<pyshell#8>", line 1, in <module>
        i.file('depencency_links.txt')
      File "pkg.py", line 80, in file
        raise KeyError('This package does not have {0} file'.format(name))
    KeyError: This package does not have depencency_links.txt file
    >>> i.file('PKG-INFO')['Metadata-Version']
    '1.0'
    >>> i.file('PKG-INFO')['Name']
    'Sphinx'
'''

setup(
    name='pkgtools',
    version=pkgtools.__version__,
    author='Michele Lacchia',
    author_email='<michelelacchia@gmail.com',
    license='MIT',
    url='http://',
    download_url='http://pypi.python.org/pypi/pkgtools',
    description='Python Packages Tools',
    long_description=long_desc,
    platforms='any',
    packages=['pkgtools'],
    keywords=['python', 'packages', 'pypi', 'setuptools', 'distutils']
)