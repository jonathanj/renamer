import errno

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
