import cgi
import errno
import glob
import itertools
import os
import sys
from StringIO import StringIO
from zope.interface import alsoProvides

from twisted.internet.defer import DeferredList, Deferred
from twisted.internet.task import Cooperator
from twisted.internet.protocol import Protocol
from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss

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



class BodyReceiver(Protocol):
    """
    Body receiver, suitable for use with L{IResponse.deliverBody}.

    @type finished: C{Deferred<unicode>}
    @ivar finished: User-specified deferred that is fired with the decoded body
        text, stored in L{_buffer}, when the body has been entirely delivered.

    @type encoding: C{str}
    @ivar encoding: Body text encoding, as specified in the I{'Content-Type'}
        header, defaults to C{'UTF-8'}.

    @type _buffer: C{StringIO}
    @ivar _buffer: Delivered body content buffer.
    """
    def __init__(self, response, finished):
        header, args = cgi.parse_header(
            response.headers.getRawHeaders('Content-Type', default=[''])[0])
        self.encoding = args.get('charset', 'utf-8')
        self.finished = finished
        self._buffer = StringIO()


    def dataReceived(self, data):
        self._buffer.write(data)


    def connectionLost(self, reason):
        if reason.check(PotentialDataLoss, ResponseDone) is None:
            self.finished.errback(reason)
        else:
            data = self._buffer.getvalue().decode(self.encoding)
            self.finished.callback(data)



def deliverBody(response, cls):
    """
    Invoke C{response.deliverBody} with C{cls(response, deferred)}.

    @rtype: C{Deferred}
    @return: A deferred that fires when the instance of C{cls} callbacks it.
    """
    finished = Deferred()
    response.deliverBody(cls(response, finished))
    return finished
