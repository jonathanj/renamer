from twisted import plugin

from renamer import plugins
from renamer.errors import PluginError
from renamer.irenamer import IRenamerPlugin


def command(func):
    """
    Decorate a function as a Renamer plugin command.
    """
    func.command = True
    return func


def getPlugins():
    """
    Get all available Renamer plugins.
    """
    return plugin.getPlugins(IRenamerPlugin, plugins)


def getPlugin(name):
    """
    Get a plugin by name.

    @raise PluginError: If no plugin is named C{name}
    """
    for p in getPlugins():
        if p.name == name:
            return p

    raise PluginError('No plugin named %r.' % (name,))


def getGlobalPlugins():
    """
    Get all available global plugins.
    """
    for p in getPlugins():
        if p.name is None:
            yield p


class Plugin(object):
    """
    Mixin for Renamer plugins.

    @type env: L{Environment}

    @type config: C{dict}
    @param config: Plugin-specific parameters
    """
    def __init__(self, env, **kw):
        super(Plugin, self).__init__(**kw)
        self.env = env
        self.config = self._readConfig()

    def _readConfig(self):
        """
        Read a user-provided plugin configuration.

        The configuration is can be found in C{~/.renamer/plugin_name/config}.

        @rtype: C{dict}
        """
        fd = self.openFile('config')
        config = {}
        if fd is not None:
            for line in fd:
                key, value = line.strip().split('=', 1)
                config[key] = value

        return config

    def openFile(self, filename):
        """
        Open a user-provided file.

        Plugin files are found in C{~/.renamer/plugin_name/}.
        """
        return self.env.openPluginFile(self, filename)

    @command
    def confvar(self, name, default):
        """
        Get a config variable.
        """
        return self.config.get(name, default)
