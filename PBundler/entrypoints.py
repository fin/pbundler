from PBundler import *

def pbcli():
    return PBCli().run(sys.argv)

def pbpy():
    argv = [sys.argv[0], "py"] + sys.argv[1:]
    return PBCli().run(argv)
