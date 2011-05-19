import sys

if sys.version_info >= (3,):
    import xmlrpc.client as xmlrpclib
    import urllib.request as urllib2
else:
    import xmlrpclib
    import urllib2

try:
    import simplejson as json
except ImportError:
    import json


def pypi_client(index_url='http://pypi.python.org/pypi', *args, **kwargs):
    '''
    Builds a PyPI client from an *index_url*. `*args` and `**kwargs` will be passed directly to the ``ServerProxy`` constructor::

        >>> pypi = pypi_client()
        >>> pypi
        <ServerProxy for pypi.python.org/pypi>
    '''

    return xmlrpclib.ServerProxy(index_url, xmlrpclib.Transport(), *args, **kwargs)

def real_name(package_name, timeout=None):
    '''
    Since the Xml-Rpc and the Json PyPI APIs require the real name of a package, this function finds it.
    For example, if you try :class:`PyPIXmlRpc` with a wrong package name, you will get nothing::

        >>> pypi = PyPIXmlRpc()
        >>> pypi.package_releases('sphinx')
        []

    But if you use the real name::

        >>> real_name('sphinx')
        'Sphinx'
        >>> pypi.package_releases('Sphinx')
        ['1.0.7']
        >>> pypi.package_releases('Sphinx', True)
        ['1.0b2', '1.0b1', '1.0.7', '1.0.6', '1.0.5', '1.0.4', '1.0.3', '1.0.2', '1.0.1',
        '1.0', '0.6b1', '0.6.7', '0.6.6', '0.6.5', '0.6.4', '0.6.3', '0.6.2', '0.6.1', '0.6',
        '0.5.2b1', '0.5.2', '0.5.1', '0.5', '0.4.3', '0.4.2', '0.4.1', '0.4', '0.3', '0.2',
        '0.1.61950', '0.1.61945', '0.1.61843', '0.1.61798', '0.1.61611']

    You can also set a timeout in seconds::

        >>> real_name('sphinx', 1)
        'Sphinx'
        >>> real_name('sphinx', .5)
        'Sphinx'
        >>> real_name('sphinx', .1)
        Traceback (most recent call last):
          File "<pyshell#12>", line 1, in <module>
            real_name('sphinx', .1)
          ...
          File "/usr/lib/python2.7/urllib2.py", line 369, in _call_chain
            result = func(*args)
          File "/usr/lib/python2.7/urllib2.py", line 1185, in http_open
            return self.do_open(httplib.HTTPConnection, req)
          File "/usr/lib/python2.7/urllib2.py", line 1160, in do_open
            raise URLError(err)
        URLError: <urlopen error timed out>
    '''

    r = urllib2.Request('http://pypi.python.org/simple/{0}'.format(package_name))
    return urllib2.urlopen(r, timeout=timeout).geturl().split('/')[-2]


