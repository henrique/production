#!/usr/bin/env python3
import argparse
import string
import sys
import re

tc_pattern = re.compile("toolchain\s*=\s*\{'name':\s*'(\S*)',\s*'version'\s*:\s*'(\S*)'\s*}")

dep_regex = lambda mod: f"(\s*)('({mod})'\s*,\s*EXTERNAL_MODULE\s*),"
dep_pattern = re.compile(dep_regex('\S*')) # any module


def parse_tc(file):
    ''' determine toolchain information in supplied EasyBuild config '''
    matches = re.search(tc_pattern, file)

    if matches:
        print("found matches from the config: ", matches.group())
        print("found original toolchain in config: ", matches.group(1))
        print("found original toolchain version in config: ", matches.group(2))
    else:
        raise RuntimeError(f"Couldn't determine toolchain information in supplied EasyBuild config.")

    return matches.group(1), matches.group(2)


def parse_metadata(metadata):
    ''' load a version map of every module in the given metadata '''
    modules = {}
    for line in metadata.readlines():
        if line[0] == '[':
            module = line[1:line.find(']')]
            module = module.split('/')
            module, version = module if len(module) > 1 else (module[0], None)
            modules[module] = version
    return modules


def main():
    parser = argparse.ArgumentParser(description='Switch toolchain to.')

    parser.add_argument('--debug',
                        type=bool, default=False,
                        help="Print verbose info.")

    parser.add_argument('--toolchain-prefix',
                        required=False,
                        help="Toolchain prefix for validation.")

    parser.add_argument('--version',
                        required=True,
                        help="New toolchain version to use.")

    parser.add_argument('--metadata',
                        type=argparse.FileType('r'), required=False,
                        help="Target metadata.")

    # parser.add_argument('--former-cdt',
    #                     type=argparse.FileType('r'), required=False,
    #                     help="Old CDT modulesrc.")

    parser.add_argument('--filenames',
                        nargs='+', required=True,
                        help="Files to process.")

    args = vars(parser.parse_args())

    if args['debug']:
        print(args)
        print(f"New toolchain is set {args['toolchain_prefix']}*-{args['version']}")

    if args['metadata']:
        modules = parse_metadata(args['metadata'])
        if args['debug']:
            print('metadata:', modules)

    for filename in args['filenames']:
        if args['debug']:
            print(f"Will use EasyBuild config {filename}.")
            print("The new config will be placed in original directory.")

        with open(filename, "r") as originalconfig:
            ec = originalconfig.read()  # contains newlines.
        if args['debug']:
            print("---- The original config was:\n", ec)

        toolchain, version = parse_tc(ec)

        if ('toolchain_prefix' in args) and not toolchain.startswith(args['toolchain_prefix']):
            sys.exit("Invalid toolchain prefix.")

        newecfilename = filename.replace(f"{toolchain}-{version}",
                                         f"{toolchain}-{args['version']}")
        if args['debug']:
            print("New config file name will be: ", newecfilename)

        newec = re.sub(tc_pattern,
                       f"toolchain = {{'name': '{toolchain}', 'version': '{args['version']}'}}",
                       ec)
        if args['debug']:
            print("---- New config will be:\n", newec)

        ## Check new toolchain
        _, version = parse_tc(newec)
        if version != args['version']:
            sys.exit("Failed to replace toolchain version.")

        with open(newecfilename, "w") as newconfig:
            newconfig.write(newec)  # contains newlines.

        print("Finished writing new config:", newecfilename)


if __name__ == "__main__":
    main()
