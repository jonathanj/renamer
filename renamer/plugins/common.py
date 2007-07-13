import os
import re
import sys

from renamer import plugins

builtin_int = int

def _push(value):
    if value.startswith('$'):
        if value.startswith('$$'):
            return value[1:]
        else:
            global _vars
            return _vars[value[1:]]
    return value

@plugins.command
def push(env, value):
    return _push(value)

@plugins.command
def pushdefault(env, value, default):
    try:
        return _push(value)
    except KeyError:
        return default

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

def _setvar(name, value):
    global _vars
    _vars[name] = value

@plugins.command
def var(env, value, name):
    _setvar(name, value)

@plugins.command
def format(env, fmt):
    global _vars
    return fmt % _vars

@plugins.command
def rename(env, src, dst):
    def _makeSaneFilename(fn):
        fn = re.sub(r'[*<>]', '', fn)

        if sys.platform == 'win32':
            fn = re.sub(r'[?\\|"]', '', fn)
            # XXX: special time hax eg. 12:00 -> 12.00
            fn = re.sub(r'(\d):(\d)', r'\1.\2', fn)
            fn = re.sub(r'[/:]', ' -', fn)

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

@plugins.command
def inc(env, value):
    return value + 1

@plugins.command
def dec(env, value):
    return value - 1

@plugins.command
def regex(env, s, r):
    m = re.match(r, s)
    if m is not None:
        for key, value in m.groupdict().iteritems():
            _setvar(key, value)
        return list(m.groups())
