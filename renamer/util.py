import re

from twisted.internet.defer import DeferredList
from twisted.internet.task import Cooperator


class ConditionalReplacer(object):
    def __init__(self, cond, regex, repl=None, flags=None):
        super(ConditionalReplacer, self).__init__()

        if flags is None:
            flags = ''

        self.globalReplace = 'g' in flags

        reflags = 0
        if 'i' in flags:
            reflags |= re.IGNORECASE

        self.cond = re.compile(cond, reflags)
        self.regex = re.compile(regex, reflags)
        self.repl = repl or ''

    @classmethod
    def fromString(cls, s):
        return cls(*s.strip('\r\n').split('\t'))

    def replace(self, input, predInput):
        if self.cond.search(predInput) is None:
            return input
        return self.regex.sub(self.repl, input, int(not self.globalReplace))


class Replacer(ConditionalReplacer):
    def __init__(self, regex, repl=None, flags=None):
        super(Replacer, self).__init__(r'.*', regex, repl, flags)

    def replace(self, input, predInput):
        return super(Replacer, self).replace(input, input)


class Replacement(object):
    def __init__(self, replacers):
        super(Replacement, self).__init__()
        self.replacers = replacers

    @classmethod
    def fromFile(cls, fd, replacerType=Replacer):
        replacers = []
        if fd is not None:
            replacers = [replacerType.fromString(line) for line in fd if not line.startswith('#')]
        return cls(replacers)

    def add(self, replacer):
        self.replacers.append(replacer)

    def replace(self, input, predInput=None):
        if predInput is None:
            predInput = input

        for r in self.replacers:
            input = r.replace(input, predInput)

        return input


def parallel(iterable, count, callable, *a, **kw):
    """
    Concurrently fire C{callable} for each element in C{iterable}.

    Any additional arguments or keyword-arguments are passed to C{callable}.

    @type iterable: C{iterable}
    @param iterable: Values to pass to C{callable}

    @type count: C{int}
    @param count: Limit of the number of concurrent tasks

    @type callable: C{callable}
    @param callable: Callable to fire concurrently

    @rtype: L{twisted.internet.defer.Deferred}
    @return: Results of each call to C{callable}
    """
    coop = Cooperator()
    work = (callable(elem, *a, **kw) for elem in iterable)
    return DeferredList([coop.coiterate(work) for i in xrange(count)])

