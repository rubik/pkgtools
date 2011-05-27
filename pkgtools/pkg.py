import os
import sys
import glob
import pkgutil
import tarfile
import zipfile
import warnings

if sys.version_info >= (3,):
    import io as StringIO
    import configparser as ConfigParser
else:
    import StringIO
    import ConfigParser

from email.parser import FeedParser
from .utils import ext, tar_files, zip_files


class MetadataFileParser(object):

    def __init__(self, data, name):

        self.MAP = {
            'PKG-INFO': self.pkg_info,
            'SOURCES.txt': self.list,
            'top_level.txt': self.list,
            'requires.txt': self.list,
            'dependency_links.txt': self.list,
            'installed-files.txt': self.list,
            'entry_points.txt': self.config,
        }
        self.data = data
        self.name = name
        if not self.name:
            raise TypeError('Invalid file name: {0}'.format(self.name))

    def parse(self):
        try:
            return self.MAP[self.name]()
        except (KeyError, ConfigParser.MissingSectionHeaderError):
            return {}

    def pkg_info(self):
        d = {}
        f = FeedParser()
        f.feed(self.data)
        d.update(list(f.close().items()))
        return d

    def list(self):
        d = []
        for line in self.data.split('\n'):
            line = line.strip()
            if not line or (line.startswith('[') and line.endswith(']')):
                continue
            d.append(line)
        return d

    def config(self):
        d = {}
        p = ConfigParser.ConfigParser()
        p.readfp(StringIO.StringIO(self.data))
        for s in p.sections():
            d[s] = dict(p.items(s))
        return d


class Dist(object):
    '''
    This is the base class for all other objects. It requires a list of tuples (``(file_data, file_name)``) and provides some methods:

    .. attribute:: has_metadata

        This attribute is True when the distribution has some metadata, False otherwise.

    .. attribute:: pkg_info

        Returns PKG-INFO's data. Equivalent to ``Dist.file('PKG-INFO')``.

    .. attribute:: name

        The package's name.

    .. attribute:: version

        The package's current version.

    .. automethod:: file

    .. automethod:: files

    .. automethod:: entry_points_map

    .. automethod:: as_req
    '''

    ## Used by __repr__ method
    _arg_name = None
    _zip_safe = True

    def __init__(self, file_objects):
        self.metadata = {}
        self.file_objects = file_objects
        self._get_metadata()

    def __repr__(self):
        ## A little trick to get the real name from sub-classes (like Egg or SDist)
        return '<{0}[{1}] object at {2}>'.format(self.__class__.__name__, self._arg_name, id(self))

    def _get_metadata(self):
        for data, name in self.file_objects:
            if name == 'not-zip-safe':
                self._zip_safe = False
            elif name.endswith('.txt') or name == 'PKG-INFO':
                metadata = MetadataFileParser(data, name).parse()
                if not metadata:
                    continue
                self.metadata[name] = metadata
        ## FIXME: Do we really need _Objectify??
        #self.metadata = _Objectify(self.metadata)
        return self.metadata

    @ property
    def has_metadata(self):
        return bool(self.metadata)

    @ property
    def pkg_info(self):
        return self.file('PKG-INFO')

    @ property
    def name(self):
        return self.pkg_info['Name']

    @ property
    def version(self):
        return self.pkg_info['Version']

    @ property
    def as_req(self):
        '''
        Returns a string that represents the parsed requirement.
        '''

        return '{0}=={1}'.format(self.name, self.version)

    @ property
    def zip_safe(self):
        '''
        Returns False whether the package has a :file:`not-zip-safe` file, True otherwise.
        '''

        return self._zip_safe

    def file(self, name):
        '''
        Returns the content of the specified file. Raises :exc:`KeyError` when the distribution does not have such file.
        '''

        if name not in self.metadata:
            raise KeyError('This package does not have {0} file'.format(name))
        return self.metadata[name]

    def files(self):
        '''
        Returns the files parsed by this distribution.
        '''

        return list(self.metadata.keys())

    def entry_points_map(self, group):
        '''
        Returns the elements under the specified section in the :file:`entry_points.txt` file.
        '''

        try:
            return self.file('entry_points.txt')[group]
        except KeyError:
            return {}


class Egg(Dist):
    '''
    Given the egg path, returns a Dist object::

        >>> e = Egg('pyg-0.4-py2.7.egg')
        >>> e
        <Egg[pyg-0.4-py2.7.egg] object at 157366028>
        >>> e.files()
        ['top_level.txt', 'requires.txt', 'PKG-INFO', 'entry_points.txt', 'SOURCES.txt']
        >>> e.file('requires.txt')
        ['setuptools', 'pkgtools>=0.3.1', 'argh>=0.14']
        >>> e.pkg_info['Name']
        'pyg'
        >>> e.name
        'pyg'
        >>> e.version
        '0.4'
        >>> e.as_req
        'pyg==0.4'
        >>> e.entry_points_map('console_scripts')
        {'pyg': 'pyg:main'}
        >>> e.file('entry_points.txt')
        {'console_scripts': {'pyg': 'pyg:main'}}
    '''

    def __init__(self, egg_path):
        z = zipfile.ZipFile(egg_path)
        self._arg_name = os.path.normpath(egg_path)
        super(Egg, self).__init__(zip_files(z, 'EGG-INFO'))


