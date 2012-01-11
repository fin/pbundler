#!/usr/bin/env python
import json
import hashlib
import os, sys, fnmatch
import pkg_resources
import time

class PBFile:
    @staticmethod
    def read(path, filename):
        try:
            with open(os.path.join(path, filename), 'r') as f:
                return f.read()
        except Exception, e:
            return None

    @staticmethod
    def find_upwards(fn, root=os.path.realpath(os.curdir)):
        if os.path.exists(os.path.join(root, fn)):
            return root
        up = os.path.abspath(os.path.join(root, '..'))
        if up == root: return None
        return PBFile.find_upwards(fn, up)

REQUIREMENTS = 'requirements.txt'
REQUIREMENTS_LAST = 'requirements.last'

class PBBasepathNotFound(Exception):
    pass

class PBundle:
    def __init__(self, basepath):
        self.basepath = basepath
        self.workpath = os.path.join(self.basepath, ".pbundle")
        self.virtualenvpath = os.path.join(self.workpath, "virtualenv")
        self.ensure_paths()
        self.ensure_virtualenv()
        self._requirements = None
        self._requirements_last = None

    @staticmethod
    def find_basepath():
        return PBFile.find_upwards(REQUIREMENTS)

    def ensure_paths(self):
        if not os.path.exists(self.workpath):
            os.mkdir(self.workpath)

    def ensure_virtualenv(self):
        if not os.path.exists(os.path.join(self.virtualenvpath, 'bin')):
            os.system("virtualenv --no-site-packages " + self.virtualenvpath + " 2>&1")

    def _parse_requirements(self, text):
        r = {}
        if text is None: return r
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith('#'): continue
            if line == "": continue
            req = pkg_resources.Requirement.parse(line)
            r[req.project_name] = str(req)
        return r

    @property
    def requirements(self):
        if not self._requirements:
            self._requirements = self._parse_requirements(PBFile.read(self.basepath, REQUIREMENTS))
        return self._requirements

    @property
    def requirements_last(self):
        if not self._requirements_last:
            self._requirements_last = self._parse_requirements(PBFile.read(self.workpath, REQUIREMENTS_LAST))
        return self._requirements_last

    def requirements_changed(self):
        return self.requirements_last != self.requirements

    def save_requirements(self):
        with open(os.path.join(self.workpath, REQUIREMENTS_LAST), "w") as f:
            f.write("#pbundle %s, written %s\n" % (REQUIREMENTS_LAST, time.time()))
            for r in self.requirements.values():
                f.write("%s\n" % r)

    def run(self, command, verbose=True):
        cmdline = ' '.join(command)
        if verbose: print "Running \"%s\" ..." % (cmdline,)
        os.system(". " + self.virtualenvpath + "/bin/activate; PBUNDLE_REQ='" + self.basepath + "'; " + cmdline)

    def uninstall_removed(self):
        to_remove = set(self.requirements_last.keys()) - set(self.requirements.keys())
        for p in to_remove:
            self.run(["pip", "uninstall", p])

    def install(self):
        self.run(["pip", "install", "-r", os.path.join(self.basepath, REQUIREMENTS)])

    def upgrade(self):
        self.run(["pip", "install", "--upgrade", "-r", os.path.join(self.basepath, REQUIREMENTS)])

class PBCliError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class PBCli():
    def __init__(self):
        self._pb = None

    @property
    def pb(self):
        if not self._pb:
            basepath = PBundle.find_basepath()
            if not basepath:
                raise PBCliError("Could not find requirements.txt in path from here to root.")
            self._pb = PBundle(basepath)
        return self._pb

    def handle_args(self, argv):
        args = argv[1:]
        command = "install"
        if args:
            command = args.pop(0)
        if 'cmd_' + command in PBCli.__dict__:
            return PBCli.__dict__['cmd_'+command](self, args)
        else:
            raise PBCliError("Unknown command \"%s\"" % (command,))

    def run(self, argv):
        try:
            return self.handle_args(argv)
        except PBCliError, e:
            print "E: " + str(e)
            return 1
        except Exception, e:
            print "E: Internal error in pbundler:\n"
            print "  ", e
            return 120

    def print_usage(self):
        print "pbundle                - Copyright 2012 Christian Hofstaedtler"
        print "pbundle Usage:"
        print "  pbundle [install]    - Run pip, if needed (also uninstalls removed"
        print "                         requirements"
        print "  pbundle upgrade      - Run pip, with --upgrade"
        print "  pbundle init         - Create empty requirements.txt"
        print "  pbundle run program  - Run \"program\" in activated virtualenv"
        print "  pbundle py args      - Run activated python with args"

    def cmd_help(self, args):
        self.print_usage()

    def cmd_init(self, args):
        # can't use PBundle here
        if os.path.exists(REQUIREMENTS):
            raise PBCliError("Cowardly refusing, as %s already exists here." % (REQUIREMENTS,))
        with open(REQUIREMENTS, "w") as f:
            f.write("# pbundle MAGIC\n")
            f.write("#pbundle>=0\n")
            f.write("\n")

    def cmd_install(self, args):
        if self.pb.requirements_changed():
            self.pb.uninstall_removed()
            self.pb.install()
            self.pb.save_requirements()

    def cmd_upgrade(self, args):
        self.pb.uninstall_removed()
        self.pb.upgrade()

    def cmd_run(self, args):
        self.pb.run(args, verbose=False)

    def cmd_py(self, args):
        self.pb.run(["python"] + args, verbose=False)
