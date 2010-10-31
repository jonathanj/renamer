from ConfigParser import SafeConfigParser

from renamer import util



_identity = lambda x: x



def flag(value):
    """
    Transform the flag C{value} into a C{bool}.
    """
    if isinstance(value, str):
        value = unicode(value, 'ascii')
    if isinstance(value, unicode):
        return value.lower() in (u'true', u'yes', u'1')
    return bool(value)



def transformersFromOptions(options):
    """
    Extract option transformers from an C{Options} subclass.

    @rtype: C{iterable} of C{(str, callable)}
    @return: Iterable of C{(longOption, transformer)}.
    """
    flags = getattr(options, 'optFlags', [])
    for long, short, desc in flags:
        yield long, flag

    parameters = getattr(options, 'optParameters', [])
    parameters = (util.padIterable(ps, _identity, 5) for ps in parameters)
    global _identity
    for long, short, default, desc, coerce in parameters:
        if coerce is None:
            coerce = _identity
        yield long, coerce



def defaultsFromConfigFactory(config, commandClass):
    """
    Create a factory function that will create an C{ICommand} provider instance
    and apply defaults from a config file.

    @type  config: L{renamer.config.ConfigFile}
    @param config: Config file to use defaults from.

    @type  commandClass: C{type}
    @param commandClass: L{renamer.irenamer.ICommand} provider to apply config
        defaults to.

    @return: C{callable} suitable for passing as the third (parser class)
        argument to C{"subCommands"}.
    """
    def initWrapper():
        conf = config.get(commandClass.name, {})

        def _params():
            parameters = getattr(commandClass, 'optParameters', [])
            parameters = (util.padIterable(p, None, 5) for p in parameters)
            for long, short, default, desc, coerce in parameters:
                if long in conf:
                    default = conf.get(long)
                    if default is not None and coerce is not None:
                        default = coerce(default)
                yield long, short, default, desc, coerce

        commandClass.optParameters = list(_params())
        cmd = commandClass()

        # Since we can't set defaults for flags, we have to apply the
        # defaults after __init__ and before parseOptions.
        flags = getattr(commandClass, 'optFlags', [])
        for long, short, desc in flags:
            if long in conf:
                cmd[long] = flag(conf[long])

        return cmd

    return initWrapper



class ConfigFile(object):
    """
    Configuration file.

    @type sections: C{dict} mapping C{str} to C{dict} mapping C{str} to C{str}.
    @ivar sections: Mapping of section names to mappings of configuration
        options to values.
    """
    def __init__(self, path):
        config = SafeConfigParser()
        if path.exists():
            fd = path.open()
            config.readfp(fd)
            fd.close()

        self.sections = {}
        for section in config.sections():
            options = self.sections.setdefault(section, {})
            for option in config.options(section):
                options[option] = unicode(config.get(section, option))


    def get(self, section, options=None):
        """
        Get and coerce configuration values.

        @type  section: C{str}
        @param section: Section name to retrieve configuration values for.

        @type  options: L{twisted.python.usage.Options}
        @param options: Options to use for determining coercion types, or
            C{None} to perform no coercions.

        @return: Mapping of configuration option names to their coerced values.
        """
        section = self.sections.get(section, {})
        if options is not None:
            for opt, optType in transformersFromOptions(options):
                value = section.get(opt)
                if value is not None:
                    if optType is not None:
                        value = optType(value)
                    section[opt] = value

        return section
