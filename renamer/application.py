"""
Renamer application logic.
"""
import glob
import os
import string
import sys

from twisted.internet import reactor, defer
from twisted.python import usage
from twisted.python.filepath import FilePath

from renamer import logging, plugin, util



class Options(usage.Options, plugin.RenamerSubCommandMixin):
    synopsis = '[options] command argument [argument ...]'


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
        for plg in plugin.getPlugins():
            try:
                yield plg.name, None, plg, plg.description
            except AttributeError:
                raise RuntimeError('Malformed plugin: %r' % (plg,))


    def __init__(self):
        usage.Options.__init__(self)
        self['verbosity'] = 1


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


    def glob(self, args):
        """
        Glob arguments.
        """
        def _glob():
            return (arg
                for _arg in args
                for arg in glob.glob(_arg))

        def _globWin32():
            for arg in args:
                if not os.path.exists(arg):
                    globbed = glob.glob(arg)
                    if globbed:
                        for a in globbed:
                            yield a
                        continue
                yield arg

        if sys.platform == 'win32':
            return _globWin32()
        return _glob()


    def parseArgs(self, *args):
        args = (self.decodeCommandLine(arg) for arg in args)
        if self['glob']:
            args = self.glob(args)
        self.args = [FilePath(arg) for arg in args]



class Renamer(object):
    """
    Renamer main logic.

    @type options: L{renamer.application.Options}
    @ivar options: Parsed command-line options.
    """
    def __init__(self, options):
        self.options = options


    def rename(self, dst, src):
        """
        Rename C{src} to {dst}.

        Perform symlinking if specified and create any required directory
        hiearchy.
        """
        options = self.options

        if options['dry-run']:
            logging.msg('Dry-run: %s => %s' % (src.path, dst.path))
            return

        if src == dst:
            logging.msg('Skipping noop "%s"' % (src.path,), verbosity=2)
            return

        if dst.exists():
            logging.msg('Refusing to clobber existing file "%s"' % (
                dst.path,))
            return

        parent = dst.parent()
        if not parent.exists():
            logging.msg('Creating directory structure for "%s"' % (
                parent.path,), verbosity=2)
            parent.makedirs()

        # Linking at the destination requires no moving.
        if options['link-dst']:
            logging.msg('Symlink: %s => %s' % (src.path, dst.path))
            util.symlink(src, dst)
        else:
            logging.msg('Move: %s => %s' % (src.path, dst.path))
            util.rename(src, dst, oneFileSystem=options['one-file-system'])
            if options['link-src']:
                logging.msg('Symlink: %s => %s' % (dst.path, src.path))
                util.symlink(dst, src)


    def _processOne(self, src):
        logging.msg('Processing "%s"' % (src.path,),
                    verbosity=3)
        command = self.options.command

        def buildDestination(mapping):
            prefixTemplate = self.options['prefix']
            if prefixTemplate is None:
                prefixTemplate = command.defaultPrefixTemplate

            if prefixTemplate is not None:
                prefix = os.path.expanduser(
                    prefixTemplate.safe_substitute(mapping))
            else:
                prefixTemplate = string.Template(src.dirname())
                prefix = prefixTemplate.template

            ext = src.splitext()[-1]

            nameTemplate = self.options['name']
            if nameTemplate is None:
                nameTemplate = command.defaultNameTemplate

            filename = nameTemplate.safe_substitute(mapping)
            logging.msg(
                'Building filename: prefix=%r  name=%r  mapping=%r' % (
                    prefixTemplate.template, nameTemplate.template, mapping),
                verbosity=3)
            return FilePath(prefix).child(filename).siblingExtension(ext)

        d = defer.maybeDeferred(command.processArgument, src)
        d.addCallback(buildDestination)
        d.addCallback(self.rename, src)
        return d


    def run(self):
        logging.msg(
            'Running, doing at most %d concurrent operations' % (
                self.options['concurrent'],),
            verbosity=3)
        d = util.parallel(
            self.options.args, self.options['concurrent'], self._processOne)
        d.addErrback(logging.err)
        d.addBoth(lambda ignored: reactor.stop())
        return d
