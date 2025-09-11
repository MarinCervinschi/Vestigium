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

    # cat-file
    argsp = argsubparsers.add_parser(
        "cat-file", help="Provide content of repository objects"
    )

    argsp.add_argument(
        "type",
        metavar="type",
        choices=["blob", "commit", "tag", "tree"],
        help="Specify the type",
    )

    argsp.add_argument("object", metavar="object", help="The object to display")

    # hash-object
    argsp = argsubparsers.add_parser(
        "hash-object",
        help="Compute object ID and optionally creates a blob from a file",
    )

    argsp.add_argument(
        "-t",
        metavar="type",
        dest="type",
        choices=["blob", "commit", "tag", "tree"],
        default="blob",
        help="Specify the type",
    )

    argsp.add_argument(
        "-w",
        dest="write",
        action="store_true",
        help="Actually write the object into the database",
    )

    argsp.add_argument("path", help="Read object from <file>")

    return argparser
