# Repository Architecture

> **📍 Navigation**: [📚 Docs Home](README.md) | **📖 Next**: [Objects](OBJECTS.md) | **🔗 Related**: [Index](INDEX.md), [Refs](REFS.md)

## 📋 Table of Contents

- [🎯 Introduction](#-introduction)
- [🏗️ Git's Repository Concept](#-gits-repository-concept)
- [🔧 VesRepository Implementation](#-vesrepository-implementation)
- [🚀 Repository Initialization](#-repository-initialization)
- [🔍 Repository Discovery](#-repository-discovery)
- [🔄 Role in Git Workflow](#-role-in-git-workflow)
- [🎓 Design Insights](#-design-insights)

---

## 🎯 Introduction

The **repository** is the foundation of every version control system. In Git, everything revolves around the `.git` directory - in Vestigium this is called `.ves` to distinguish it from the original. This document explains the core concepts behind Git's repository structure and how they enable version control operations.

## 🏗️ Git's Repository Concept

### The Core Idea: Everything is Data

Git's brilliance lies in treating **everything as data stored in a database**. Your entire project history - files, directories, commits, branches - are all just different types of objects stored in a simple directory structure.

### The Directory Structure

```
.ves/                    # The repository database
├── objects/             # Content-addressable object store
├── refs/                # Named pointers to important commits
│   ├── heads/          # Branch pointers
│   └── tags/           # Tag pointers
├── HEAD                # Current position indicator
├── config              # Repository settings
└── index               # Staging area (when present)
```

### Why This Structure Works

- **`objects/`**: The heart of Git - a content-addressable database where every piece of content gets a unique SHA-1 hash
- **`refs/`**: Human-readable names that point to specific commits (branches and tags)
- **`HEAD`**: A special pointer that tracks "where you are" in the repository
- **`index`**: The staging area that sits between your working directory and commits

## 🔄 Role in Git's Flow

### The Three Trees Concept

Git operates on three main areas:

1. **Working Directory** (worktree): Where you edit files
2. **Staging Area** (index): Where you prepare commits
3. **Repository** (.ves): Where commits are permanently stored

The repository serves as the **permanent storage layer** - once something is committed here, it becomes part of the project's immutable history.

### Repository as the Source of Truth

Every Git operation ultimately reads from or writes to the repository:

- **`git add`** → Prepares objects for the repository
- **`git commit`** → Writes new objects to the repository
- **`git checkout`** → Reads objects from the repository
- **`git merge`** → Combines repository objects (not shown in Vestigium yet)
- **`git log`** → Traverses repository history

## 🔧 Core Implementation

### The VesRepository Class

```python
@dataclass
class VesRepository:
    _worktree: str      # Working directory path
    _vesdir: str        # Repository database path (.ves)
    _conf: ConfigParser # Repository configuration
```

This class represents the connection between the working directory and the version control database. It provides the foundation for all other Git operations.

### Repository Initialization

When creating a repository, the essential structure must be established:

```python
def repo_create(path: str) -> VesRepository:
    # Create directory structure
    assert repo_dir(repo, "objects", mkdir=True)      # Object database
    assert repo_dir(repo, "refs", "heads", mkdir=True) # Branch storage
    assert repo_dir(repo, "refs", "tags", mkdir=True)  # Tag storage

    # Initialize HEAD to point to master branch
    with open(head_path, "w") as f:
        f.write("ref: refs/heads/master\n")
```

The key insight: **a repository is just a directory structure with specific meaning**. The magic happens in how objects are stored and referenced within this structure.

## 🕵️ Repository Discovery

### The Git Workspace Concept

One of Git's most elegant features: **commands work from anywhere within a project**. This is enabled by the repository discovery mechanism.

```python
def repo_find(path: str = ".", required: bool = True) -> Optional[VesRepository]:
    path = os.path.realpath(path)

    # Look for .ves in current directory
    if os.path.isdir(os.path.join(path, ".ves")):
        return VesRepository(path)

    # Search upward through parent directories
    parent = os.path.realpath(os.path.join(path, ".."))
    if parent == path:  # Reached filesystem root
        return None if not required else raise Exception("No ves directory.")

    return repo_find(parent, required)  # Recursive search
```

### Why This Matters

This discovery pattern enables Git's **workspace concept**: any directory containing a `.git` folder (and all its subdirectories) becomes a Git workspace. You can run `git status` from `project/src/components/` and Git automatically finds the repository in `project/.git`.

## 🎯 Repository Validation

### Ensuring Compatibility

The repository validates its format to ensure compatibility:

```python
# Only support Git's standard format
vers = int(self._conf.get("core", "repositoryformatversion"))
if vers != 0:
    raise Exception(f"Unsupported repositoryformatversion: {vers}")
```

This ensures that Vestigium repositories remain compatible with Git's object format and can be inspected with standard Git tools.

## 🔄 Integration with Git Operations

### The Repository as Foundation

Every Git operation depends on the repository:

- **Object Storage**: All content (blobs, trees, commits) gets stored in `objects/`
- **Reference Management**: Branch and tag pointers stored in `refs/`
- **Configuration**: Repository-specific settings in `config`
- **State Tracking**: Current position via `HEAD`

The repository provides the **persistent layer** that makes version control possible. Without it, Git would just be a file copying tool.

### Working with Other Components

The repository integrates with other Git components:

- **Index**: Uses repository to validate and store staged changes
- **Objects**: Stored within repository's object database
- **References**: Managed within repository's refs structure
- **Configuration**: Repository settings affect all operations

The repository is the **coordination point** where all Git concepts come together to create a coherent version control system.

---

> **📍 Navigation**: [📚 Docs Home](README.md) | **📖 Next**: [Objects](OBJECTS.md) | **🔗 Related**: [Index](INDEX.md), [Refs](REFS.md)
