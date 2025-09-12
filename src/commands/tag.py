from argparse import Namespace

from src.commands.show_ref import show_ref
from src.core.refs import RefDict, ref_list, tag_create
from src.core.repository import repo_find


def cmd_tag(args: Namespace) -> None:
    """CLI command to create or list Ves tags.

    This command provides the interface for tag management in Ves. It can either
    create new tags (lightweight or annotated) or list existing tags in the
    repository. The behavior depends on whether a tag name is provided.

    Args:
        args (Namespace): Command line arguments containing:
            - name (Optional[str]): Name of the tag to create. If None, lists tags
            - object (str): Target object/commit for the new tag (used when name is provided)
            - create_tag_object (bool): Whether to create an annotated tag object
                                      or a lightweight tag reference

    Returns:
        None: Either creates a new tag or prints the list of existing tags

    Behavior:
        - If args.name is provided: Creates a new tag pointing to args.object
        - If args.name is None: Lists all existing tags in the repository

    Tag creation modes:
        - Lightweight tag (create_tag_object=False): Simple reference to commit
        - Annotated tag (create_tag_object=True): Full tag object with metadata

    Example:
        $ ves tag                          # List all tags
        $ ves tag v1.0 abc123             # Create lightweight tag
        $ ves tag -a v1.1 def456          # Create annotated tag

    Note:
        The function silently returns if not in a Ves repository.
        Tag listing shows tags without their SHA hashes for cleaner output.
    """
    repo = repo_find()
    if repo is None:
        return

    if args.name:
        tag_create(
            repo, args.name, args.object, create_tag_object=args.create_tag_object
        )
    else:
        refs = ref_list(repo)
        assert type(refs["tags"]) is RefDict
        show_ref(repo, refs["tags"], with_hash=False)
