import os
import sys
import glob
import tarfile
import zipfile
import warnings
import StringIO
import ConfigParser

from utils import ext, tar_files, zip_files
import ConfigParser


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
        return self.MAP[self.name]()

    def pkg_info(self):
        d = {}
        for line in self.data.split('\n'):
            if not line.strip():
                continue
            if line.startswith(' '):
                d['Description'] += line
            parts = line.split(':')
            k, v = parts[0], ':'.join(parts[1:])
            d[k.strip()] = v.strip()
        return d

    def list(self):
        d = []
        for line in self.data.split('\n'):
            if not line.strip():
                continue
            d.append(line.strip())
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

    .. automethod:: file

    .. automethod:: files

    .. automethod:: entry_points_map

    .. automethod:: as_req
    '''

    ## Used by __repr__ method
    _arg_name = None

    def __init__(self, file_objects):
        self.metadata = {}
        self.file_objects = file_objects
        self._get_metadata()

    def __repr__(self):
        ## A little trick to get the real name from sub-classes (like Egg or SDist)
        return '<{0}[{1}] object at {2}>'.format(self.__class__.__name__, self._arg_name, id(self))

    @ property
    def has_metadata(self):
        return bool(self.metadata)

    def _get_metadata(self):
        for data, name in self.file_objects:
            if name == 'not-zip-safe':
                self.metadata['zip-safe'] = False
            elif name.endswith('.txt') or name == 'PKG-INFO':
                self.metadata[name] = MetadataFileParser(data, name).parse()
        ## FIXME: Do we really need _Objectify??
        #self.metadata = _Objectify(self.metadata)
        return self.metadata

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

        return self.metadata.keys()

    def entry_points_map(self, group):
        '''
        Returns the elements under the specified section in the :file:`entry_points.txt` file.
        '''

        try:
            return self.file('entry_points.txt')[group]
        except KeyError:
            return {}

    def as_req(self):
        '''
        Returns a string that represents the parsed requirement.
        '''

        pkg_info = self.file('PKG-INFO')
        return '{0}=={1}'.format(pkg_info['Name'], pkg_info['Version'])


class Egg(Dist):
    '''
    Given the egg path, returns a Dist object::

        >>> e = Egg('pyg-0.1.2-py2.7.egg')
        >>> e
        <Egg[pyg-0.1.2-py2.7.egg] object at 172517100>
        >>> e.files()
        ['requires.txt', 'PKG-INFO', 'SOURCES.txt', 'top_level.txt', 'dependency_links.txt', 'entry_points.txt']
        >>> e.file('requires.txt')
        ['setuptools']
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

        >>> s = SDist('pyg-0.1.2.zip')
        >>> s
        <SDist[pyg-0.1.2.zip] object at 159709868>
        >>> s.files()
        ['requires.txt', 'PKG-INFO', 'SOURCES.txt', 'top_level.txt', 'dependency_links.txt', 'entry_points.txt']
        >>> s.file('requires.txt')
        ['setuptools', 'pkgtools']
        >>> s.file('entry_points.txt')
        {'console_scripts': {'pyg': 'pyg:main'}}
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

        >>> p = Dir('/usr/local/lib/python2.7/dist-packages/pypol_-0.5-py2.7.egg/EGG-INFO')
        >>> p
        <Dir object at 150234636>
        >>> p.files()
        ['top_level.txt', 'dependency_links.txt', 'PKG-INFO', 'SOURCES.txt']
        >>> p.file('PKG-INFO')
        {'Author': 'Michele Lacchia',
         'Author-email': 'michelelacchia@gmail.com',
         'Classifier': 'Programming Language :: Python :: 2.7',
         'Description': 'UNKNOWN',
         'Download-URL': 'http://github.com/rubik/pypol/downloads/',
         'Home-page': 'http://pypol.altervista.org/',
         'License': 'GNU GPL v3',
         'Metadata-Version': '1.0',
         'Name': 'pypol-',
         'Platform': 'any',
         'Summary': 'Python polynomial library',
         'Version': '0.5'}
    '''

    def __init__(self, path):
        files = []
        for f in os.listdir(path):
            with open(os.path.join(path, f)) as fobj:
                data = fobj.read()
            files.append((data, f))
        self._arg_name = os.path.normpath(path)
        super(Dir, self).__init__(files)


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
            except ImportError:
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
