import sys
from typing import List

from src.cli import get_parser

argparser = get_parser()


def main(argv: List[str] = sys.argv[1:]) -> None:
    args = argparser.parse_args(argv)
    match args.command:
        case "add":
            from src.commands.add import cmd_add

            cmd_add(args)
        case "cat-file":
            from src.commands.cat_file import cmd_cat_file

            cmd_cat_file(args)
        case "check-ignore":
            from src.commands.check_ignore import cmd_check_ignore

            cmd_check_ignore(args)
        case "checkout":
            from src.commands.checkout import cmd_checkout

            cmd_checkout(args)
        case "commit":
            from src.commands.commit import cmd_commit

            cmd_commit(args)
        case "hash-object":
            from src.commands.hash_object import cmd_hash_object

            cmd_hash_object(args)
        case "init":
            from src.commands.init import cmd_init

            cmd_init(args)
        case "log":
            from src.commands.log import cmd_log

            cmd_log(args)
        case "ls-files":
            from src.commands.ls_files import cmd_ls_files

            cmd_ls_files(args)
        case "ls-tree":
            from src.commands.ls_tree import cmd_ls_tree

            cmd_ls_tree(args)
        case "rev-parse":
            from src.commands.rev_parse import cmd_rev_parse

            cmd_rev_parse(args)
        case "rm":
            from src.commands.rm import cmd_rm

            cmd_rm(args)
        case "show-ref":
            from src.commands.show_ref import cmd_show_ref

            cmd_show_ref(args)
        case "status":
            from src.commands.status import cmd_status

            cmd_status(args)
        case "tag":
            from src.commands.tag import cmd_tag

            cmd_tag(args)
        case _:
            print("Bad command.")
