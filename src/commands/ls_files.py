import grp
import pwd
from argparse import Namespace
from datetime import datetime

from src.core.index import index_read
from src.core.repository import repo_find

ENTRY_TYPE = {
    0b1000: "regular file",
    0b1010: "symlink",
    0b1110: "git link",
}


def cmd_ls_files(args: Namespace) -> None:
    """
    Lists files tracked in the repository index.

    If the repository or index cannot be found, the function returns early.
    In verbose mode, prints detailed information about each index entry, including:
        - Entry type and permissions
        - Blob SHA
        - Creation and modification timestamps
        - Device and inode numbers
        - User and group names and IDs
        - Entry flags (stage and assume_valid)

    Args:
        args (Namespace): Command-line arguments, expects a 'verbose' attribute to control output verbosity.

    Returns:
        None
    """
    repo = repo_find()
    if repo is None:
        return
    index = index_read(repo)

    for e in index.entries:
        print(e.name)
        if args.verbose:
            if e.mode_type is not None:
                entry_type = ENTRY_TYPE[e.mode_type]

            if e.ctime is not None and e.mtime is not None:
                created = f"{datetime.fromtimestamp(e.ctime[0])}.{e.ctime[1]}"
                modified = f"{datetime.fromtimestamp(e.mtime[0])}.{e.mtime[1]}"

            if e.uid is not None and e.gid is not None:
                uid = pwd.getpwuid(e.uid).pw_name
                gid = grp.getgrgid(e.gid).gr_name

            print(f"  {entry_type} with perms: {e.mode_perms:o}")
            print(f"  on blob: {e.sha}")
            print(f"  created: {created}, modified: {modified}")
            print(f"  device: {e.dev}, inode: {e.ino}")
            print(f"  user: {uid} ({e.uid})  group: {gid} ({e.gid})")
            print(f"  flags: stage={e.flag_stage} assume_valid={e.flag_assume_valid}")
