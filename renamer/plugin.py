import os
import string
import sys
import time
try:
    from xml.etree import ElementTree as etree
    etree # Ssssh, Pyflakes.
except ImportError:
    from elementtree import ElementTree as etree

from twisted import plugin
from twisted.internet import defer
from twisted.python import usage
from twisted.python.components import registerAdapter
from twisted.python.filepath import FilePath

from renamer import errors, logging, plugins
from renamer.irenamer import ICommand, IRenamingCommand, IRenamingAction
from renamer.util import DirectlyProvidingMetaclass



def getCommands():
    """
    Get all available standard commands.
    """
    return plugin.getPlugins(ICommand, plugins)



def getRenamingCommands():
    """
    Get all available renaming commands.
    """
    return plugin.getPlugins(IRenamingCommand, plugins)



def getActions():
    """
    Get all available Renamer actions.
    """
    return plugin.getPlugins(IRenamingAction, plugins)



def getActionByName(name):
    """
    Get an C{IRenamingAction} by name.

    @type name: C{unicode}
    @param name: Name of the action to find.

    @raises NoSuchAction: If no action named C{name} could be found.

    @rtype: C{IRenamingAction}
    """
    for action in getActions():
        if action.name == name:
            return action

    raise errors.NoSuchAction(name)



class _CommandMixin(object):
    """
    Mixin for Renamer commands.
    """
    def decodeCommandLine(self, cmdline):
        """
        Turn a byte string from the command line into a unicode string.
        """
        codec = getattr(sys.stdin, 'encoding', None) or sys.getdefaultencoding()
        return unicode(cmdline, codec)


    def setCommand(self, command):
        if getattr(self.parent, 'command', None) is None:
            self.parent.command = command


    def postOptions(self):
        super(_CommandMixin, self).postOptions()
        self.setCommand(self)



class Command(_CommandMixin, usage.Options):
    """
    Top-level Renamer command.

    This command will display in the main help listing.
    """
    __metaclass__ = DirectlyProvidingMetaclass(
        __name__, 'Command', plugin.IPlugin, ICommand)


    def process(self, renamer):
        pass



class SubCommand(_CommandMixin, usage.Options):
    """
    Sub-level Renamer command.
    """
    def setCommand(self, command):
        self.parent.setCommand(command)



class RenamingCommand(_CommandMixin, usage.Options):
    """
    Top-level renaming command.

    This command will display in the main help listing.
    """
    __metaclass__ = DirectlyProvidingMetaclass(
        __name__, 'RenamingCommand', plugin.IPlugin, IRenamingCommand)


    synopsis = '[options] <argument> [argument ...]'


    defaultPrefixTemplate = None
    defaultNameTemplate = None


    def buildDestination(self, mapping, options, src):
        prefixTemplate = options['prefix']
        if prefixTemplate is None:
            prefixTemplate = self.defaultPrefixTemplate

        if prefixTemplate is not None:
            prefix = os.path.expanduser(
                prefixTemplate.safe_substitute(mapping))
        else:
            prefixTemplate = string.Template(src.dirname())
            prefix = prefixTemplate.template

        ext = src.splitext()[-1]

        nameTemplate = options['name']
        if nameTemplate is None:
            nameTemplate = self.defaultNameTemplate

        filename = nameTemplate.safe_substitute(mapping)
        logging.msg(
            'Building filename: prefix=%r  name=%r  mapping=%r' % (
                prefixTemplate.template, nameTemplate.template, mapping),
            verbosity=3)
        return FilePath(prefix).child(filename).siblingExtension(ext)


    def parseArgs(self, *args):
        self.parent.parseArgs(*args)


    def process(self, renamer):
        arg = renamer.currentArgument
        logging.msg('Processing "%s"' % (arg.path,),
                    verbosity=3)
        d = defer.maybeDeferred(self.processArgument, arg)
        d.addCallback(self.buildDestination, renamer.options, arg)
        return d



class RenamingAction(object):
    __metaclass__ = DirectlyProvidingMetaclass(
        __name__, 'RenamingAction', plugin.IPlugin, IRenamingAction)


    def __init__(self, src, dst, timestamp=None):
        self.src = src
        self.dst = dst
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp


    def __repr__(self):
        return '<%s name=%r src=%r dst=%r timestamp=%r>' % (
            type(self).__name__,
            self.name,
            self.src,
            self.dst,
            self.timestamp)


    def makedirs(self, parent):
        """
        Create any directory structure that does not yet exist.
        """
        if not parent.exists():
            logging.msg('Creating directory structure for "%s"' % (
                parent.path,), verbosity=2)
            parent.makedirs()


    def checkExisting(self, dst):
        """
        Ensure that the destination file does not yet exist.
        """
        if dst.exists():
            msg = 'Refusing to clobber existing file "%s"' % (
                dst.path,)
            logging.msg(msg)
            raise errors.NoClobber(msg)


    def prepare(self, dst, options):
        """
        Prepare an action to be performed.
        """
        self.checkExisting(dst)
        self.makedirs(dst.parent())


    # IRenamingAction

    def asHumanly(self):
        return u'%s: %s => %s (%s)' % (
            self.name.title(), self.src.path, self.dst.path,
            time.asctime(time.localtime(self.timestamp)),)


    @classmethod
    def fromElement(cls, elem):
        actionType = getActionByName(elem.get('name'))
        return actionType(
            src=FilePath(elem.get('src')),
            dst=FilePath(elem.get('dst')),
            timestamp=float(elem.get('timestamp')))


    def asElement(self):
        return etree.Element(
            'action',
            name=self.name,
            src=self.src.path,
            dst=self.dst.path,
            timestamp=unicode(self.timestamp))


registerAdapter(
    RenamingAction.fromElement, etree._ElementInterface, IRenamingAction)