class SDist(Dist):
    '''
    Given the source distribution path, returns a Dist object::

        >>> s = SDist('pyg-0.4.tar.gz')
        >>> s
        <SDist[pyg-0.4.tar.gz] object at 157425036>
        >>> s.files()
        ['top_level.txt', 'requires.txt', 'PKG-INFO', 'entry_points.txt', 'SOURCES.txt']
        >>> s.pkg_info['Metadata-Version']
        '1.1'
        >>> s.as_req()
        'pyg==0.4'
    '''

    def __init__(self, sdist_path):
        e = ext(sdist_path)
        if e == '.zip':
            arch = zipfile.ZipFile(sdist_path)
            func = zip_files
        elif e.startswith('.tar'):
            mode = 'r' if e == '.tar' else 'r:' + e.split('.')[2]
            arch = tarfile.open(sdist_path, mode=mode)
            func = tar_files
        self._arg_name = os.path.normpath(sdist_path)
        super(SDist, self).__init__(func(arch))


class Dir(Dist):
    '''
    Given a path containing the metadata files, returns a Dist object::

        >>> d = Dir('/usr/local/lib/python2.7/dist-packages/pypol_-0.5.egg-info')
        >>> d
        <Dir[/usr/local/lib/python2.7/dist-packages/pypol_-0.5.egg-info] object at 157419436>
        >>> d.as_req()
        'pypol-==0.5'
        >>> d.pkg_info
        {'Name': 'pypol-', 'License': 'GNU GPL v3',
        'Author': 'Michele Lacchia', 'Metadata-Version': '1.0',
        'Home-page': 'http://pypol.altervista.org/',
        'Summary': 'Python polynomial library', 'Platform': 'any',
        'Version': '0.5', 'Download-URL': 'http://github.com/rubik/pypol/downloads/',
        'Classifier': 'Programming Language :: Python :: 2.7',
        'Author-email': 'michelelacchia@gmail.com', 'Description': 'UNKNOWN'
        }
    '''

    def __init__(self, path):
        files = []
        if not os.path.exists(os.path.join(path, 'PKG-INFO')):
            raise ValueError('This directory does not contain metadata files')
        for f in os.listdir(path):
            if not os.path.isfile(os.path.join(path, f)):
                continue
            with open(os.path.join(path, f)) as fobj:
                data = fobj.read()
            files.append((data, f))
        self._arg_name = os.path.normpath(path)
        super(Dir, self).__init__(files)


class EggDir(Dir):
    '''
    Given a directory path which contains an EGG-INFO dir, returns a Dist object::

        >>> ed = EggDir('/usr/local/lib/python2.7/dist-packages/pkgtools-0.3.1-py2.7.egg')
        >>> ed
        <EggDir[/usr/local/lib/python2.7/dist-packages/pkgtools-0.3.1-py2.7.egg/EGG-INFO] object at 145505740>
        >>> ed.files()
        ['top_level.txt', 'PKG-INFO', 'SOURCES.txt']
        >>> ed.pkg_info['Summary']
        'Python Packages Tools'
        >>> ed.as_req()
        'pkgtools==0.3.1'
        >>> ed.file('entry_points.txt')
        Traceback (most recent call last):
          File "<pyshell#7>", line 1, in <module>
            ed.file('entry_points.txt')
          File "/usr/local/lib/python2.7/dist-packages/pkgtools-0.3.1-py2.7.egg/pkgtools/pkg.py", line 140, in file
            raise KeyError('This package does not have {0} file'.format(name))
        KeyError: 'This package does not have entry_points.txt file'
        >>> ed.zip_safe
        False
    '''

    def __init__(self, path):
        path = os.path.join(path, 'EGG-INFO')
        if not os.path.exists(path):
            raise ValueError('Path does not exist: {0}'.format(path))
        super(EggDir, self).__init__(path)


