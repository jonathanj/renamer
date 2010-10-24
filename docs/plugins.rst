.. index:: plugins

Creating a Renamer Plugin
=========================

Introduction
------------

Renamer plugins are Python code, discovered by Twisted's `plugin
system`_, that extends Renamer's functionality without having to modify the
core of Renamer.

.. _plugin system:
    http://twistedmatrix.com/documents/current/core/howto/plugin.html

There are two kinds of pluggable code in Renamer:

1. Commands that perform actions unrelated to directly renaming a file. An
   example of this would be the `undo` command.

2. Renaming commands that determine new filenames from existing files and
   ultimately result in an input being renamed. An example of this would be the
   :ref:`tvrage` command.

Since the topic of creating commands that are not directly related to renaming
is so broad, this document will primarily focus on creating a command that
performs renaming.


Foundations
-----------

Renamer commands are simply Twisted `Options`_ subclasses with a few extra bits
thrown in, so all the usual Options attributes (such as ``optParameters``) are
available for use and should be how you expose additional options for your
command.

.. _Options:
    http://twistedmatrix.com/documents/current/core/howto/options.html

In almost all cases you will want to inherit from the ``RenamingCommand`` base
class, as it ensure your subclass provides all the right interfaces as well as
invoking your command and performing the actual file renaming.

At the heart of a renaming command is ``processArgument`` which accepts one
argument and returns a Python dictionary. That dictionary is then used to
perform `template substitution`_ on the ``name`` and ``prefix`` command-line
options (or, if they're not given, command-specific defaults.) This process of
calling ``processArgument`` is repeated for each argument given, letting your
command process one argument at a time.

.. _template substitution:
    http://docs.python.org/library/string.html#template-strings


Deferreds
---------

If your command performs a long-running task, such as fetching data from a web
server, you can return a `Deferred`_ from ``processArgument`` that should
ultimately return with a Python dictionary to be used in assembling the
destination filename.

.. _Deferred:
    http://twistedmatrix.com/documents/current/core/howto/deferredindepth.html


Sample command
--------------

Below is the complete source code of a command that renames files named as
POSIX timestamps (e.g. ``1287758780.4690211.txt``) to a human-readable
representation of the timestamp (e.g. ``2010-10-22 16-46-20.txt``).

.. literalinclude:: code/plugins_command.py
   :linenos:


Installing the plugin
---------------------

Now that we've constructed our command we need to make it available to Renamer.
This process consists of the following simple steps:

1. Create a directory for your plugins such as ``MyRenamerPlugins`` wherever you
   usually put your source code, beneath this create a directory named
   ``renamer`` and beneath that a directory named ``plugins``.

   Your directory tree should look like::

        .
        |-- MyRenamerPlugins
        |   `-- renamer
        |   |   `-- plugins

2. Add your directory (``MyRenamerPlugins`` in the previous step) to sys.path
   (typically by adding it to the PYTHONPATH environment variable.)

3. Put your plugin source code file (with a ``.py`` extension) in the
   ``MyRenamerPlugins/renamer/plugins`` directory. It is important to note that
   this directory must **not** be a Python package (i.e. it must not contain
   ``__init__.py``) and will be skipped (i.e. no plugins will be loaded) if it is
   one.

4. You can verify that your plugin is visible by running an interactive Python
   prompt and doing something similar to::

       >>> from renamer.plugins.timestamp import ReadableTimestamps
       >>>

   (This obviously assumes that you used the ``ReadableTimestamps`` example and
   stored it in a file called ``timestamp.py``.)

   If your plugin is installed correctly there should be no errors importing
   the module.


Using the plugin
----------------

After your plugin has been installed correctly you can use it::

    $ touch 1287758780.4690211.txt
    $ rn timestamp 1287758780.4690211.txt
    $ ls
    2010-10-22 16-46-20.txt

It is possible that you may need to regenerate the Twisted plugin cache if you
notice nonsensical errors related to your plugin objects, especially if you're
actively developing a plugin and testing it. Refer to the Twisted documentation
regarding `plugin caching`_.

.. _plugin caching:
    http://twistedmatrix.com/documents/current/core/howto/plugin.html#auto3
