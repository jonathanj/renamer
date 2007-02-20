import os
import re
import sys

from renamer import plugins

builtin_int = int

@plugins.command
def push(env, value):
    return value

@plugins.command
def pop(env, dummy):
    return

@plugins.command
def dup(env):
    return env.stack.peek()

@plugins.command
def pushlist(env):
    l = env.stack.pop()
    for e in reversed(l):
        env.stack.push(e)

@plugins.command
def duplistn(env, l, index):
    index = builtin_int(index)
    env.stack.push(l)
    return l[index]

@plugins.command
def split(env, s, delim):
    return s.split(delim)

@plugins.command
def splitn(env, s, delim, n):
    n = builtin_int(n)
    return s.split(delim, n)

@plugins.command
def rsplitn(env, s, delim, n):
    n = builtin_int(n)
    return s.rsplit(delim, n)

@plugins.command
def join(env, l, delim):
    return delim.join(l)

@plugins.command
def strip(env, s, c):
    return s.strip(c)

@plugins.command
def title(env, s):
    return s.title()

@plugins.command
def lower(env, s):
    return s.lower()

@plugins.command
def int(env, s):
    return builtin_int(s)

_vars = {}

@plugins.command
def var(env, value, name):
    global _vars
    _vars[name] = value

@plugins.command
def format(env, fmt):
    global _vars
    return fmt % _vars

@plugins.command
def rename(env, src, dst):
    def _makeSaneFilename(fn):
        fn.replace('*', ''
         ).replace('<', ''
         ).replace('>', '')

        if sys.platform == 'win32':
            fn = fn.replace('?', ''
                 ).replace('\\', ''
                 ).replace('/', ' -'
                 ).replace(':', ' -'
                 ).replace('|', ''
                 ).replace('"', '')

        return fn

    dst = _makeSaneFilename(dst)

    print '%s ->\n  %s' % (src, dst)
    if env.safemode:
        return

    os.rename(src, dst)

@plugins.command
def load(env, name):
    '''Load a plugin.'''
    env.load(name)

@plugins.command
def camel_case_into_sentence(env, s):
    '''Converts a proper camel-case string (LikeThisOne) into a sentence (Like This One).'''
    return re.sub(r'(?<![\s-])([A-Z\(])', r' \1', s).strip()

@plugins.command
def stack(env):
    '''Displays the current stack.'''
    print env.stack

@plugins.command
def help(env, name):
    '''Displays help for a command.'''
    fn = env.resolveFunction(name)
    if fn.__doc__:
        print fn.__doc__
    else:
        print 'No help available.'
