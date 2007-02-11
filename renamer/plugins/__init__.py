class PluginError(Exception): pass

def command(fun):
    fun.pluginCommand = True
    return fun
