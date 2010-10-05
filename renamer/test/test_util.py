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


    def test_symlink(self):
        """
        Symlink a file, copying it across filesystems if need be.
        """
        src = self.path.child('src')
        src.touch()
        dst = self.path.child('dst')
        self.assertTrue(not dst.exists())
        util.symlink(src, dst)
        self.assertTrue(dst.exists())
        self.assertTrue(dst.islink())


    def test_crosslinking(self):
        """
        Attempting to symlink a file across file system boundaries results in
        L{renamer.errors.DifferentLogicalDevices} being raised, assuming the
        current platform doesn't support cross-linking.
        """
        src = self.path.child('src')
        src.touch()
        dst = self.path.child('dst')
        self.assertRaises(
            errors.DifferentLogicalDevices,
            util.symlink, src, dst, symlinker=self.exdev)



class IThing(Interface):
    """
    Silly test interface.
    """



class Thing(object):
    """
    IThing, the silly test interface, providing base class.
    """
    __metaclass__ = util.DirectlyProvidingMetaclass(
        __name__, 'Thing', IThing)



class SomeThing(Thing):
    """
    Provide IThing by subclassing Thing.
    """



class DirectlyProvidingMetaclassTests(TestCase):
    """
    Tests for L{renamer.util.DirectlyProvidingMetaclass}.
    """
    def test_providedBy(self):
        """
        Interfaces are not provided by the base class but are provided by any
        subclasses.
        """
        self.assertFalse(
            IThing.providedBy(Thing))
        self.assertTrue(
            IThing.providedBy(SomeThing))


    def test_type(self):
        """
        L{renamer.util.DirectlyProvidingMetaclass} returns a type instance,
        suitable for use as a metaclass.
        """
        t = util.DirectlyProvidingMetaclass(__name__, 'Chuck', IThing)
        self.assertTrue(isinstance(t, type))
