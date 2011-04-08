import os


def name_ext(path):
    p, e = os.path.splitext(path)
    if p.endswith('.tar'):
        return p[:-4], '.tar' + e
    return p, e

def name(path):
    return name_ext(path)[0]

def ext(path):
    return name_ext(path)[1]

## The search parameter is for Egg files, since they have a different structure

def zip_files(zf, search='egg-info'):
    names = [n for n in zf.namelist() if search in n]
    fobj_list = [zf.read(n) for n in names]
    return zip(fobj_list, map(os.path.basename, names))

def tar_files(tf):
    names = [n for n in tf.getnames() if 'egg-info' in n and not n.endswith('egg-info')]
    fobj_list = [tf.extractfile(n).read() for n in names]
    return zip(fobj_list, map(os.path.basename, names))


class _Objectify(object):
    def __init__(self, entries):
        self.__dict__.update(**entries)

    def _valid(self, item):
        return not item.startswith('_') or item in ('_pypi_hidden', '_pypi_ordering')

    def _clean_dict(self):
        return dict((k, v) for k, v in self.__dict__.iteritems() if self._valid(k))

    def __repr__(self):
        return 'Object({0})'.format(self._clean_dict())

    def __contains__(self, item):
        return item in self.__dict__

    def __getitem__(self, item):
        if not self._valid(item):
            raise KeyError(item)
        return getattr(self, item)