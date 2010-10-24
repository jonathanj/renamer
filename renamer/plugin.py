import os
import string
import sys
from zope.interface import noLongerProvides

from twisted.plugin import getPlugins, IPlugin
from twisted.internet import defer
from twisted.python import usage
from twisted.python.filepath import FilePath

from renamer import errors, logging, plugins
from renamer.irenamer import ICommand, IRenamingCommand, IRenamingAction
from renamer.util import InterfaceProvidingMetaclass



def getCommands():
    """
    Get all available L{renamer.irenamer.ICommand}s.
    """
    return getPlugins(ICommand, plugins)



def getRenamingCommands():
    """
    Get all available L{renamer.irenamer.IRenamingCommand}s.
    """
    return getPlugins(IRenamingCommand, plugins)



def getActions():
    """
    Get all available L{renamer.irenamer.IRenamingAction}s.
    """
    return getPlugins(IRenamingAction, plugins)



def getActionByName(name):
    """
    Get an L{renamer.irenamer.IRenamingAction} by name.

    @type name: C{unicode}
    @param name: Action name.

    @raises L{renamer.errors.NoSuchAction}: If no action named C{name} could be
        found.

    @rtype: L{renamer.irenamer.IRenamingAction}
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


    # ICommand

    def process(self, renamer):
        raise NotImplementedError('Commands must implement "process"')



class CommandMeta(InterfaceProvidingMetaclass):
    providedInterfaces = [IPlugin, ICommand]



class Command(_CommandMixin, usage.Options):
    """
    Top-level generic command.

    This command will display in the main help listing.
    """
    __metaclass__ = CommandMeta

noLongerProvides(Command, IPlugin)
noLongerProvides(Command, ICommand)



class SubCommand(_CommandMixin, usage.Options):
    """
    Sub-level generic command.
    """



class RenamingCommandMeta(InterfaceProvidingMetaclass):
    providedInterfaces = [IPlugin, IRenamingCommand]



class RenamingCommand(_CommandMixin, usage.Options):
    """
    Top-level renaming command.

    This command will display in the main help listing.
    """
    __metaclass__ = RenamingCommandMeta


    synopsis = '[options] <argument> [argument ...]'


    # IRenamingCommand

    defaultPrefixTemplate = None
    defaultNameTemplate = None


    def buildDestination(self, mapping, options, src):
        """
        Build a destination path.

        Substitution of C{mapping} into the C{'prefix'} command-line option
        (defaulting to L{defaultPrefixTemplate}) and the C{'name'} command-line
        option (defaulting to L{defaultNameTemplate}) is performed.

        @type  mapping: C{dict} mapping C{str} to C{unicode}
        @param mapping: Mapping of template variables, used for template
            substitution.

        @type  options: L{twisted.python.usage.Options}

        @type  src: L{twisted.python.filepath.FilePath}
        @param src: Source path.

        @rtype:  L{twisted.python.filepath.FilePath}
        @return: Destination path.
        """
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
        # Parse args like our parent (hopefully renamer.application.Options)
        # which decodes and unglobs stuff.
        # XXX: This is probably not great.
        self.parent.parseArgs(*args)


    # ICommand

    def process(self, renamer):
        arg = renamer.currentArgument
        logging.msg('Processing "%s"' % (arg.path,),
                    verbosity=3)
        d = defer.maybeDeferred(self.processArgument, arg)
        d.addCallback(self.buildDestination, renamer.options, arg)
        return d


    # IRenamingCommand

    def processArgument(self, argument):
        raise NotImplementedError(
            'RenamingCommands must implement "processArgument"')

noLongerProvides(RenamingCommand, IPlugin)
noLongerProvides(RenamingCommand, IRenamingCommand)



class RenamingActionMeta(InterfaceProvidingMetaclass):
    providedInterfaces = [IPlugin, IRenamingAction]



class RenamingAction(object):
    """
    An action that performs some renaming-related function and is undoable.

    @see: L{renamer.irenamer.IRenamingAction}
    """
    __metaclass__ = RenamingActionMeta


    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


    def __repr__(self):
        return '<%s name=%r src=%r dst=%r>' % (
            type(self).__name__,
            self.name,
            self.src,
            self.dst)


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
        Prepare for an action about to be performed.

        The following preparations are done:

            * Check that C{dst} does not already exist.

            * Create any directory structure required for C{dst}.
        """
        self.checkExisting(dst)
        self.makedirs(dst.parent())


    # IRenamingAction

    def do(self, options):
        raise NotImplementedError('Base classes must implement "do"')


    def undo(self, options):
        raise NotImplementedError('Base classes must implement "undo"')

noLongerProvides(RenamingAction, IPlugin)
noLongerProvides(RenamingAction, IRenamingAction)
