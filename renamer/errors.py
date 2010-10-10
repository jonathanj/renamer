class PluginError(RuntimeError):
    """
    An error that has something to do with plugins.
    """



class DifferentLogicalDevices(RuntimeError):
    """
    An attempt to move a file to a different logical device was made.
    """



class NoSuchAction(ValueError):
    """
    An invalid or unknown action name was specified.
    """



class NoClobber(RuntimeError):
    """
    A destination file already exists.
    """
