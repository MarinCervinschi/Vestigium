# Ignore System - Git's File Filtering

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Tree](TREE.md) | **📖 Next**: [Utilities](UTILITIES.md) | **🔗 Related**: [Index](INDEX.md), [Repository](REPOSITORY.md), [Commands](COMMANDS.md)


## 📋 Table of Contents

- [🎯 Introduction](#-introduction)
- [🚫 The Ignore Problem](#-the-ignore-problem)
- [🔧 Ignore Rule Sources](#-ignore-rule-sources)
- [📝 Ignore Rule Syntax](#-ignore-rule-syntax)
- [🔍 Rule Evaluation Algorithm](#-rule-evaluation-algorithm)
- [🔄 Role in Git Workflow](#-role-in-git-workflow)
- [🎓 Design Insights](#-design-insights)

---

## 🎯 Introduction

The **ignore system** is Git's mechanism for excluding files from version control. It solves a fundamental problem: not all files in a project directory should be tracked. Build artifacts, temporary files, personal configurations, and other generated content should be excluded. This document explains how Vestigium implements Git's ignore functionality and why it's essential for clean version control.

## 🚫 The Ignore Problem

### What Should Be Ignored?

Every project contains files that shouldn't be versioned:

- **Build artifacts**: `*.o`, `*.class`, `target/`, `dist/`
- **Dependencies**: `node_modules/`, `vendor/`, `.venv/`
- **IDE files**: `.vscode/`, `.idea/`, `*.swp`
- **OS files**: `.DS_Store`, `Thumbs.db`, `*.tmp`
- **Secrets**: `.env`, `config.local.json`, API keys
- **Logs**: `*.log`, `debug.txt`, crash dumps

### Why Ignore Matters

Without proper ignoring:
- **Repository bloat**: Huge files make cloning slow
- **Noise in diffs**: Generated files obscure real changes  
- **Merge conflicts**: Build artifacts cause unnecessary conflicts
- **Security risks**: Secrets accidentally committed
- **Cross-platform issues**: OS-specific files break builds

## 🔧 Ignore Rule Sources

Git uses **multiple ignore sources** with different scopes:

### 1. **Repository Exclude** (`.ves/info/exclude`)
- **Scope**: Local repository only
- **Use case**: Personal preferences, local tools
- **Not versioned**: Changes don't affect other contributors
- **Example**: Personal editor configs, local debug files

### 2. **Global Ignore** (`~/.config/ves/ignore`)
- **Scope**: All repositories for this user
- **Use case**: User-wide preferences (OS files, editor configs)
- **Personal**: Each developer has their own global rules
- **Example**: `.DS_Store`, `*.swp`, IDE folders

### 3. **Tracked Ignore Files** (`.vesignore`)
- **Scope**: Directory where file is located (and subdirectories)
- **Versioned**: Shared with all contributors
- **Use case**: Project-specific ignores
- **Example**: `build/`, `*.log`, language-specific patterns

## 📝 Ignore Rule Syntax

### Basic Patterns

```bash
# Exact filename
secret.txt

# Extension wildcard  
*.log

# Directory (trailing slash)
build/

# Path from repo root
src/debug/temp.txt
```

### Advanced Patterns

#### **Negation Rules** (Whitelist)
```bash
# Ignore all .txt files
*.txt

# But include important.txt
!important.txt

# Ignore build directory
build/

# But include build/README.md
!build/README.md
```

#### **Directory Globbing**
```bash
# Any depth
**/debug/

# From root
debug/

# Specific depth
src/*/temp/
```

#### **Escape Characters**
```bash
# Literal # character (not comment)
\#not-a-comment

# Literal ! character (not negation)
\!not-negation
```

## 🔍 Rule Evaluation Algorithm

### Multiple Rule Sources

The ignore system must **combine rules** from different sources:

```python
@dataclass
class VesIgnore:
    absolute: List[List[Tuple[str, bool]]]      # Global + repo exclude
    scoped: Dict[str, List[Tuple[str, bool]]]   # .vesignore files
```

### Rule Precedence

1. **Scoped rules first**: `.vesignore` files take precedence
2. **Directory hierarchy**: Closer `.vesignore` files override distant ones
3. **Absolute rules**: Global and repository exclude as fallback
4. **Rule order**: Later rules override earlier rules

### `check_ignore()` - The Main Algorithm

```python
def check_ignore(rules: VesIgnore, path: str) -> bool:
```

#### 1. **Scoped Rule Check**
```python
result = check_ignore_scoped(rules.scoped, path)
if result != None:
    return result
```

Walks up directory tree from file location, checking for `.vesignore` files:
- `src/utils/file.py` → check `src/utils/.vesignore`, then `src/.vesignore`, then `.vesignore`
- First matching rule wins

#### 2. **Absolute Rule Fallback** 
```python
return check_ignore_absolute(rules.absolute, path)
```

If no scoped rules match, check global and repository exclude rules.

### Pattern Matching Logic

#### `check_ignore1()` - Single Ruleset Processing

This function implements the **core pattern matching**:

##### **Directory Patterns** (ending with `/`)
```python
if pattern.endswith("/"):
    if path.startswith(dir_pattern + "/") or path == dir_pattern:
        result = value
```

Matches directories and their contents:
- `build/` matches `build/output.jar`, `build/libs/app.jar`
- `build/` matches `build` itself

##### **Globstar Patterns** (`**`)
```python
if "**" in dir_pattern:
    # Matches any depth
```

Handles advanced globbing:
- `**/debug/` matches `debug/`, `src/debug/`, `src/main/debug/`
- `logs/**` matches everything under `logs/`

##### **File Patterns**
```python
if fnmatch(path, pattern):
    result = value
```

Uses Python's `fnmatch` for glob patterns:
- `*.log` matches `app.log`, `debug.log`
- `test_*.py` matches `test_auth.py`, `test_db.py`

#### **Last Match Wins**
```python
for pattern, value in rules:
    if fnmatch(path, pattern):
        result = value  # Override previous matches
```

Later rules override earlier ones, enabling negation patterns.

## 🔄 Role in Git Workflow

### During Status Checking

```bash
ves status
```

1. **Scan working directory** for all files
2. **Read ignore rules** from all sources
3. **Filter untracked files**:
   ```python
   for file in working_directory:
       if not in_index(file) and not check_ignore(rules, file):
           show_as_untracked(file)
   ```
4. **Show only non-ignored** untracked files

Without ignoring, `ves status` would show thousands of irrelevant files.

### During Add Operations

```bash
ves add .
```

When adding directories recursively:
1. **Traverse directory tree**
2. **Skip ignored files** during traversal
3. **Add only non-ignored files** to index

Prevents accidentally staging build artifacts or temporary files.

### Check-Ignore Command

```bash
ves check-ignore build/output.jar node_modules/
```

Diagnostic tool that:
1. **Tests specific paths** against ignore rules
2. **Shows which paths would be ignored**
3. **Helps debug ignore patterns**

## 🎯 Design Insights

### Why Multiple Sources?

Different ignore needs require different scopes:

- **Global**: User preferences (OS files, personal tools)
- **Repository**: Local preferences (not shared with team)
- **Versioned**: Project requirements (shared with team)

### Why Scoped Rules?

Directory-specific rules enable:
- **Granular control**: Different rules for different parts of project
- **Inheritance**: Subdirectories inherit parent rules
- **Override capability**: Closer rules override distant ones

### Why Negation Rules?

Negation enables **whitelist patterns**:
```bash
# Ignore everything in logs/
logs/*

# Except the README
!logs/README.md
```

This is more maintainable than listing every specific file to ignore.

### Performance Considerations

#### Rule Caching
The ignore system reads rules once and caches them:
- **Expensive**: File I/O to read `.vesignore` files
- **Cheap**: Pattern matching against cached rules

#### Directory Walking
When checking `src/deep/nested/file.py`:
- Walk up: `src/deep/nested/` → `src/deep/` → `src/` → ``
- Stop at first match (most specific wins)
- Cache results for sibling files

### The Ignore Abstraction

Ignore rules transform the repository view:
- **Physical reality**: All files in working directory
- **Git's view**: Only non-ignored, trackable files

This abstraction enables:
- **Clean repositories**: Only meaningful content tracked
- **Consistent experience**: Same ignore behavior across platforms
- **Flexible control**: Fine-grained inclusion/exclusion rules

The ignore system is essential for **practical version control** - it makes Git usable for real projects by filtering out the noise and focusing on what actually matters for the project's history.

---

> **📍 Navigation**: [📚 Docs Home](README.md) | **⬅️ Prev**: [Tree](TREE.md) | **📖 Next**: [Utilities](UTILITIES.md) | **🔗 Related**: [Index](INDEX.md), [Repository](REPOSITORY.md), [Commands](COMMANDS.md)