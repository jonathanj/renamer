from epsilon.setuphelper import autosetup

import renamer

distobj = autosetup(
    name="Renamer",
    version=renamer.version.short(),
    maintainer="Jonathan Jacobs",
    url="http://launchpad.net/renamer",
    license="MIT",
    platforms=["any"],
    description="A mass file renamer with plugin support",
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities"],

    scripts=['bin/rn'])
