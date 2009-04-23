class StackError(RuntimeError):
    """
    An error occured while attempting to manipulate the stack.
    """


class PluginError(RuntimeError):
    """
    An error that has something to do with plugins.
    """


class EnvironmentError(RuntimeError):
    """
    Attempting to do something in the environment failed.
    """