class PyPIXmlRpc(object):
    '''
    Connect to PyPI using the Xml-Rpc API.

    .. automethod:: list_packages

    .. automethod:: package_releases

    .. automethod:: release_urls

    .. automethod:: release_data

    .. automethod:: search

    .. automethod:: changelog
    '''

    def __init__(self, *args, **kwargs):
        self._client = pypi_client(*args, **kwargs)

    def list_packages(self):
        '''
        Retrieve a list of the package names registered with the package index. Returns a list of name strings::

            >>> pypi = PyPIXmlRpc()
            >>> packages = pypi.list_packages()
            >>> len(packages)
            14109
            >>> packages[-10:]
            ['ztfy.utils', 'ztfy.workflow', 'ztfy.zmi', 'zums', 'Zwiki', 'zwiki-zeta',
            'zw.jsmath', 'zw.mail.incoming', 'zw.schema', 'zw.widget']
            >>> packages[:10]
            ['2C.py', '3to2', '3to2_py3k', '4Suite', '4Suite-XML', 'a', 'aafigure', 'Aap',
            'aarddict', 'aardtools']
            >>> 'pkgtools' in packages
            True
            >>> 'pyg' in packages
            True
        '''

        return self._client.list_packages()

    def package_releases(self, package_name, show_hidden=False):
        '''
        Retrieve a list of the releases registered for the given package_name.
        Returns a list with all version strings if *show_hidden* is True or only the non-hidden ones otherwise::

            >>> pypi = PyPIXmlRpc()
            >>> pypi.package_releases('Sphinx')
            ['1.0.7']
            >>> pypi.package_releases('Sphinx', True)
            ['1.0b2', '1.0b1', '1.0.7', '1.0.6', '1.0.5', '1.0.4', '1.0.3', '1.0.2',
            '1.0.1', '1.0', '0.6b1', '0.6.7', '0.6.6', '0.6.5', '0.6.4', '0.6.3',
            '0.6.2', '0.6.1', '0.6', '0.5.2b1', '0.5.2', '0.5.1', '0.5', '0.4.3',
            '0.4.2', '0.4.1', '0.4', '0.3', '0.2', '0.1.61950', '0.1.61945', '0.1.61843',
            '0.1.61798', '0.1.61611']
            >>> pypi.package_releases('pkgtools')
            ['0.2']
            >>> pypi.package_releases('pkgtools', True)
            ['0.2', '0.1']
        '''

        return self._client.package_releases(package_name, show_hidden)

    def release_urls(self, package_name, version):
        '''
        Retrieve a list of download URLs for the given package release. Returns a list of dicts with the following keys:

            * url
            * packagetype (``sdist``, ``bdist``, etc.)
            * filename
            * size
            * md5_digest
            * downloads
            * has_sig
            * python_version (required version, or ``source`` or ``any``)
            * comment text

        ::

            >>> pypi = PyPIXmlRpc()
            >>> release = pypi.release_urls('pkgtools', '0.2')[0]
            >>> release['filename']
            'pkgtools-0.2-py2.7.egg'
            >>> release.filename
            'pkgtools-0.2-py2.7.egg'
            >>> release.size
            14425
            >>> release.url
            'http://pypi.python.org/packages/2.7/p/pkgtools/pkgtools-0.2-py2.7.egg'
            >>> release['python_version']
            '2.7'
        '''

        return self._client.release_urls(package_name, version)

    def release_data(self, package_name, version):
        '''
        Retrieve metadata describing a specific package release. Returns a dict with keys for:

            * name
            * version
            * stable_version
            * author
            * author_email
            * maintainer
            * maintainer_email
            * home_page
            * license
            * summary
            * description
            * keywords
            * platform
            * download_url
            * classifiers (list of classifier strings)
            * requires
            * requires_dist
            * provides
            * provides_dist
            * requires_external
            * requires_python
            * obsoletes
            * obsoletes_dist
            * project_url

        If the release does not exist, an empty dictionary is returned.
        ::

            >>> pypi = PyPIXmlRpc()
            >>> data = pypi.release_data('pkgtools', '0.2')
            >>> data.home_page
            'http://pkgtools.readthedocs.org/'
            >>> data.license
            'MIT'
            >>> data.platform
            'any'
            >>> data['author']
            'Michele Lacchia & Alex Marcat'
            >>> data['name']
            'pkgtools'
            >>> data.name
            'pkgtools'
        '''

        return self._client.release_data(package_name, version)

    def search(self, spec, operator='and'):
        '''
        Search the package database using the indicated search *spec*.

        The *spec* may include any of the keywords described in the above list (except 'stable_version' and 'classifiers'), for example: ``{'description': 'spam'}`` will search description fields. Within the *spec*, a field's value can be a string or a list of strings (the values within the list are combined with an OR), for example: ``{'name': ['foo', 'bar']}``. Valid keys for the *spec* dict are listed here. Invalid keys are ignored:

            * name
            * version
            * author
            * author_email
            * maintainer
            * maintainer_email
            * home_page
            * license
            * summary
            * description
            * keywords
            * platform
            * download_url

        Arguments for different fields are combined using either ``and`` (the default) or ``or``.
        Example: ``search({'name': 'foo', 'description': 'bar'}, 'or')``. The results are returned as a list of dicts {'name': package name, 'version': package release version, 'summary': package release summary}
        '''

        return self._client.search(spec, operator)

    def changelog(self, since):
        '''
        Retrieve a list of four-tuples (name, version, timestamp, action) since the given timestamp. All timestamps are UTC values. The argument is a UTC integer seconds since the epoch.
        '''

        return self._client.changelog(since)


class PyPIJson(object):
    '''
    Use Json to interoperate with PyPI.
    '''

    URL = 'http://pypi.python.org/pypi/{0}{1}/json'

    def __init__(self, package_name, version=None, fast=False):
        self.package_name = package_name

        # If we don't want to be really fast, we can check if the package name
        # is the real name (because if we don't use the real name it won't work).
        # If we are sure that `package_name` is the real name we can set `fast=True`
        if not fast:
            self.package_name = real_name(package_name)

        ## Not the simplest way in the world, but it works
        if version is None:
            self.version = ''
        else:
            self.version = '/{0}'.format(version)

    def __repr__(self):
        return '<PyPIJson[{0}] object at {1}>'.format(self.package_name, id(self))

    def retrieve(self, req_func=None, timeout=None):
        def _request(url, timeout=None):
            r = urllib2.Request(url)
            return urllib2.urlopen(r, timeout=timeout).read()
        if req_func is None:
            req_func = _request
        url = self.URL.format(self.package_name, self.version)
        data = req_func(url, timeout)
        return json.loads(data)

    def find(self):
        data = self.retrieve()
        version = data['info']['version']
        for release in data['urls']:
            yield version, release['filename'], release['md5_digest'], release['url']
