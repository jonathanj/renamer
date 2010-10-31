import errno
import glob
import itertools
import os
import sys
from zope.interface import alsoProvides

from twisted.internet.defer import DeferredList
from twisted.internet.task import Cooperator

from renamer import errors



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
    """
    coop = Cooperator()
    work = (callable(elem, *a, **kw) for elem in iterable)
    return DeferredList([coop.coiterate(work) for i in xrange(count)])



def rename(src, dst, oneFileSystem=False, renamer=os.rename):
    """
    Rename a file, optionally refusing to do it across file systems.

    @type  src: L{twisted.python.filepath.FilePath}
    @param src: Source path.

    @type  dst: L{twisted.python.filepath.FilePath}
    @param dst: Destination path.

    @type  oneFileSystem: C{bool}
    @param oneFileSystem: Refuse to move a file across file systems?

    @raise renamer.errors.DifferentLogicalDevices: If C{src} and C{dst} reside
        on different filesystems and cross-linking files is not supported on
        the current platform.
    """
    if oneFileSystem:
        try:
            renamer(src.path, dst.path)
        except OSError, e:
            if e.errno == errno.EXDEV:
                raise errors.DifferentLogicalDevices(
                    'Refusing to move "%s" to "%s" on another filesystem' % (
                        src.path, dst.path))
    else:
        src.moveTo(dst)



class InterfaceProvidingMetaclass(type):
    """
    Metaclass that C{alsoProvides} interfaces specified in
    C{providedInterfaces}.
    """
    providedInterfaces = []


    def __new__(cls, name, bases, attrs):
        newcls = type.__new__(cls, name, bases, attrs)
        alsoProvides(newcls, *cls.providedInterfaces)
        return newcls



def globArguments(args, platform=sys.platform, exists=os.path.exists):
    """
    Glob arguments.
    """
    def _iglobWin32(pathname):
        if not exists(pathname):
            return glob.iglob(pathname)
        return [pathname]

    def _glob(globbing):
        return itertools.chain(
            *itertools.imap(globbing, args))

    globbing = glob.iglob
    if platform == 'win32':
        globbing = _iglobWin32
    return _glob(globbing)



def padIterable(iterable, padding, count):
    """
    Pad C{iterable}, with C{padding}, to C{count} elements.

    Iterables containing more than C{count} elements are clipped to C{count}
    elements.

    @param iterable: The iterable to iterate.

    @param padding: Padding object.

    @param count: The padded length.

    @return: An iterable.
    """
    return itertools.islice(
        itertools.chain(iterable, itertools.repeat(padding)), count)
