import fileinput
import re
import os
import sys

# usage: python3 main.py example.cfg

# this takes a raw paste from "show firewall policy"


def normalize(input: str) -> str:
    """Converts input ' ' spaces to '-' dashes and downcases
    Returns a string
    """

    clean = input.replace(" ", "-").lower()

    return clean


def generate_terraform(input: str):
    """Generates terraform resource blocks for firewall policies
    Takes fortios 6.0.0+ CLI output of "show firewall policy"
    """

    f = open("policy.tf", "a")

    action = '  action   = "accept"\n'
    schedule = '  schedule = "always"\n'

    # Add header for appended files
    f.write("### AUTOMATICALLY GENERATED CODE BELOW ###" + "\n\n\n")

    # Find all policies
    policy_re = re.compile(r"\s+edit \d+\n(?:\s+set [^\n]+\n)+\s+next", re.MULTILINE)
    policy = policy_re.findall(input)

    # Iterate through policies individually
    for p in policy:
        policy_id = re.search("\d+", p).group(0)
        name = re.search('(?:set name) "(.+)"', p).group(1)
        srcintf_match = re.search('(?:set srcintf)(( "[a-zA-Z0-9_\-\s]+")+)', p)
        srcaddr_match = re.search('(?:set srcaddr)(( "[a-zA-Z0-9_.\-\s]+")+)', p)
        dstintf_match = re.search('(?:set dstintf)(( "[a-zA-Z0-9_\-\s]+")+)', p)
        dstaddr_match = re.search('(?:set dstaddr)(( "[a-zA-Z0-9_.\-\s]+")+)', p)
        service_match = re.search('(?:set service)(( "[a-zA-Z0-9_\-\s]+")+)', p)

        # Format of multi src/dst in a policy differs between cli / tf
        # we split the matches into a list, so we can build terraform blocks
        blocks = {
            "srcintf": srcintf_match.group(1).split(),
            "srcaddr": srcaddr_match.group(1).split(),
            "dstintf": dstintf_match.group(1).split(),
            "dstaddr": dstaddr_match.group(1).split(),
            "service": service_match.group(1).split(),
        }

        # Import for policy
        f.write(
            "import {"
            + "\n  "
            + f'id = "{policy_id}"'
            + "\n  "
            + f"to = fortios_firewall_policy.{normalize(name)}"
            + "\n"
            + "}"
            + "\n\n"
        )

        # Policy attributes
        f.write(
            f'resource "fortios_firewall_policy" "{normalize(name)}" {{\n'
            + f'  name     = "{name}"\n'
            + f"  policyid = {policy_id}\n"
            + action
            + schedule
        )

        # Policy blocks
        for srcdst_type in blocks:
            for srcdst in blocks[srcdst_type]:
                f.write(f"\n  {srcdst_type} {{\n" + f"    name = {srcdst}\n  }}")

        # end terraform resource
        f.write("\n}\n\n\n")

    f.write("### END OF GENERATED CODE ###" + "\n\n")
    f.close()
    return


def main():
    filename = sys.argv[1]

    f = open(filename, "r")
    input = f.read()

    generate_terraform(input)


if __name__ == "__main__":
    main()
