from twisted import plugin

from renamer import plugins
from renamer.errors import PluginError
from renamer.irenamer import IRenamerPlugin


def command(f):
    f.command = True
    return f


def getPlugins():
    return plugin.getPlugins(IRenamerPlugin, plugins)


def getPlugin(name):
    for p in getPlugins():
        if p.name == name:
            return p

    raise PluginError('No plugin named %r.' % (name,))


def getGlobalPlugins():
    for p in getPlugins():
        if p.name is None:
            yield p


class Plugin(object):
    def __init__(self, env, **kw):
        super(Plugin, self).__init__(**kw)
        self.env = env

    def openFile(self, filename):
        return self.env.openPluginFile(self, filename)