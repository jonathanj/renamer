class PluginError(RuntimeError):
    """
    An error that has something to do with plugins.
    """



class DifferentLogicalDevices(RuntimeError):
    """
    An attempt to cross-link (either rename or symlink) files was made.
    """



class NoSuchAction(ValueError):
    """
    An invalid or unknown action name was specified.
    """



class NoClobber(RuntimeError):
    """
    A destination file already exists.
    """
