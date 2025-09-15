# Index System - Git's Staging Area

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Objects](OBJECTS.md) | **📖 Next**: [Refs](REFS.md) | **🔗 Related**: [Repository](REPOSITORY.md), [Tree](TREE.md)

## 📋 Table of Contents

- [🎯 Introduction](#-introduction)
- [🏗️ What is the Index?](#️-what-is-the-index)
- [📊 Index Entry Structure](#-index-entry-structure)
- [🔄 Index Binary Format](#-index-binary-format)
- [🚀 Role in Git Workflow](#-role-in-git-workflow)
- [🎯 Advanced Index Features](#-advanced-index-features)
- [🎓 Design Insights](#-design-insights)

---

## 🎯 Introduction

The **index** (also called "staging area") is Git's intermediate layer between the working directory and the repository. It's one of Git's most distinctive features and the key to understanding how Git prepares commits. This document explains how Vestigium implements Git's index system and why it's crucial to Git's workflow.

## 🏗️ What is the Index?

The index is a **snapshot preparation area** that holds the exact content intended for the next commit. Unlike many VCS systems that commit directly from working directory, Git uses a three-stage model:

```
Working Directory → Index (Staging) → Repository
    (files you edit)  (prepared commit)  (committed history)
```

### The Three-Tree Architecture

1. **Working Directory**: Files as you see and edit them
2. **Index**: Staged files prepared for commit  
3. **HEAD**: Last committed snapshot

This separation enables:
- **Selective staging**: Choose exactly which changes to commit
- **Atomic commits**: All staged changes become one commit
- **Conflict resolution**: Merge states tracked during operations
- **Performance**: Fast status checks without scanning files

## 📊 Index Entry Structure

### Complete File Metadata

Each index entry contains **comprehensive file metadata**:

```python
@dataclass
class VesIndexEntry:
    # Timestamps
    ctime: Tuple[int, int]          # Creation time (seconds, nanoseconds)
    mtime: Tuple[int, int]          # Modification time (seconds, nanoseconds)
    
    # Filesystem metadata
    dev: int                        # Device ID  
    ino: int                        # Inode number
    mode_type: int                  # File type (regular, symlink, gitlink)
    mode_perms: int                 # Permissions (644, 755, etc.)
    uid: int                        # User ID
    gid: int                        # Group ID
    fsize: int                      # File size
    
    # Version control data
    sha: str                        # SHA hash of content
    flag_assume_valid: bool         # Skip file checks optimization
    flag_stage: int                 # Merge conflict stage (0-3)
    name: str                       # File path from repo root
```

### Why So Much Metadata?

Git stores **complete filesystem metadata** to enable:

- **Change detection**: Compare current file stats vs index stats
- **Fast status**: Avoid reading file content when metadata unchanged
- **Merge tracking**: Handle three-way merges with stage flags
- **Cross-platform**: Preserve permissions and ownership info
- **Optimization**: Skip expensive operations when safe

## 🔄 Index Binary Format

### File Structure

The index file (`.ves/index`) uses a compact binary format:

```
┌─────────────────┐
│ Header (12B)    │ ← Magic "DIRC" + version + count
├─────────────────┤
│ Entry 1         │ ← Fixed 62B + variable name + padding
├─────────────────┤
│ Entry 2         │ ← Fixed 62B + variable name + padding  
├─────────────────┤
│ ...             │
└─────────────────┘
```

### Header Format
- **Bytes 0-3**: Magic signature `"DIRC"` (Directory Cache)
- **Bytes 4-7**: Version number (2)
- **Bytes 8-11**: Number of entries

### Entry Format
- **62 bytes**: Fixed metadata (timestamps, filesystem info, SHA, flags)
- **Variable**: Null-terminated filename
- **Padding**: Align to 8-byte boundaries for performance

## 🚀 Role in Git Workflow

### Adding Files (`ves add`)

```bash
ves add file.txt
```

1. **Read file content** from working directory
2. **Create blob object** and calculate SHA
3. **Collect metadata** (timestamps, permissions, size)
4. **Create index entry** with all metadata + SHA
5. **Update index** by adding/replacing entry
6. **Write index file** to disk

The file is now **staged** - ready for commit but not yet committed.

### Status Checking (`ves status`)

```bash
ves status
```

Git performs **three comparisons**:

#### 1. **HEAD vs Index** (Changes to be committed)
- Compare commit tree vs index entries
- Shows: new files, deleted files, modified content

#### 2. **Index vs Working Directory** (Changes not staged)
- Compare index metadata vs current file stats
- If metadata differs: compare content hashes
- Shows: modified files, new files, deleted files

#### 3. **Working Directory scan** (Untracked files)
- Find files not in index
- Exclude ignored files
- Shows: new files not yet added

### Committing (`ves commit`)

```bash
ves commit -m "Add feature"
```

1. **Read current index** entries
2. **Build tree objects** from index structure
3. **Create commit object** pointing to root tree
4. **Update branch reference** to new commit
5. **Index unchanged** - still contains same staged content

Key insight: **Commit snapshots the index**, not the working directory.

### Resetting (`ves reset`) (not in Vestigium yet)

Different reset modes manipulate the three trees differently:

- **`--soft`**: Move HEAD only (repository changes)
- **`--mixed`** (default): Move HEAD + reset index (unstage changes)  
- **`--hard`**: Move HEAD + reset index + reset working directory

## 🎯 Advanced Index Features

### Merge Conflict Resolution (not in Vestigium yet)

During merges, the index uses **stage flags**:

- **Stage 0**: Normal, no conflict
- **Stage 1**: Common ancestor (base)
- **Stage 2**: "Ours" (current branch)
- **Stage 3**: "Theirs" (merging branch)

When conflicts occur, Git stores all three versions in the index, allowing tools to perform three-way merges.

### Performance Optimizations

#### 1. **Assume Valid Flag**
```python
flag_assume_valid: bool
```
When set, Git skips checking if file changed. Used for large files that rarely change.

#### 2. **Stat Matching**
If file metadata (timestamps, size, inode) unchanged, Git assumes content unchanged. Avoids expensive SHA calculations.

#### 3. **Binary Format**
Compact binary storage enables fast loading/saving of large indexes.

## 🎓 Design Insights

### Why the Index Exists

The staging area solves several fundamental problems:

#### 1. **Atomic Commits**
- **Problem**: How to commit some changes but not others?
- **Solution**: Stage exactly what you want, commit the stage

#### 2. **Commit Preparation**  
- **Problem**: How to review changes before committing?
- **Solution**: Stage changes, review staging area, then commit

#### 3. **Merge Resolution**
- **Problem**: How to handle conflicted merges?
- **Solution**: Store multiple versions in index stages

#### 4. **Performance**
- **Problem**: How to quickly detect file changes?
- **Solution**: Cache metadata and compare stats first

### The Index as State Machine

The index represents Git's **preparation state**:

```
Working Directory ─add→ Index ─commit→ Repository
        ↑                 ↓
        └─────checkout─────┘
```

- **Working Directory**: Your current workspace
- **Index**: Your intended next commit
- **Repository**: Your permanent history

### Content vs Metadata

Git separates:
- **Content identity**: SHA hash (immutable, content-addressable)
- **Content metadata**: Filename, permissions, timestamps (mutable, in index)

This separation enables:
- **File moves**: Same content, different path
- **Permission changes**: Same content, different mode
- **Rename detection**: Content hash unchanged, path changed

The index is Git's **preparation workspace** - the place where commits are carefully crafted before being made permanent. It transforms Git from a simple "save snapshot" system into a sophisticated "prepare and commit" workflow that gives developers precise control over their version history.

---

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Objects](OBJECTS.md) | **📖 Next**: [Refs](REFS.md) | **🔗 Related**: [Repository](REPOSITORY.md), [Tree](TREE.md)