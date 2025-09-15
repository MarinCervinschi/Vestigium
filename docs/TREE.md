# Tree Operations - Git's Directory Structure

## 🎯 Introduction

**Tree operations** are essential utilities for manipulating Git's directory structure representation. While the core `VesTree` object handles basic tree storage, these utilities provide the complex algorithms needed to convert between different representations: index entries to tree objects, tree objects to filesystem directories, and tree hierarchies to flat dictionaries.

## 🌳 Tree Structure Fundamentals

### What Trees Represent

In Git, **trees are directories**. Each tree object contains entries that point to:
- **Blobs** (files) with names and permissions
- **Subtrees** (subdirectories) with names

### Tree Entry Format

Each tree entry contains:
```python
class VesTreeLeaf:
    mode: bytes    # File permissions (100644, 100755, 040000)
    path: str      # File/directory name
    sha: str       # SHA hash of referenced object
```

### Mode Meanings
- `100644`: Regular file (rw-r--r--)
- `100755`: Executable file (rwxr-xr-x)
- `040000`: Directory (tree object)
- `120000`: Symbolic link
- `160000`: Git submodule

## 🔄 Key Tree Operations

### Index to Tree Conversion

#### The Challenge
The **index is flat** - a list of file paths with SHAs:
```
src/main.py -> abc123...
src/utils/helper.py -> def456...
docs/README.md -> 789abc...
```

But **trees are hierarchical**:
```
Root Tree
├── src/ (tree)
│   ├── main.py (blob)
│   └── utils/ (tree)
│       └── helper.py (blob)
└── docs/ (tree)
    └── README.md (blob)
```

#### `tree_from_index()` - The Algorithm

This function performs the critical **index → tree hierarchy** conversion:

##### 1. **Directory Grouping**
```python
contents: dict[str, list] = dict()
contents[""] = list()  # Root directory

for entry in index.entries:
    dirname = os.path.dirname(entry.name)
    # Group files by their directory
```

Groups index entries by directory path, creating a mapping like:
```python
{
    "": [docs/README.md],
    "src": [src/main.py],
    "src/utils": [src/utils/helper.py]
}
```

##### 2. **Bottom-Up Processing**
```python
sorted_paths = sorted(contents.keys(), key=len, reverse=True)
```

Processes directories from **deepest to shallowest**:
1. `src/utils/` → create tree with `helper.py`
2. `src/` → create tree with `main.py` + `utils/` subtree
3. `""` (root) → create tree with `src/` + `docs/` subtrees

##### 3. **Tree Object Creation**
For each directory:
- Create `VesTree` object
- Add file entries (from index)
- Add subdirectory entries (from previously created trees)
- Write tree object to repository
- Return SHA for parent directory to reference

#### Why Bottom-Up?

To create a tree that references subtrees, the **subtrees must exist first**. The algorithm ensures child trees are created before parent trees reference them.

### Tree to Dictionary Flattening

#### `tree_to_dict()` - Hierarchical to Flat

This function **flattens tree hierarchy** into a simple path→SHA mapping:

```python
def tree_to_dict(repo: VesRepository, ref: str, prefix: str = "") -> dict[str, str]:
```

##### The Algorithm
1. **Read tree object** from repository
2. **For each entry**:
   - If **blob** → add `path: sha` to dictionary
   - If **tree** → recursively process subdirectory
3. **Return flat mapping** of all files

##### Example Output
```python
{
    "src/main.py": "abc123...",
    "src/utils/helper.py": "def456...", 
    "docs/README.md": "789abc..."
}
```

#### Use Cases
- **Status comparison**: Compare two tree states efficiently
- **Diff generation**: Find added/deleted/modified files
- **Merge algorithms**: Three-way merge requires flat file lists

### Tree Checkout

#### `tree_checkout()` - Tree to Filesystem

This function **materializes a tree** in the filesystem:

```python
def tree_checkout(repo: VesRepository, tree: VesTree, path: str) -> None:
```

##### The Algorithm
1. **For each tree entry**:
   - Read the referenced object
   - Determine destination path
2. **If object is tree**:
   - Create directory
   - Recursively checkout subtree
3. **If object is blob**:
   - Write blob content to file

This is the core operation behind `git checkout` - extracting a commit's tree structure to the working directory.

## 🎯 Role in Git Workflow

### During Commit Creation

```bash
ves commit -m "Add feature"
```

1. **Read current index** (staged files)
2. **Convert index to tree hierarchy** with `tree_from_index()`
3. **Get root tree SHA** 
4. **Create commit object** pointing to root tree
5. **Write commit to repository**

The index→tree conversion is **critical** - it transforms the flat staging area into the hierarchical snapshot that commits store.

### During Status Checking

```bash
ves status
```

Status checking requires comparing **three tree states**:

1. **HEAD tree** → `tree_to_dict(repo, "HEAD")`
2. **Index tree** → `tree_to_dict(repo, index_tree_sha)`  
3. **Working directory** → scan filesystem

By flattening all three to dictionaries, Git can efficiently:
- Find **staged changes**: HEAD vs Index differences
- Find **unstaged changes**: Index vs Working differences
- Find **untracked files**: Files in Working but not Index

### During Checkout

```bash
ves checkout branch-name
```

1. **Resolve branch** to commit SHA
2. **Get commit's tree** SHA
3. **Clear working directory**
4. **Checkout tree** with `tree_checkout()`
5. **Update HEAD** to point to branch

Tree checkout is how Git **reconstructs your workspace** from repository history.

## 🎓 Design Insights

### Why These Utilities Matter

The core Git objects (`VesTree`, `VesBlob`, etc.) handle **storage and retrieval**. These utilities handle **transformation algorithms**:

- **Index ↔ Tree**: Convert between flat and hierarchical representations
- **Tree ↔ Filesystem**: Convert between Git objects and actual files
- **Tree ↔ Dictionary**: Convert between hierarchical and flat for comparison

### Performance Considerations

#### Bottom-Up Tree Creation
Creating trees bottom-up ensures:
- **No duplicate work**: Each subtree created exactly once
- **Correct references**: Parent trees can reference child tree SHAs
- **Optimal ordering**: Deep directories processed first

#### Flat Dictionary Comparisons
Converting trees to dictionaries enables:
- **O(n) comparison**: Simple dictionary diff operations
- **Memory efficiency**: Single pass through tree hierarchy
- **Algorithm simplicity**: Standard set operations for differences

### The Tree Abstraction

Trees represent **directory snapshots** at specific points in time. The utilities enable Git to:

1. **Capture snapshots**: Index → Tree (during commit)
2. **Compare snapshots**: Tree → Dictionary (during status/diff)
3. **Restore snapshots**: Tree → Filesystem (during checkout)

This abstraction is fundamental to Git's model: **commits are snapshots**, and snapshots are represented as tree hierarchies. The utilities provide the essential algorithms for working with these hierarchical snapshots in practical Git operations.