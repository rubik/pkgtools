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
    return list(zip(fobj_list, map(os.path.basename, names)))

def tar_files(tf):
    names = [n for n in tf.getnames() if 'egg-info' in n and not n.endswith('egg-info')]
    fobj_list = [tf.extractfile(n).read() for n in names]
    return list(zip(fobj_list, map(os.path.basename, names)))