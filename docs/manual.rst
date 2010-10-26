.. index:: manual, rn

Renamer manual
==============

========
SYNOPSIS
========

rn [*options*] command [*options*] argument ...


===========
DESCRIPTION
===========

**rn** is a command line interface to Renamer, an extensible utility for
renaming files that also keeps a log of previous activities, which allows
actions to be reversed.

The required *command* argument selects which renamer command to execute. Most,
but not all, commands invoke the renaming process on the provided arguments,
the :ref:`undo` command is one example that differs. Consult ``--help`` for a
list of available commands and the :ref:`COMMANDS` section for descriptions of
the builtin commands.

Renamer can be extended with new commands via Python plugins.


=======
OPTIONS
=======

-g, --glob
    Expand arguments as UNIX-style globs.

-x, --one-file-system
    Don't cross filesystems. This is primarily useful for avoiding copy-delete
    behavior when renaming will cross file-system boundaries.

-n, --no-act
    Perform a trial run with no changes made.

--link-src
    Create a symlink at the source. The file will be moved to its new location
    and a symlink created at its original location.

--link-dst
    Create a symlink at the destination. The original file will not be moved
    but a symlink will be created at the new location.

-c file, --config=file
    Read configuration defaults from *file*. The default configuration is read
    from *~/.renamer/renamer.conf*. See the :ref:`CONFIGURATION` section for
    more information.

-e template, --name=template
    Formatted filename. See the :ref:`TEMPLATES` section for more information.

-p template, --prefix=template
    Formatted path to prefix to files before renaming. See the :ref:`TEMPLATES`
    section for more information.

-l number, --concurrent=number
    Maximum number of asynchronous tasks to perform concurrently. The default
    is 10.

--help
    Display a help message describing Renamer's command-line options.

-q, --quiet
    Suppress output.

--version
    Display version information.

-v, --verbose
    Increase output, use more times for greater effect.


.. index:: commands

.. _commands:

========
COMMANDS
========

Commands are the parts of Renamer that process arguments and make things
happen. Most commands will extract metadata from each argument in some fashion
and store that metadata in template variables which is used to rename the
files.

.. index:: tvrage

.. _tvrage:

tvrage
------

Use TV episode metadata from filenames (such as ``Lost S01E01.avi``) to consult
the `TV Rage`_ database for detailed and accurate metadata used in renaming.

Renamer is able to extract metadata from a wide variety of filename structures.
Unfortunately, since useful metadata within the video container itself is
extremely rare, the only reliable way to extract information is from the
filename, meaning that filenames should be as clear as possible and contain as
much useful metadata as possible.

.. _TV Rage: http://tvrage.com/


.. index:: audio

.. _audio:

audio
-----

Use audio metadata from files for renaming. A wide variety of audio and audio
metadata formats are supported.


.. index:: undo

.. _undo:

undo
----

--ignore-errors
    Do not stop the process when encountering OS errors.


Undo previous Renamer actions.

The ``action`` subcommand will undo individual actions while the ``changeset``
subcommand will undo entire changesets, once an item has been undone it is
removed from the history. The ``forget`` subcommand will remove an item from
history without undoing it.

Use the ``list`` subcommand to find identifiers for the changesets or actions
to undo.


.. index:: templates

.. _templates:

=========
TEMPLATES
=========

A Python template string, as described by the Python `template documentation`_,
can contain variables that will be substituted with runtime values from Renamer
commands.

.. _template documentation:
    http://docs.python.org/library/string.html#template-strings

For example the :ref:`tvrage` command provides variables containing TV episode
metadata; so a template such as::

    $series S${padded_season}E${padded_episode} - $title

Applied to episode 1 of season 1 of "Lost" (named "Pilot (1)") will result in::

    Lost S01E01 - Pilot (1)

The variables available will differ from command to command, consult the
``--help`` output for the command to learn more.


.. index:: configuration, config file

.. _configuration:

=============
CONFIGURATION
=============

Configuration files follow a basic INI syntax. Sections are named after their
command names, as listed in ``--help``, the global configuration section is
named ``renamer``. Configuration options are derived from their long
command-line counterparts without the ``--`` prefix. Flags can be turned on or
off with values such as: ``true``, ``yes``, ``1``, ``false``, ``no``, ``0``.

For example the command line::

    rn --concurrent=5 --link-src --prefix=~/stuff somecommand --no-thing

can be specified in a configuration file::

    [renamer]
    concurrent=5
    link-src=yes
    prefix=~/stuff

    [somecommand]
    no-thing=yes

It is also possible to specify global configuration options in a command
section to override them only for that specific command.

Arguments specified on the command line will override values in the
configuration file.


====
BUGS
====

Please report any bugs to the `Renamer Launchpad project`_
``<http://launchpad.net/renamer/>``.

.. _Renamer Launchpad project: http://launchpad.net/renamer/


=====
FILES
=====

~/.renamer/renamer.conf
    Contains the user's default configuration.
