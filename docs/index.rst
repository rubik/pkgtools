.. pkgtools documentation master file, created by
   sphinx-quickstart on Tue Apr  5 17:18:14 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pkgtools's documentation!
====================================

pkgtools is a Python library that offers some tools to work with Python Packages. It includes two modules:

    * :mod:`pkgtools.pypi`: a simple yet powerful interface to `PyPI <http://pypi.python.org/pypi>`_ (Python Package Index)
    * :mod:`pkgtools.pkg`: some package utilities, like metadata reading


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
    {'has_sig': False, 'upload_time': <DateTime '20110213T09:33:07' at 97d666c>, 'comment_text': '',
    'python_version': '2.6', 'url': 'http://pypi.python.org/packages/2.6/p/pypol_/pypol_-0.5-py2.6.egg',
    'md5_digest': '20e660cef8513f35fdb0afd5390146bc', 'downloads': 46, 'filename': 'pypol_-0.5-py2.6.egg',
    'packagetype': 'bdist_egg', 'size': 116826}
    >>> pypol_egg['python_version']
    '2.6'
    >>> pypol_egg.python_version
    '2.6'
    >>> pypol_egg.filename
    'pypol_-0.5-py2.6.egg'
    >>> pypol_egg.url
    'http://pypi.python.org/packages/2.6/p/pypol_/pypol_-0.5-py2.6.egg'
    >>> pypi = PyPIJson('pyg')
    >>> pypi.retrieve()['info']['author']
    'Michele Lacchia'
    >>> list(pypi.find())
    [('0.4',
      'pyg-0.4-py2.7.egg',
      'f8c23fe4dbb64df4235bf14fe1646c92',
      'http://pypi.python.org/packages/2.7/p/pyg/pyg-0.4-py2.7.egg'),
     ('0.4',
      'pyg-0.4.tar.gz',
      '6860ac99bf45508acdf1c751d7ce2633',
      'http://pypi.python.org/packages/source/p/pyg/pyg-0.4.tar.gz')]
    >>> pypi = PyPIJson('pyg', '0.3.2')
    >>> list(pypi.find())
    [('0.3.2',
      'pyg-0.3.2-py2.6.egg',
      'd933b3ddc6913d5b149c7c751e836bfc',
      'http://pypi.python.org/packages/2.6/p/pyg/pyg-0.3.2-py2.6.egg'),
     ('0.3.2',
      'pyg-0.3.2.tar.gz',
      '9ce6efcf44548add6fa5540c529d33ee',
      'http://pypi.python.org/packages/source/p/pyg/pyg-0.3.2.tar.gz')]

::

    >>> from pkgtools.pkg import Installed
    >>> i = Installed('sphinx')
    >>> i
    <Installed[/usr/local/lib/python2.7/dist-packages/Sphinx-1.0.7.egg-info] object at 176896748>
    >>> i.file('entry_points.txt')
    {'console_scripts': {'sphinx-build': 'sphinx:main', 'sphinx-quickstart': 'sphinx.quickstart:main',
    'sphinx-autogen': 'sphinx.ext.autosummary.generate:main'},
    'distutils.commands': {'build_sphinx': 'sphinx.setup_command:BuildDoc'}
    }
    >>> i.entry_points_map('console_scripts')
    {'sphinx-build': 'sphinx:main', 'sphinx-quickstart': 'sphinx.quickstart:main',
    'sphinx-autogen': 'sphinx.ext.autosummary.generate:main'}
    >>> i.file('requires.txt')
    ['Pygments>=0.8', 'Jinja2>=2.2', 'docutils>=0.5']
    >>> i.file('dependency_links.txt')
    Traceback (most recent call last):
      File "<pyshell#8>", line 1, in <module>
        i.file('dependency_links.txt')
      File "/usr/local/lib/python2.7/dist-packages/pkgtools-0.3.1-py2.7.egg/pkgtools/pkg.py", line 140, in file
        raise KeyError('This package does not have {0} file'.format(name))
    KeyError: 'This package does not have dependency_links.txt file'
    >>> i.pkg_info['Metadata-Version'] # Same as i.file('PKG-INFO')['Metadata-Version']
    '1.0'
    >>> i.pkg_info['Name']
    'Sphinx'
    >>> i.name
    'Sphinx'
    >>> i.as_req()
    'Sphinx==1.0.7'
    >>> i = Installed(__import__('sphinx'))
    >>> i
    <Installed[/usr/local/lib/python2.7/dist-packages/Sphinx-1.0.7.egg-info] object at 177199596>
    >>> i.files()
    ['requires.txt', 'PKG-INFO', 'SOURCES.txt', 'top_level.txt', 'entry_points.txt', 'zip-safe']