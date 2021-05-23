#!/usr/bin/env python

import yaml
import posixpath
import sys
import os
import time
from xdg import xdg_config_home
from pyalpm import Handle

config_path = posixpath.join(xdg_config_home(), 'alpstein/conf.yml')
config_file = open(config_path, 'r')
config = yaml.load(config_file, Loader=yaml.FullLoader)
pkg_mngr = config['package-manager']


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Pick 'yes' or 'no' " "(or 'y' or 'n').\n")

def isExplicit(pkg):
    return pkg.compute_requiredby() == []


handle = Handle(".", "/var/lib/pacman")
localdb = handle.get_localdb()

# localdb.update(force=False) # TODO

installed_pkgs = [pkg.name for pkg in localdb.pkgcache]
explicit_pkgs = [pkg.name for pkg in localdb.pkgcache if isExplicit(pkg)]

groups = dict(localdb.grpcache)
group_pkgs = [groups[grp] for grp in config['package-groups']]
group_pkgs = [pkg.name for pkgs in group_pkgs for pkg in pkgs]  # flatten

individual_pkgs = config['packages']
selected_pkgs = set(group_pkgs + individual_pkgs)
inadvert_pkgs = set(explicit_pkgs) - selected_pkgs
required_pkgs = selected_pkgs - set(installed_pkgs)

prefix = color.BOLD + color.CYAN + ":: " + color.END + color.BOLD
iprefix = " " + prefix
nothing_to_do = iprefix + "Nothing to do here ✔"


def displayOverview():
    print(prefix + "Selected groups: " + color.END, config['package-groups'])
    print(prefix + "Selected individual packages:" +
        color.END, len(config['packages']))

def removeInadvert():
    print(prefix + "Inadvertently installed packages:" +
          color.END, len(inadvert_pkgs))
    if len(inadvert_pkgs) < 1:
        print(nothing_to_do)
        return
    for pkg in inadvert_pkgs:
        print(" ", pkg)
    q = iprefix + "Call " + color.CYAN + pkg_mngr + " -Rsu" + color.END + "?"
    if query_yes_no(q, default="no"):
        remove_command = pkg_mngr + " -Rsu " + " ".join(inadvert_pkgs)
        os.system(remove_command)
    print()

def installRequired():
    print(prefix + "Packages required to reach target state:" +
          color.END, len(required_pkgs))
    if len(required_pkgs) < 1:
        print(nothing_to_do)
        return
    for pkg in required_pkgs:
        print("\t", pkg)
    q = prefix + "Call " + color.CYAN + pkg_mngr + " -S" + color.END + "?"
    if query_yes_no(q, default="yes"):
        install_command = pkg_mngr + " -S --quiet " + " ".join(required_pkgs)
        os.system(install_command)


def main():
    displayOverview()
    print()
    removeInadvert()
    print()
    installRequired()
    print()
    print(prefix, "Target state reached 🎉")

if __name__ == "__main__":
    main()




# pkg = localdb.get_pkg("syncthing")

# transaction = handle.init_transaction()

# transaction.add_pkg(pkg)
# transaction.prepare()
# transaction.commit()
