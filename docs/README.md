# Vestigium Documentation

## 🎯 Overview

This documentation explains how Git works internally by exploring Vestigium's implementation. Each document focuses on fundamental Git concepts and their role in the version control workflow, rather than implementation details.

## 📚 Documentation Roadmap

### 🌟 **Essential Core Concepts** (Start Here)
These documents cover Git's fundamental architecture - the building blocks that everything else depends on:

1. **[REPOSITORY.md](REPOSITORY.md)** - Repository structure and discovery
   - The foundation: `.git` directory organization
   - Repository initialization and navigation
   - How Git finds repositories in directory trees

2. **[OBJECTS.md](OBJECTS.md)** - Git's object model and content storage
   - The four object types: blob, tree, commit, tag
   - Content-addressable storage and SHA hashing
   - Object resolution and naming systems

3. **[INDEX.md](INDEX.md)** - The staging area and three-tree architecture
   - Git's distinctive staging workflow
   - How the index enables atomic commits
   - Status checking and change detection

4. **[REFS.md](REFS.md)** - References and pointer management
   - Branches, tags, and HEAD explained
   - Symbolic vs direct references
   - How Git creates human-readable names for commits

### 🔧 **Essential Operations** (Build Understanding)
These documents explain the critical algorithms that make Git work:

5. **[TREE.md](TREE.md)** - Directory structure operations
   - Converting between flat and hierarchical representations
   - Index → Tree → Filesystem transformations
   - How commits capture directory snapshots

6. **[IGNORE.md](IGNORE.md)** - File filtering and ignore rules
   - Multi-source ignore system (global, repo, versioned)
   - Pattern matching and rule precedence
   - Making Git practical for real projects

### 📖 **Commands Reference** (Practical Usage)
7. **[COMMANDS.md](COMMANDS.md)** - Complete command reference
   - All Vestigium commands with syntax and examples
   - Organized by functional categories
   - Typical workflows and usage patterns

### 🎓 **Learning Path**

#### **Beginner Path** (Understanding Git's Model)
```
REPOSITORY → OBJECTS → REFS → INDEX
```
Start with the basic architecture, then understand how Git stores and references content.

#### **Intermediate Path** (Understanding Git's Operations)
```
TREE → IGNORE
```
Learn how Git manipulates directory structures and filters files.

#### **Complete Understanding**
Read all documents in the suggested order for comprehensive Git internals knowledge.

## 🧭 Quick Navigation

### **By Git Command**
- **[Complete Commands Reference](COMMANDS.md)** - Detailed guide for all Vestigium commands
- **`git init`** → [REPOSITORY.md](REPOSITORY.md)
- **`git add`** → [INDEX.md](INDEX.md), [TREE.md](TREE.md)
- **`git commit`** → [OBJECTS.md](OBJECTS.md), [TREE.md](TREE.md)
- **`git status`** → [INDEX.md](INDEX.md), [IGNORE.md](IGNORE.md)
- **`git checkout`** → [REFS.md](REFS.md), [TREE.md](TREE.md)
- **`git branch`** → [REFS.md](REFS.md)

### **By Concept**
- **Storage** → [OBJECTS.md](OBJECTS.md)
- **Naming** → [REFS.md](REFS.md)
- **Staging** → [INDEX.md](INDEX.md)
- **Structure** → [REPOSITORY.md](REPOSITORY.md)
- **Operations** → [TREE.md](TREE.md)
- **Filtering** → [IGNORE.md](IGNORE.md)

### **By Workflow Stage**
- **Setup** → [REPOSITORY.md](REPOSITORY.md)
- **Daily Work** → [INDEX.md](INDEX.md), [IGNORE.md](IGNORE.md)
- **History** → [OBJECTS.md](OBJECTS.md), [REFS.md](REFS.md)
- **Advanced** → [TREE.md](TREE.md)

## 🎯 Documentation Philosophy

Each document follows these principles:

### **Concept-Focused**
- Explains **why** Git works the way it does
- Focuses on **fundamental concepts** over implementation details
- Emphasizes **design insights** and **architectural decisions**

### **Workflow-Integrated**  
- Shows how each component fits into **Git's overall workflow**
- Explains the **role** of each system in version control operations
- Connects **theory to practice**

### **Technically Accurate**
- Based on **actual Vestigium implementation** (Git-compatible)
- Explains **real algorithms** used in version control
- Provides **concrete examples** of data structures and operations

## 🚀 Getting Started

1. **New to Git internals?** Start with [REPOSITORY.md](REPOSITORY.md)
2. **Want to understand storage?** Jump to [OBJECTS.md](OBJECTS.md)  
3. **Confused by staging?** Read [INDEX.md](INDEX.md)
4. **Need the full picture?** Follow the complete roadmap

## 💡 How to Use This Documentation

### **For Learning**
- Read documents in suggested order
- Try commands in Vestigium to see concepts in action
- Use navigation links to explore related concepts

### **For Reference**
- Use quick navigation to find specific topics
- Each document is self-contained for focused reading
- Cross-references help connect related concepts

### **For Understanding Git**
- Focus on the **concepts** rather than the code
- Pay attention to **design insights** sections
- Notice how everything **connects together** in the workflow

---

**Ready to dive deep into Git's internals?** Start with [REPOSITORY.md](REPOSITORY.md) and begin your journey! 🚀