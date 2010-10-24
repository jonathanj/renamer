import errno
from zope.interface import Interface

from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import errors, util



class UtilTests(TestCase):
    """
    Tests for L{renamer.util}.
    """
    def setUp(self):
        self.path = FilePath(self.mktemp())
        self.path.makedirs()


    def exdev(self, s, d):
        e = OSError()
        e.errno = errno.EXDEV
        raise e


    def test_rename(self):
        """
        Rename a file, copying it across filesystems if need be.
        """
        src = self.path.child('src')
        src.touch()
        dst = self.path.child('dst')
        self.assertTrue(not dst.exists())
        util.rename(src, dst)
        self.assertTrue(dst.exists())


    def test_renameOneFileSystem(self):
        """
        Attempting to rename a file across file system boundaries when
        C{oneFileSystem} is C{True} results in
        L{renamer.errors.DifferentLogicalDevices} being raised, assuming the
        current platform doesn't support cross-linking.
        """
        src = self.path.child('src')
        src.touch()
        dst = self.path.child('dst')
        self.assertRaises(
            errors.DifferentLogicalDevices,
            util.rename, src, dst, oneFileSystem=True, renamer=self.exdev)

        self.assertTrue(not dst.exists())
        util.rename(src, dst, oneFileSystem=True)
        self.assertTrue(dst.exists())



class GlobTests(TestCase):
    """
    Tests for L{renamer.util.globArguments}.
    """
    def setUp(self):
        self.path = FilePath(self.mktemp())
        self.path.makedirs()

        filenames = ['a', 'ab', '.a', 'a[b]c']
        for fn in filenames:
            self.path.child(fn).touch()


    def assertGlob(self, expected, paths, **kw):
        """
        Assert that L{renamer.util.globArguments}C{(paths, **kw)} returns a
        result equal to C{expected}.
        """
        paths = [self.path.child(p).path for p in paths]
        res = util.globArguments(paths, **kw)
        self.assertEquals(
            sorted(expected), sorted(FilePath(v).basename() for v in res))


    def test_glob(self):
        """
        Non-Windows globbing will expand an iterable of glob arguments
        according to regular globbing rules.
        """
        values = [
            (['a*'], ['a', 'a[b]c', 'ab']),
            (['a?'], ['ab'])]
        for paths, expected in values:
            self.assertGlob(expected, paths)

        self.assertGlob(
            [], ['a[b]c'],
            platform='notwin32')


    def test_globWin32(self):
        """
        On Windows globbing will only occur if the glob argument is not the
        name of an existing file, in which case the existing file name will be
        the only result of globbing that argument.
        """
        self.assertGlob(
            ['a', 'a[b]c'],
            ['[ab]', 'a[b]c'],
            platform='win32')



class IThing(Interface):
    """
    Silly test interface.
    """



class ThingMeta(util.InterfaceProvidingMetaclass):
    """
    Metaclass that C{alsoProvides} IThing.
    """
    providedInterfaces = [IThing]



class Thing(object):
    """
    IThing, the silly test interface, providing base class.
    """
    __metaclass__ = ThingMeta



class InterfaceProvidingMetaclassTests(TestCase):
    """
    Tests for L{renamer.util.InterfaceProvidingMetaclass}.
    """
    def test_providedBy(self):
        """
        Interfaces are not provided by subclasses.
        """
        self.assertTrue(IThing.providedBy(Thing))
