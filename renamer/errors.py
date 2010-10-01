class PluginError(RuntimeError):
    """
    An error that has something to do with plugins.
    """



class DifferentLogicalDevices(RuntimeError):
    """
    An attempt to cross-link (either rename or symlink) files was made.
    """
