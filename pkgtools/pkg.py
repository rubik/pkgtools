import os
import sys
import glob
import tarfile
import zipfile
import warnings
import StringIO
import ConfigParser

from utils import ext, tar_files, zip_files


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
    def __init__(self, file_objects):
        self.metadata = {}
        self.file_objects = file_objects
        self.get_metadata()

    def __repr__(self):
        ## A little trick to get the real name from sub-classes (like Egg or SDist)
        return '<{0} object at {1}>'.format(self.__class__.__name__, id(self))

    def get_metadata(self):
        for data, name in self.file_objects:
            if name == 'not-zip-safe':
                self.metadata['zip-safe'] = False
            elif name.endswith('.txt') or name == 'PKG-INFO':
                self.metadata[name] = MetadataFileParser(data, name).parse()
        ## FIXME: Do we really need _Objectify??
        #self.metadata = _Objectify(self.metadata)
        return self.metadata

    def has_metadata(self):
        return bool(self.metadata)

    def file(self, name):
        if name not in self.metadata:
            raise KeyError('This package does not have {0} file'.format(name))
        return self.metadata[name]

    def files(self):
        return self.metadata.keys()


class Egg(Dist):
    def __init__(self, egg_path,):
        z = zipfile.ZipFile(egg_path)
        super(Egg, self).__init__(zip_files(z))


class SDist(Dist):
    def __init__(self, sdist_path):
        e = ext(sdist_path)
        if e == '.zip':
            arch = zipfile.ZipFile(sdist_path)
            func = zip_files
        elif e.startswith('.tar'):
            mode = 'r' if e == '.tar' else 'r:' + e.split('.')[2]
            arch = tarfile.open(sdist_path, mode=mode)
            func = tar_files
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
        super(Dir, self).__init__(files)


class Develop(Dir):
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
        super(Develop, self).__init__(path)


class Installed(Dir):
    '''
    This class accept either a string or a module object and returns a Dist object::

        
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
        super(Installed, self).__init__(path)