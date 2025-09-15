# Vestigium Commands Guide

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Ignore](IGNORE.md) | **� Related**: [Repository](REPOSITORY.md), [Objects](OBJECTS.md), [Index](INDEX.md), [Refs](REFS.md), [Tree](TREE.md)

---

A quick guide to the available commands in Vestigium, the educational version control system.

## 📋 Table of Contents

- [Basic Commands](#basic-commands)
- [Index Management](#index-management)
- [Viewing and Navigation](#viewing-and-navigation)
- [Objects and Hashing](#objects-and-hashing)
- [References and Tags](#references-and-tags)
- [Utilities and Debug](#utilities-and-debug)

---

## 🚀 Basic Commands

### `init` - Initialize Repository

**Purpose**: Creates a new empty Vestigium repository.

**Syntax**:

```bash
ves init [directory]
```

**How it works**:

- Creates the `.ves/` structure with `objects/`, `refs/`, `branches/` directories
- Sets up default configuration files (`HEAD`, `config`, `description`)
- If not specified, uses the current directory

**Example**:

```bash
ves init                    # Initialize in current directory
ves init /path/to/project   # Initialize in specific directory
```

---

## 📝 Index Management

### `add` - Add Files to Index

**Purpose**: Adds files to the staging area (index) to prepare them for commit.

**Syntax**:

```bash
ves add <file1> [file2] [...]
```

**How it works**:

1. Removes any existing entries for the specified files
2. Computes SHA hash of content and saves it as blob object
3. Collects filesystem metadata (timestamps, permissions, size)
4. Creates new index entries with all metadata
5. Writes updated index to disk

**Example**:

```bash
ves add file.txt           # Add a single file
ves add *.py               # Add all Python files
ves add file1.txt file2.txt # Add multiple files
```

**Notes**: Files must exist and be within the repository worktree.

### `rm` - Remove Files from Index

**Purpose**: Removes files from the index and optionally from the filesystem.

**Syntax**:

```bash
ves rm <file1> [file2] [...]
```

**How it works**:

1. Validates that paths are within the worktree
2. Finds corresponding entries in the index
3. Removes entries from the index
4. Deletes physical files from disk (default behavior)
5. Writes updated index

**Example**:

```bash
ves rm file.txt           # Remove file from index and disk
ves rm *.tmp              # Remove all temporary files
```

**Notes**: After `rm`, the file will appear as "deleted" in `status` until you commit.

### `commit` - Record Changes

**Purpose**: Creates a commit with the changes currently in the index.

**Syntax**:

```bash
ves commit -m "message"
```

**How it works**:

1. Reads current index and creates tree object from structure
2. Retrieves author information from user configuration
3. Creates commit object with tree, parent, author, timestamp and message
4. Updates HEAD or active branch with new commit SHA

**Example**:

```bash
ves commit -m "Add new feature"
ves commit -m "Fix bug in parser"
```

**Notes**: Requires user configuration (`user.name` and `user.email`).

---

## 👁️ Viewing and Navigation

### `status` - Repository Status

**Purpose**: Shows the current state of the working tree and index.

**Syntax**:

```bash
ves status
```

**How it works**:

- **Current branch**: Shows which branch you're on or if HEAD is detached
- **Changes to be committed**: Differences between HEAD and index (staged changes)
- **Changes not staged**: Differences between index and working tree
- **Untracked files**: Files in worktree not present in index

**Typical output**:

```
On branch master.
Changes to be committed:
  added:    new_file.txt
  modified: existing_file.txt
  deleted:  old_file.txt

Changes not staged for commit:
  modified: modified_file.txt

Untracked files:
  untracked_file.txt
```

### `log` - Commit History

**Purpose**: Displays commit history in Graphviz graph format.

**Syntax**:

```bash
ves log [commit]
```

**How it works**:

- Generates a directed graph of commits starting from specified commit (default: HEAD)
- Follows parent-child relationships to build complete history
- Outputs in DOT format for Graphviz visualization

**Example**:

```bash
ves log                    # History from HEAD
ves log abc123             # History from specific commit
ves log | dot -Tpng > history.png  # Generate image
```

>**Notes**: Or paste the output into [GraphvizOnline](https://dreampuf.github.io/GraphvizOnline) to visualize directly.

### `checkout` - Extract Commit

**Purpose**: Extracts all files from a commit/tree to a directory.

**Syntax**:

```bash
ves checkout <commit> <directory>
```

**How it works**:

1. Resolves the specified commit/tree object
2. Verifies that destination directory is empty
3. Recursively extracts all files and subdirectories
4. Writes blobs as physical files to filesystem

**Example**:

```bash
ves checkout HEAD /tmp/current     # Extract current commit
ves checkout abc123 /tmp/old       # Extract specific commit
```

**Notes**: Directory must be empty or non-existent.

---

## 🔍 Objects and Hashing

### `hash-object` - Calculate File Hash

**Purpose**: Calculates SHA hash of a file and optionally saves it to repository.

**Syntax**:

```bash
ves hash-object [-t type] [-w] <file>
```

**Options**:

- `-t type`: Specify object type (blob, commit, tree, tag) - default: blob
- `-w`: Actually write the object to repository database

**How it works**:

1. Reads file content
2. Creates object of specified type
3. Calculates SHA-1 hash
4. If `-w` specified, compresses and saves to `.ves/objects/`

**Example**:

```bash
ves hash-object file.txt           # Only calculate hash
ves hash-object -w file.txt        # Calculate and save to repo
ves hash-object -t commit msg.txt  # Treat as commit object
```

### `cat-file` - Display Object Content

**Purpose**: Shows the content of a repository object.

**Syntax**:

```bash
ves cat-file <type> <object>
```

**How it works**:

1. Resolves object using provided name/hash
2. Reads and decompresses object from database
3. Verifies type if specified
4. Prints serialized content to stdout

**Example**:

```bash
ves cat-file blob abc123           # Show blob content
ves cat-file commit HEAD           # Show current commit details
ves cat-file tree HEAD^{tree}      # Show directory structure
```

---

## 🏷️ References and Tags

### `tag` - Tag Management

**Purpose**: Creates and lists tags to mark specific commits.

**Syntax**:

```bash
ves tag                            # List all tags
ves tag <name> [object]            # Create lightweight tag
ves tag -a <name> [object]         # Create annotated tag
```

**How it works**:

- **List tags**: Shows all tags in `refs/tags/`
- **Lightweight tag**: Creates simple reference to commit
- **Annotated tag**: Creates complete tag object with metadata

**Example**:

```bash
ves tag                            # v1.0, v2.0, beta
ves tag v1.1                       # Lightweight tag on HEAD
ves tag -a v2.0 abc123             # Annotated tag on specific commit
```

### `show-ref` - Show References

**Purpose**: Lists all repository references with their hashes.

**Syntax**:

```bash
ves show-ref
```

**How it works**:

- Recursively traverses the `refs/` directory
- Resolves each reference to its final SHA
- Shows hierarchical structure of references

**Typical output**:

```
abc123... refs/heads/master
def456... refs/heads/develop
789abc... refs/tags/v1.0
012def... refs/remotes/origin/master
```

### `rev-parse` - Resolve Identifiers

**Purpose**: Converts names/references to complete SHA hashes.

**Syntax**:

```bash
ves rev-parse [--ves-type type] <name>
```

**How it works**:

- Resolves symbolic references (HEAD, branch names, tag names)
- Expands partial hashes to complete hashes
- Optionally verifies object type

**Example**:

```bash
ves rev-parse HEAD                 # SHA of current commit
ves rev-parse master               # SHA of master branch
ves rev-parse abc123               # Expand partial hash
```

---

## 🔧 Utilities and Debug

### `ls-files` - List Files in Index

**Purpose**: Shows all files currently tracked in the index.

**Syntax**:

```bash
ves ls-files [--verbose]
```

**How it works**:

- Reads index and shows all tracked files
- With `--verbose`: shows complete metadata (timestamps, permissions, SHA, etc.)

**Example**:

```bash
ves ls-files                       # Simple list
ves ls-files --verbose             # Complete details
```

**Verbose output**:

```
file.txt
  regular file with perms: 644
  on blob: abc123...
  created: 2025-01-15 10:30:00.123
  device: 2049, inode: 12345
  user: mario (1000)  group: staff (20)
```

### `ls-tree` - List Tree Contents

**Purpose**: Shows the content of a tree object in readable format.

**Syntax**:

```bash
ves ls-tree [-r] <tree>
```

**Options**:

- `-r`: Recursively show subdirectory contents

**How it works**:

1. Resolves specified tree object
2. Reads tree entries (mode, type, SHA, name)
3. If recursive, also traverses subtrees

**Example**:

```bash
ves ls-tree HEAD                   # Root directory content
ves ls-tree -r HEAD                # All files recursively
ves ls-tree abc123^{tree}          # Tree of specific commit
```

**Output**:

```
100644 blob abc123... file.txt
040000 tree def456... src/
100755 blob 789abc... script.sh
```

### `check-ignore` - Verify Ignore Rules

**Purpose**: Checks if certain paths are ignored by ignore rules.

**Syntax**:

```bash
ves check-ignore <path1> [path2] [...]
```

**How it works**:

1. Reads ignore rules from `.ves/info/exclude`, `~/.config/ves/ignore`, and `.vesignore`
2. Evaluates each path against all rules
3. Prints only paths that are ignored

**Example**:

```bash
ves check-ignore *.tmp build/ test.log
# Output: build/ test.log (if ignored)
```

---

## 📚 General Notes

### Required Configuration

Some commands require user configuration:

```bash
# In ~/.vesconfig or ~/.config/ves/config
[user]
name = Mario Rossi
email = mario.rossi@example.com
```

### Object Format

Vestigium supports four object types:

- **blob**: File content
- **tree**: Directory structure
- **commit**: Snapshot with metadata
- **tag**: Annotated reference

### Typical Workflow

```bash
ves init                           # Initialize repo
ves add file.txt                   # Add file
ves commit -m "Initial commit"     # Create commit
ves status                         # Check status
ves log                            # View history
ves tag v1.0                       # Mark version
```

### Compatibility

Vestigium uses formats compatible with Git for:

- Object storage (blob, tree, commit, tag)
- Index file format
- References structure
- SHA-1 hashing

This allows limited interoperability with standard Git tools for inspection and debugging.

---

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Ignore](IGNORE.md) | **🔗 Related**: [Repository](REPOSITORY.md), [Objects](OBJECTS.md), [Index](INDEX.md), [Refs](REFS.md), [Tree](TREE.md)
