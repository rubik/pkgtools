import os
import sys
import glob
import tarfile
import zipfile
import ConfigParser

from utils import _Objectify, dir_ext


class MetadataFileParser(object):

    def __init__(self, path):

        self.MAP = {
            'PKG-INFO': self.pkg_info,
            'SOURCES.txt': self.list,
            'top_level.txt': self.list,
            'requires.txt': self.list,
            'dependency_links.txt': self.list,
            'installed-files.txt': self.list,
            'entry_points.txt': self.config,
        }
        self.path = path

    def parse(self):
        return self.MAP[os.path.basename(self.path)]()

    def pkg_info(self):
        d = {}
        with open(self.path) as f:
            for line in f:
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
        with open(self.path) as f:
            for line in f:
                d.append(line.strip())
        return d

    def config(self):
        d = {}
        with open(self.path) as f:
            p = ConfigParser.ConfigParser()
            p.readfp(f)
            for s in p.sections():
                d[s] = dict(p.items(s))
        return d


class Dist(object):
    def __init__(self, path):
        self.metadata = {}
        self.path = path
        self.get_metadata()

    def get_metadata(self):
        for f in os.listdir(self.path):
            if f == 'not-zip-safe':
                self.metadata['zip-safe'] = False
            if f.endswith('.txt') or f == 'PKG-INFO':
                path = os.path.join(self.path, f)
                self.metadata[f] = MetadataFileParser(path).parse()
        self.metadata = _Objectify(self.metadata)
        return self.metadata

    def has_metadata(self):
        return bool(self.metadata)

    def file(self, name):
        if name not in self.metadata:
            raise KeyError('This package does not have {0} file'.format(name))
        return self.metadata[name]


class Egg(Dist):
    def __init__(self, egg_path, dest):
        z = zipfile.ZipFile(egg_path)
        z.extractall(dest)
        super(Egg, self).__init__(os.path.join(dest, 'EGG-INFO'))


class SDist(Dist):
    def __init__(self, sdist_path, dest):
        d, e = dir_ext(sdist_path)
        if e == '.zip':
            arch = zipfile.ZipFile(sdist_path)
        elif e.startswith('.tar'):
            mode = 'r' if e == '.tar' else 'r:' + e.split('.')[2]
            arch = tarfile.open(sdist_path, mode=mode)
        arch.extractall(dest)
        path = os.path.join(dest, d, d.split('-')[0] + '.egg-info')
        super(SDist, self).__init__(path)


class Installed(Dist):
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