#!/opt/homebrew/bin/python3
import fileinput
import re
import os
import sys

# usage: python3 main.py example.cfg

# this takes a raw paste from the output of
# `show firewall policy` on a fortigate
# and produces terraform objects and matching import statements
# two files are created, the first 'import.sh' is used to import the existing policies
# the second, 'policy.tf' is needed for the import to work

# it does NOT like spaces or slashes in address / policy names
# you may need to massage those in the raw paste


def checks():
    """Pre-flight checks

    WARNING, THIS WILL DELETE 'import.sh' and 'policy.tf' if present!!!
    """
    if os.path.exists("import.sh"):
        os.remove("import.sh")

    if os.path.exists("policy.tf"):
        os.remove("policy.tf")
    return


def generate_import(input: str):
    """Generates terraform import commands

    This takes a raw paste from the fortigate, and generates import commands
    """
    f = open("import.sh", "a")

    f.write("#!/bin/bash\n")

    import_re = re.compile(r"(?:edit) (\d+)")
    import_matches = import_re.findall(input)

    for policy in import_matches:
        f.write(
            "terraform import fortios_firewall_policy.pol"
            + policy
            + " "
            + policy
            + "\n"
        )

    f.close()
    return


def generate_terraform(input: str):
    """Generates terraform resource blocks for firewall policies

    Expects normal fortigate 6.0.0+ output
    """
    f = open("policy.tf", "a")

    policy_re = re.compile(r"\s+edit \d+\n(?:\s+set [^\n]+\n)+\s+next", re.MULTILINE)
    policy = policy_re.findall(input)

    # we iterate through the matches, so we can construct the terraform resources individually
    for p in policy:
        policy_id = re.search("\d+", p).group(0)
        name = re.search("(?:set name) (.+)", p).group(1)
        srcintf_match = re.search('(?:set srcintf)(( "[a-zA-Z0-9_\-\s]+")+)', p)
        srcaddr_match = re.search('(?:set srcaddr)(( "[a-zA-Z0-9_\-\s]+")+)', p)
        dstintf_match = re.search('(?:set dstintf)(( "[a-zA-Z0-9_\-\s]+")+)', p)
        dstaddr_match = re.search('(?:set dstaddr)(( "[a-zA-Z0-9_\-\s]+")+)', p)
        service_match = re.search('(?:set service)(( "[a-zA-Z0-9_\-\s]+")+)', p)

        # blocks can be repeated in terraform, but are all on one line in the fortigate CLI
        # we split the matches into a list, and make a dict for easier handling
        blocks = {
            "srcintf": srcintf_match.group(1).split(),
            "srcaddr": srcaddr_match.group(1).split(),
            "dstintf": dstintf_match.group(1).split(),
            "dstaddr": dstaddr_match.group(1).split(),
            "service": service_match.group(1).split(),
        }

        # arguments for a resource
        # watch the quotes (', ") here, as the syntax differs between CLI and terraform
        f.write(
            'resource "fortios_firewall_policy" '
            + '"pol'
            + policy_id
            + '" '
            + "{\n"
            + 'action = "accept"'
            + "\nname= "
            + name
            + "\npolicyid = "
            + policy_id
            + "\n"
            + 'schedule = "always"\n'
        )

        # this iterates through multiple values and produces terraform blocks
        for block in blocks:
            for name in blocks[block]:
                f.write("\n" + block + " {" + "\nname = " + name + "\n}")

        # end terraform resource
        f.write("\n}\n\n")

    f.close()
    return


def main():
    checks()

    filename = sys.argv[1]

    f = open(filename, "r")
    input = f.read()

    generate_import(input)
    generate_terraform(input)


if __name__ == "__main__":
    main()
