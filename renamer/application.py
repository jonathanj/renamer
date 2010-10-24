"""
Renamer application logic.
"""
import itertools
import os
import string
import sys

from axiom.store import Store

from twisted.internet import defer
from twisted.python import usage, log
from twisted.python.filepath import FilePath

from renamer import logging, plugin, util
from renamer.irenamer import IRenamingCommand
from renamer.history import History



class Options(usage.Options, plugin._CommandMixin):
    optFlags = [
        ('glob',            'g',  'Expand arguments as UNIX-style globs.'),
        ('one-file-system', 'x',  "Don't cross filesystems."),
        ('no-act',          'n',  'Perform a trial run with no changes made.'),
        ('link-src',        None, 'Create a symlink at the source.'),
        ('link-dst',        None, 'Create a symlink at the destination.')]


    optParameters = [
        ('name',   'e', None,
         'Formatted filename.', string.Template),
        ('prefix', 'p', None,
         'Formatted path to prefix to files before renaming.', string.Template),
        ('concurrent', 'l',  10,
         'Maximum number of concurrent tasks to perform at a time.', int)]


    @property
    def subCommands(self):
        commands = itertools.chain(
            plugin.getRenamingCommands(), plugin.getCommands())
        for plg in commands:
            try:
                yield plg.name, None, plg, plg.description
            except AttributeError:
                raise RuntimeError('Malformed plugin: %r' % (plg,))


    def __init__(self):
        usage.Options.__init__(self)
        self['verbosity'] = 1


    @property
    def synopsis(self):
        return 'Usage: %s [options]' % (
            os.path.basename(sys.argv[0]),)


    def opt_verbose(self):
        """
        Increase output, use more times for greater effect.
        """
        self['verbosity'] = self['verbosity'] + 1

    opt_v = opt_verbose


    def opt_quiet(self):
        """
        Suppress output.
        """
        self['verbosity'] = self['verbosity'] - 1

    opt_q = opt_quiet


    def parseArgs(self, *args):
        args = (self.decodeCommandLine(arg) for arg in args)
        if self['glob']:
            args = util.globArguments(args)
        self.args = (FilePath(arg) for arg in args)



class Renamer(object):
    """
    Renamer main logic.

    @type store: L{axiom.store.Store}
    @ivar store: Renamer database Store.

    @type history: L{renamer.history.History}
    @ivar history: Renamer history Item.

    @type options: L{renamer.application.Options}
    @ivar options: Parsed command-line options.

    @type command: L{renamer.irenamer.ICommand}
    @ivar command: Renamer command being executed.
    """
    def __init__(self):
        obs = logging.RenamerObserver()
        log.startLoggingWithObserver(obs.emit, setStdout=False)

        self.store = Store(os.path.expanduser('~/.renamer/renamer.axiom'))
        # XXX: One day there might be more than one History item.
        self.history = self.store.findOrCreate(History)

        self.options = Options()
        self.options.parseOptions()
        obs.verbosity = self.options['verbosity']
        self.command = self.getCommand()


    def getCommand(self):
        """
        Get the L{twisted.python.usage.Options} command that was invoked.
        """
        command = getattr(self.options, 'subOptions', None)
        if command is None:
            raise usage.UsageError('At least one command must be specified')

        while getattr(command, 'subOptions', None) is not None:
            command = command.subOptions

        return command


    def performRename(self, dst, src):
        """
        Perform a file rename.
        """
        options = self.options
        if options['no-act']:
            logging.msg('Simulating: %s => %s' % (src.path, dst.path))
            return

        if src == dst:
            logging.msg('Skipping noop "%s"' % (src.path,), verbosity=2)
            return

        if options['link-dst']:
            self.changeset.do(
                self.changeset.newAction(u'symlink', src, dst),
                options)
        else:
            self.changeset.do(
                self.changeset.newAction(u'move', src, dst),
                options)
            if options['link-src']:
                self.changeset.do(
                    self.changeset.newAction(u'symlink', dst, src),
                    options)


    def runCommand(self, command):
        """
        Run a generic command.
        """
        return defer.maybeDeferred(command.process, self)


    def runRenamingCommand(self, command):
        """
        Run a renaming command.
        """
        def _processOne(src):
            self.currentArgument = src
            d = self.runCommand(command)
            d.addCallback(self.performRename, src)
            return d

        self.changeset = self.history.newChangeset()
        logging.msg(
            'Running, doing at most %d concurrent operations' % (
                self.options['concurrent'],),
            verbosity=3)
        return util.parallel(
            self.options.args, self.options['concurrent'], _processOne)


    def run(self):
        """
        Begin processing commands.
        """
        if IRenamingCommand(type(self.command), None) is not None:
            d = self.runRenamingCommand(self.command)
        else:
            d = self.runCommand(self.command)
        d.addCallback(self.exit)
        return d


    def exit(self, ignored):
        """
        Perform the exit routine.
        """
        # We can safely do this even with "no-act", since nothing was actioned
        # and there is no point leaving orphaned Items around.
        self.history.pruneChangesets()
