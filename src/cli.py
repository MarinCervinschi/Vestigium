from argparse import ArgumentParser


def get_parser() -> ArgumentParser:
    """
    Builds and returns the ArgumentParser configured for the Vestigium CLI.

    The parser includes all supported commands and their arguments.

    Returns:
        ArgumentParser: The configured argument parser for the CLI.
    """
    argparser = ArgumentParser(description="Vestigium - A Version Control System")
    argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
    argsubparsers.required = True

    # init
    argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
    argsp.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Where to create the repository.",
    )

    return argparser
