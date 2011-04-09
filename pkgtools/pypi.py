import urllib2
import xmlrpclib
try:
    import simplejson as json
except ImportError:
    import json

from utils import _Objectify


def pypi_client(index_url='http://pypi.python.org/pypi', *args, **kwargs):
    return xmlrpclib.ServerProxy(index_url, xmlrpclib.Transport(), *args, **kwargs)

def real_name(package_name, timeout=None):
    r = urllib2.Request('http://pypi.python.org/simple/{0}'.format(package_name))
    return urllib2.urlopen(r, timeout=timeout).geturl().split('/')[-2]

def request(url, timeout=None):
    r = urllib2.Request(url)
    return urllib2.urlopen(r, timeout=timeout)


class PyPIXmlRpc(object):
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


class PyPIJson(object):

    URL = 'http://pypi.python.org/pypi/{0}/json'

    def __init__(self, package_name, fast=False):
        self.package_name = package_name

        # If we don't want to be really fast, we can check if the package name
        # is the real name (because if we don't use the real name it won't work).
        # If we are sure that `package_name` is the real name we can set `fast=True`
        if not fast:
            self.package_name = real_name(package_name)

    def __repr__(self):
        return '<PyPIJson[{0}] object at {1}>'.format(self.package_name, id(self))

    def retrieve(self, package_name=None):
        pkg_name = package_name or self.package_name
        data = request(self.URL.format(pkg_name))
        return json.loads(data.read())