"""
Collection of miscellaneous utility functions.
"""
import itertools, re

from twisted.internet.defer import DeferredList
from twisted.internet.task import Cooperator


class ConditionalReplacer(object):
    """
    Perform regular-expression substitutions based on a conditional regular-expression.

    @type globalReplace: C{bool}
    @ivar globalReplace: Flag indicating whether to perform a global replace
        or not

    @type cond: C{regex}
    @ivar cond: Conditional compiled regular-expression

    @type regex: C{regex}
    @ivar regex: Regular-expression to match for substitution
    """
    def __init__(self, cond, regex, subst=None, flags=None):
        """
        Initialise the replacer.

        @type cond: C{str} or C{unicode}
        @param cond: Conditional regular-expression to compile

        @type regex: C{str} or C{unicode}
        @param regex: Regular-expression to match for substitution

        @type subst: C{str} or C{unicode}
        @param subst: String to use for substitution

        @type flags: C{str}
        @param flags: Collection of regular-expression flags, the following
            values are valid::

                i - Ignore case

                g - Global replace
        """
        super(ConditionalReplacer, self).__init__()

        if flags is None:
            flags = ''

        self.globalReplace = 'g' in flags

        reflags = 0
        if 'i' in flags:
            reflags |= re.IGNORECASE

        self.cond = re.compile(cond, reflags)
        self.regex = re.compile(regex, reflags)
        self.subst = subst or ''

    @classmethod
    def fromString(cls, s):
        """
        Create a replacer from a string.

        Parameters should be separated by a literal tab and are passed
        directly to the initialiser.
        """
        return cls(*s.strip('\r\n').split('\t'))

    def replace(self, input, condInput):
        """
        Perform a replacement.

        @type input: C{str} or C{unicode}
        @param input: Input to perform substitution on

        @type condInput: C{str} or C{unicode}
        @param condInput: Input to check against C{cond}

        @rtype: C{str} or C{unicode}
        @return: Substituted result
        """
        if self.cond.search(condInput) is None:
            return input
        return self.regex.sub(self.subst, input, int(not self.globalReplace))


class Replacer(ConditionalReplacer):
    """
    Perform regular-expression substitutions.
    """
    def __init__(self, regex, subst=None, flags=None):
        super(Replacer, self).__init__(r'.*', regex, subst, flags)

    def replace(self, input, condInput):
        return super(Replacer, self).replace(input, input)


class Replacement(object):
    """
    Perform a series of replacements on input.

    @type replacers: C{list}
    @ivar replacers: Replacer objects used to transform input
    """
    def __init__(self, replacers):
        """
        Initialise a Replacer manager.

        @type replacers: C{iterable}
        @param replacers: Initial set of replacer objects
        """
        super(Replacement, self).__init__()
        self.replacers = list(replacers)

    @classmethod
    def fromIterable(cls, iterable, replacerType=Replacer):
        """
        Create a L{Replacement} instance from an iterable.

        Lines beginning with C{#} are ignored

        @type iterable: C{iterable} of C{str} or C{unicode}
        @param iterable: Lines to create replacer objects from.

        @type replacerType: C{type}
        @param replacerType: Replacer object type to create for each line,
            defaults to L{Replacer}

        @rtype: L{Replacement}
        """
        replacers = []
        if iterable is not None:
            replacers = [replacerType.fromString(line)
                         for line in iterable
                         if line.strip() and not line.startswith('#')]
        return cls(replacers)

    def add(self, replacer):
        """
        Add a new replacer object.
        """
        self.replacers.append(replacer)

    def replace(self, input, condInput=None):
        """
        Perform a replacement.
        """
        if condInput is None:
            condInput = input

        for r in self.replacers:
            input = r.replace(input, condInput)

        return input


def parallel(iterable, count, callable, *a, **kw):
    """
    Concurrently fire C{callable} for each element in C{iterable}.

    Any additional arguments or keyword-arguments are passed to C{callable}.

    @type  iterable: C{iterable}
    @param iterable: Values to pass to C{callable}.

    @type  count: C{int}
    @param count: Limit of the number of concurrent tasks.

    @type  callable: C{callable}
    @param callable: Callable to fire concurrently.

    @rtype:  L{twisted.internet.defer.Deferred}
    @return: Results of each call to C{callable}.
    """
    coop = Cooperator()
    work = (callable(elem, *a, **kw) for elem in iterable)
    return DeferredList([coop.coiterate(work) for i in xrange(count)])



def rename(src, dst, oneFileSystem=False):
    """
    Rename a file, optionally refusing to do it across file systems.

    @type  src: L{twisted.python.filepath.FilePath}
    @param src: Source path.

    @type  dst: L{twisted.python.filepath.FilePath}
    @param dst: Destination path.

    @type  oneFileSystem: C{bool}
    @param oneFileSystem: Refuse to move a file across file systems?
    """
    if oneFileSystem:
        try:
            os.rename(src.path, dst.path)
        except OSError, e:
            if e.errno == errno.EXDEV:
                logging.msg(
                    'Refusing to move "%s" to "%s" on another filesystem' % (
                        src.path, dst.path))
    else:
        src.moveTo(dst)
