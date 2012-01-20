Python Bundler
==============

Simplifies virtualenv and pip usage.

Aims to be compatible with all existing projects already carrying a "requirements.txt" in their source.

Inspired by http://gembundler.com/

Howto
-----

* easy\_install pbundler
* cd into your project path
* Run pbundle. It will install your project's dependencies into a fresh virtualenv.

To run commands with the activated virtualenv:

    pbundle run echo "I am activated. virtualenv: \$VIRTUAL_ENV"


Or, for python programs:

    pbundle py ./debug.py


If you don't have a requirements.txt yet but have an existing project, try this:

    pip freeze > requirements.txt


If you start fresh, try this for a project setup:

    mkdir myproject && cd myproject
    git init
    pbundle init


Making python scripts automatically use pbundle py
--------------------------------------------------

Replace the shebang with "/usr/bin/env pbundle-py". Example:

    #!/usr/bin/env pbundle-py
    import sys
    print sys.path


TODO
----

* Build inventory from what is installed, instead of requirements.last file
* Handle failed egg installs
* Really remove all no longer needed packages from virtualenv
* Get rid of os.system
* Reorganize library code

