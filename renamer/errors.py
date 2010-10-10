class PluginError(RuntimeError):
    """
    An error that has something to do with plugins.
    """



class DifferentLogicalDevices(RuntimeError):
    """
    An attempt to move a file to a different logical device was made.
    """
