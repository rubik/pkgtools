import xmlrpclib
from utils import _Objectify

def pypi_client(index_url='http://pypi.python.org/pypi', *args, **kwargs):
    return xmlrpclib.ServerProxy(index_url, xmlrpclib.Transport(), *args, **kwargs)


class PyPI(object):
    def __init__(self, *args, **kwargs):
        self._client = pypi_client(*args, **kwargs)

    def list_packages(self):
        return self._client.list_packages()

    def package_releases(self, package_name, show_hidden=False):
        return self._client.package_releases(package_name, show_hidden)

    def release_urls(self, package_name, version):
        return map(_Objectify, self._client.release_urls(package_name, version))

    def release_data(self, package_name, version):
        return _Objectify(self._client.release_data(package_name, version))

    def search(self, spec, operator='or'):
        return map(_Objectify, self._client.search(spec, operator))

    def changelog(self, since):
        return self._client.changelog(since)

    def ratings(self, name, version, since):
        return self._client.ratings(name, version, since)
