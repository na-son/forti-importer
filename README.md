# Fortios Policy Import

This script generates terraform and imports from fortios 6.0.0+ "show firewall policy"


## Usage

An example config is provided to demonstrate:

`python3 main.py example.cfg`


It expects a raw paste, with the same formatting as the CLI.

Mapping of interfaces, addresses, and services to terraform resources is not done.

If policy.tf already exists, the script will append to the file.
