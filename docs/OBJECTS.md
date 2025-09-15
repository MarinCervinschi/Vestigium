# Object System - Git's Core Data Model

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Repository](REPOSITORY.md) | **📖 Next**: [Index](INDEX.md) | **🔗 Related**: [Refs](REFS.md), [Tree](TREE.md)

## 📋 Table of Contents

- [🎯 Introduction](#-introduction)
- [🏗️ The Four Object Types](#️-the-four-object-types)
- [🔄 Object Storage and Retrieval](#-object-storage-and-retrieval)
- [🕵️ Object Resolution System](#️-object-resolution-system)
- [🎯 Content-Addressable Storage](#-content-addressable-storage)
- [🔗 Object Graph Relationships](#-object-graph-relationships)
- [🚀 Role in Git Workflow](#-role-in-git-workflow)
- [🎓 Design Insights](#-design-insights)

---

## 🎯 Introduction

The **object system** is Git's fundamental data storage mechanism. Everything in Git - files, directories, commits, tags - is stored as an object. This document explains how Vestigium implements Git's object model and how objects flow through the version control lifecycle.

## 🏗️ The Four Object Types

Git's genius lies in reducing all version control data to four simple object types:

### **Blob** - File Content
```python
class VesBlob(VesObject):
    fmt: ClassVar[bytes] = b"blob"
```

Stores raw file content with no metadata. Blobs are **content-addressable** - identical files produce identical SHA hashes regardless of filename or location.

### **Tree** - Directory Structure  
```python
class VesTree(VesObject):
    fmt: ClassVar[bytes] = b"tree"
```

Represents a directory, containing entries that point to blobs (files) and other trees (subdirectories). Each entry includes:
- File/directory name
- Permissions (644, 755, etc.)
- SHA hash of the referenced object

### **Commit** - Snapshots in Time
```python
class VesCommit(VesObject):
    fmt: ClassVar[bytes] = b"commit"
```

Captures a complete project snapshot with metadata:
- **Tree**: SHA pointing to the root directory
- **Parent(s)**: SHA(s) of previous commit(s)
- **Author/Committer**: Identity and timestamp
- **Message**: Description of changes

### **Tag** - Named References
```python
class VesTag(VesCommit):
    fmt: ClassVar[bytes] = b"tag"
```

Annotated tags that point to commits with additional metadata like tagger info and description.

## 🔄 Object Storage and Retrieval

### Storage Format

All objects follow Git's standard storage format:
```
{type} {size}\0{content}
```

The complete object is:
1. **SHA-1 hashed** to generate unique identifier
2. **zlib compressed** for storage efficiency  
3. **Stored** in `.ves/objects/{first2chars}/{remaining38chars}`

### Key Functions

#### `object_write()` - Persistence
```python
def object_write(obj: VesObject, repo: Optional[VesRepository] = None) -> str:
```

The core storage function that:
- Serializes object to bytes
- Calculates SHA-1 hash (the object's identity)
- Compresses and stores if repository provided
- Returns the SHA for referencing

#### `object_read()` - Retrieval
```python
def object_read(repo: VesRepository, sha: str) -> Optional[VesObject]:
```

Reverse of storage:
- Locates object file by SHA
- Decompresses zlib content
- Parses header to determine type
- Instantiates appropriate object class

## 🕵️ Object Resolution System

### The Challenge

Git allows flexible object referencing:
- Full SHA: `a1b2c3d4e5f6...` (40 chars)
- Short SHA: `a1b2c3d` (4+ chars)
- Branch names: `main`, `feature-xyz`
- Tag names: `v1.0`, `release-2024`
- Special refs: `HEAD`

### `object_resolve()` - The Name Resolver

```python
def object_resolve(repo: VesRepository, name: str) -> Optional[List[Optional[str]]]:
```

This function implements Git's sophisticated name resolution strategy:

#### 1. **HEAD Special Case**
```python
if name == "HEAD":
    return [ref_resolve(repo, "HEAD")]
```

HEAD is always resolved first as it's the most common reference.

#### 2. **SHA Hash Matching**
```python
if hashRE.match(name):
    # Search objects directory for matches
```

For SHA patterns (4-40 hex chars):
- Converts to lowercase for case-insensitive matching
- Uses directory structure optimization (first 2 chars = subdirectory)
- Supports partial matches (returns all possibilities)

#### 3. **Reference Resolution**
Checks in order:
- `refs/tags/{name}` - Tags first
- `refs/heads/{name}` - Local branches  
- `refs/remotes/{name}` - Remote branches (not in Vestigium yet)

#### 4. **Ambiguity Handling**
Returns **all** matches, letting calling code handle ambiguity. This is crucial for user experience - Git shows all possibilities when names conflict.

## 🎯 Content-Addressable Storage

### The Core Concept

Objects are identified by their **content hash**, not by name or location. This provides:

- **Deduplication**: Identical content = same SHA = single storage
- **Integrity**: Any content change = different SHA = corruption detection  
- **Immutability**: Objects never change (new content = new object)
- **Efficiency**: Only store unique content once

### Example Flow

1. **File Creation**: `hello.txt` with content "Hello World"
2. **Hash Calculation**: SHA-1 of blob = `557db03de997c86a4a028e1ebd3a1ceb225be238`
3. **Storage**: Content stored in `.ves/objects/55/7db03de997c86a4a028e1ebd3a1ceb225be238`
4. **Reference**: Tree object points to this blob with name "hello.txt"

If another file has identical content, it references the same blob object.

## 🔗 Object Graph Relationships

### The Commit Graph
```
Commit A ←─ Commit B ←─ Commit C (HEAD)
   │           │           │
   Tree 1      Tree 2      Tree 3
   │           │           │
 Blobs...    Blobs...    Blobs...
```

### Tree Hierarchy
```
Root Tree
├── file1.txt (blob)
├── file2.py (blob)  
└── src/ (tree)
    ├── main.py (blob)
    └── utils/ (tree)
        └── helper.py (blob)
```

### Key Properties

- **Trees point down** to files and subdirectories
- **Commits point to exactly one root tree** (the project snapshot)
- **Commits point back** to parent commit(s) (the history)
- **Objects are immutable** - changes create new objects

## 🚀 Role in Git Workflow

### During Add (Staging)
1. Read file content
2. Create blob object with `object_write()`
3. Store blob, get SHA
4. Update index with filename → SHA mapping

### During Commit
1. Read index entries
2. Build tree objects from index structure
3. Create commit object pointing to root tree
4. Store commit, get SHA
5. Update branch reference to new commit SHA

### During Checkout
1. Resolve branch/tag to commit SHA with `object_resolve()`
2. Read commit object with `object_read()`
3. Follow tree SHA to get directory structure
4. Recursively read tree and blob objects
5. Write blob content to working directory files

## 🎓 Design Insights

### The Power of Content-Addressing

Traditional filesystems store files by name/path. Git stores content by hash, with names as metadata. This inversion enables:

- **Reliable merging**: Same content = same hash across branches
- **Efficient storage**: No duplicate content ever stored
- **Strong integrity**: Content tampering immediately detected
- **Distributed consistency**: Objects with same SHA are identical everywhere

The object system transforms version control from "tracking file changes" to "managing content graphs" - a fundamentally more powerful abstraction.

---

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Repository](REPOSITORY.md) | **📖 Next**: [Index](INDEX.md) | **🔗 Related**: [Refs](REFS.md), [Tree](TREE.md)