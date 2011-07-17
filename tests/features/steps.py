import os
import sys
from lettuce import *
try:
    import pkgtools.pkg as pkg
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.pardir))
    import pkgtools.pkg as pkg


DISTS = os.path.abspath('dist')
ENV = {}

@step(r'I set (?P<var>[\w][\w\d]*) to "(?P<arg>.*?)" as (?P<obj>\w+)$')
def i_set_to_as(step, var, arg, obj):
    dist = getattr(pkg, obj)(os.path.join(DISTS, arg))
    ENV[var] = dist
    setattr(world, var, dist)

@step(r'I get (?P<var>[\w][\w\d]*)\.(?P<attr>.*)$')
def i_get_attr(step, var, attr):
    world.res = getattr(ENV[var], attr)

@step(r'I see (.*)$')
def i_see(step, result):
    if str(world.res) != result:
        raise AssertionError('Wrong result. Expected %s, got %s' % (world.res, result))