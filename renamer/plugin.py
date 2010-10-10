import sys
from zope.interface import noLongerProvides

from twisted import plugin
from twisted.python import usage

from renamer import plugins
from renamer.irenamer import IRenamerCommand
from renamer.util import InterfaceProvidingMetaclass



def getPlugins():
    """
    Get all available Renamer plugins.
    """
    return plugin.getPlugins(IRenamerCommand, plugins)



class RenamerSubCommandMixin(object):
    """
    Mixin for Renamer commands.
    """
    def decodeCommandLine(self, cmdline):
        """
        Turn a byte string from the command line into a unicode string.
        """
        codec = getattr(sys.stdin, 'encoding', None) or sys.getdefaultencoding()
        return unicode(cmdline, codec)



class RenamerSubCommand(usage.Options, RenamerSubCommandMixin):
    """
    Sub-level Renamer command.
    """



class RenamerCommandMeta(InterfaceProvidingMetaclass):
    providedInterfaces = [plugin.IPlugin, IRenamerCommand]



class RenamerCommand(usage.Options, RenamerSubCommandMixin):
    """
    Top-level Renamer command.

    These commands will display in the main help listing.
    """
    __metaclass__ = RenamerCommandMeta

    defaultPrefixTemplate = None
    defaultNameTemplate = None


    def parseArgs(self, *args):
        self.parent.parseArgs(*args)


    def postOptions(self):
        self.parent.command = self

noLongerProvides(RenamerCommand, plugin.IPlugin)
noLongerProvides(RenamerCommand, IRenamerCommand)
