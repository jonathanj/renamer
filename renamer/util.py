import re


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
        return cls(*s.split('\t'))

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
            replacers = [replacerType.fromString(line) for line in fd]
        return cls(replacers)

    def add(self, replacer):
        self.replacers.append(replacer)

    def replace(self, input, predInput=None):
        if predInput is None:
            predInput = input

        for r in self.replacers:
            input = r.replace(input, predInput)

        return input
