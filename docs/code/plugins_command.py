import os
import string
import time

from renamer.plugin import RenamingCommand
from renamer.errors import PluginError


class ReadableTimestamps(RenamingCommand):
    # The name of our command, as it will be used from the command-line.
    name = 'timestamp'

    # A brief description of the command's purpose, displayed in --help output.
    description = 'Rename files with POSIX timestamps to human-readble times.'

    # Command-line parameters we support.
    optParameters = [
        ('format', 'f', '%Y-%m-%d %H-%M-%S', 'strftime format.')]

    # The default name template to use if no name template is specified via the
    # command-line or configuration file.
    defaultNameTemplate = string.Template('$time')

    # IRenamerCommand

    def processArgument(self, arg):
        # The extension is not needed as it will be determined from the
        # original file name.
        name, ext = arg.splitext()
        try:
            # Try convert the filename to a floating point number.
            timestamp = float(name)
        except (TypeError, ValueError):
            # If it is not a floating point number then we raise an exception
            # to stop the process.
            raise PluginError('%r is not a valid timestamp' % (name,))
        else:
            # Convert and format the timestamp according to the "format"
            # command-line parameter.
            t = time.localtime(timestamp)
            return {
                'time': time.strftime(self['format'], t)}
