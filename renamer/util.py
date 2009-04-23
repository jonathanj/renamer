import re


class ConditionalReplacer(object):
    def __init__(self, cond, regex, repl):
        super(ConditionalReplacer, self).__init__()

        self.cond = re.compile(cond)
        self.regex = re.compile(regex)
        self.repl = repl

    @classmethod
    def fromString(cls, s):
        return cls(*s.strip().split('\t'))

    def replace(self, input, predInput):
        if self.cond.search(predInput) is None:
            return input
        return self.regex.sub(self.repl, input, int(not self.globalReplace))


class Replacer(ConditionalReplacer):
    def __init__(self, regex, replace):
        super(Replacer, self).__init__(r'.*', regex, replace)

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