class Develop(Dir):
    '''
    This class accepts either a string or a module object. Returns a Dist object::

        >>> d = Develop('pkgtools')
        >>> d
        <Develop[pkgtools] object at 158833324>
        >>> d.files()
        ['top_level.txt', 'dependency_links.txt', 'PKG-INFO', 'SOURCES.txt']
        >>> d.file('SOURCES.txt')
        ['AUTHORS', 'CHANGES', 'LICENSE', 'MANIFEST.in', 'README', 'TODO', 'setup.py',
        'docs/Makefile', 'docs/conf.py', 'docs/index.rst', 'docs/make.bat', 'docs/pkg.rst',
        'docs/pypi.rst', 'docs/_themes/pyg/theme.conf', 'docs/_themes/pyg/static/pyg.css_t',
        'pkgtools/__init__.py', 'pkgtools/__init__.pyc', 'pkgtools/pkg.py', 'pkgtools/pkg.pyc',
        'pkgtools/pypi.py', 'pkgtools/pypi.pyc', 'pkgtools/utils.py', 'pkgtools/utils.pyc',
        'pkgtools.egg-info/PKG-INFO', 'pkgtools.egg-info/SOURCES.txt',
        'pkgtools.egg-info/dependency_links.txt', 'pkgtools.egg-info/top_level.txt']
        >>> import pyg
        >>> d = Develop(pyg)
        >>> d
        <Develop[/home/3jkldfi84r2hj/pyg/pyg.egg-info] object at 175354540>
        >>> d.files()
        ['requires.txt', 'PKG-INFO', 'SOURCES.txt', 'top_level.txt', 'dependency_links.txt', 'entry_points.txt']
    '''

    def __init__(self, package):
        if isinstance(package, str):
            try:
                package = __import__(package)
            except ImportError:
                raise ValueError('cannot import {0}'.format(package))
        package_name = package.__package__
        if package_name is None:
            package_name = package.__name__
        d = os.path.dirname(package.__file__)
        egg_info = package_name + '.egg-info'
        paths = [os.path.join(d, egg_info), os.path.join(d, '..', egg_info)]
        for p in paths:
            if os.path.exists(p):
                path = p
                break
        else:
            raise ValueError('cannot find metadata for {0}'.format(package_name))
        self._arg_name = package_name
        super(Develop, self).__init__(path)


class Installed(Dir):
    '''
    This class accepts either a string or a module object and returns a Dist object::

        >>> i = Installed('argh')
        >>> i
        <Installed[argh] object at 158358348>
        >>> i.files()
        ['top_level.txt', 'dependency_links.txt', 'PKG-INFO', 'SOURCES.txt']
        >>> i.file('top_level.txt')
        ['argh']
        >>> import argh
        >>> i = Installed(argh)
        >>> i
        <Installed[/usr/local/lib/python2.7/dist-packages/argh-0.14.0-py2.7.egg-info] object at 175527500>
        >>> i.files()
        ['top_level.txt', 'dependency_links.txt', 'PKG-INFO', 'SOURCES.txt']
    '''

    def __init__(self, package):
        if isinstance(package, str):
            try:
                package = __import__(package)
            except (ImportError, SystemExit):
                try:
                    package = __import__(package.lower())
                except (ImportError, SystemExit):
                    raise ValueError('cannot import {0}'.format(package))
        package_name = package.__package__
        if package_name is None:
            package_name = package.__name__
        base_patterns = ('{0}-*.egg-info', 'EGG-INFO')
        patterns = []
        for bp in base_patterns:
            patterns.extend([bp.format(n) for n in (package_name, package_name.capitalize())])
        dir, name = os.path.split(package.__file__)
        candidates = []
        for p in patterns:
            for g in (os.path.join(d, p) for d in (dir, os.path.join(dir, '..'))):
                candidates.extend(glob.glob(g))
        for c in candidates:
            if os.path.exists(os.path.join(c, 'PKG-INFO')):
                path = c
                break
        else:
            raise ValueError('cannot find PKG-INFO for {0}'.format(package_name))
        self._arg_name = package_name
        super(Installed, self).__init__(path)


class WorkingSet(object):
    def __init__(self, entries=None, onerror=None, debug=None):
        self.packages = {}
        self.onerror = onerror or (lambda arg: None)
        self.debug = debug or (lambda arg: None)
        self._find_packages()

    def _find_packages(self):
        for loader, package_name, ispkg in pkgutil.walk_packages(onerror=self.onerror):
            if len(package_name.split('.')) > 1:
                self.debug('Not a top-level package: {0}'.format(package_name))
                continue
            path = loader.find_module(package_name).filename
            if ext(path) in ('.py', '.pyc', '.so'):
                self.debug('Not a package: {0}'.format(package_name))
                continue

            ## We want to keep only packages with metadata-files
            try:
                installed = Installed(package_name)
            except Exception as e:
                self.debug('Error on retrieving metadata from {0}: {1}'.format(package_name, e))
                continue
            self.packages[installed.name] = (path, installed)

    def get(self, package_name, default=None):
        return self.packages.get(package_name, default)

    def __contains__(self, item):
        return item in self.packages

    def __iter__(self):
        for package, data in list(self.packages.items()):
            yield package, data

    def __bool__(self):
        return bool(self.packages)

    def __len__(self):
        return len(self.packages)


def get_metadata(pkg):
    import types

    if type(pkg) is types.ModuleType:
        return Installed(pkg)
    if isinstance(pkg, str):
        try:
            m = __import__(pkg)
        except ImportError:
            pass
        else:
            try:
                return Installed(pkg)
            except ValueError:
                return Develop(pkg)
        if os.path.exists(pkg):
            e = ext(pkg)
            if os.path.isdir(pkg):
                if e == '.egg':
                    return EggDir(pkg)
                return Dir(pkg)
            if e in ('.tar', '.tar.gz', '.tar.bz2', '.zip'):
                return SDist(pkg)
            elif e == '.egg':
                return Egg(pkg)
    raise TypeError('Cannot return a Dist object')