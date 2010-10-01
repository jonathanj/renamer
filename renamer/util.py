import errno, os

from twisted.internet.defer import DeferredList
from twisted.internet.task import Cooperator

from renamer import errors, logging



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



def symlink(src, dst, symlinker=os.symlink):
    """
    Symlink a file.

    @type  src: L{twisted.python.filepath.FilePath}
    @param src: Source path.

    @type  dst: L{twisted.python.filepath.FilePath}
    @param dst: Destination path.

    @param symlinker: C{callable} taking two paths

    @raise renamer.errors.DifferentLogicalDevices: If C{src} and C{dst} reside
        on different filesystems and cross-linking files is not supported on
        the current platform.
    """
    try:
        symlinker(src.path, dst.path)
    except OSError, e:
        if e.errno == errno.EXDEV:
            raise errors.DifferentLogicalDevices(
                'Refusing to symlink "%s" to "%s" on another filesystem' % (
                    src.path, dst.path))



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
