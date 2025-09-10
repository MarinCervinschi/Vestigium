import sys
from typing import List

from src.commands.init import cmd_init
from src.commands.add import cmd_add
from src.commands.commit import cmd_commit
from src.commands.ls_files import cmd_ls_files
from src.commands.cat_file import cmd_cat_file
from src.commands.hash_object import cmd_hash_object
from src.commands.log import cmd_log
from src.commands.ls_tree import cmd_ls_tree
from src.commands.checkout import cmd_checkout
from src.commands.rm import cmd_rm
from src.commands.status import cmd_status
from src.commands.check_ignore import cmd_check_ignore
from src.commands.tag import cmd_tag
from src.commands.rev_parse import cmd_rev_parse
from src.commands.show_ref import cmd_show_ref
from src.cli import get_parser

argparser = get_parser()


def main(argv: List[str] = sys.argv[1:]) -> None:
    args = argparser.parse_args(argv)
    match args.command:
        case "add":
            cmd_add(args)
        case "cat-file":
            cmd_cat_file(args)
        case "check-ignore":
            cmd_check_ignore(args)
        case "checkout":
            cmd_checkout(args)
        case "commit":
            cmd_commit(args)
        case "hash-object":
            cmd_hash_object(args)
        case "init":
            cmd_init(args)
        case "log":
            cmd_log(args)
        case "ls-files":
            cmd_ls_files(args)
        case "ls-tree":
            cmd_ls_tree(args)
        case "rev-parse":
            cmd_rev_parse(args)
        case "rm":
            cmd_rm(args)
        case "show-ref":
            cmd_show_ref(args)
        case "status":
            cmd_status(args)
        case "tag":
            cmd_tag(args)
        case _:
            print("Bad command.")
