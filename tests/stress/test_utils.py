"""
Utilities for generating test data for stress tests.

This module provides helper functions to create files and directory structures
for performance testing, including large files and numerous small files.
"""

import os
import random
import string
from pathlib import Path
from typing import List


def generate_random_content(size_bytes: int) -> bytes:
    """
    Generate random binary content of specified size.

    Args:
        size_bytes: Size of content to generate in bytes

    Returns:
        Random binary content
    """
    # Use a mix of text and binary data for realistic testing
    chunk_size = 1024
    content = bytearray()

    while len(content) < size_bytes:
        remaining = size_bytes - len(content)
        current_chunk_size = min(chunk_size, remaining)

        # Generate random text content
        text_chunk = "".join(
            random.choices(
                string.ascii_letters + string.digits + "\n\t ", k=current_chunk_size
            )
        )
        content.extend(text_chunk.encode("utf-8")[:current_chunk_size])

    return bytes(content[:size_bytes])


def create_large_file(filepath: Path, size_mb: int) -> None:
    """
    Create a large file with random content.

    Args:
        filepath: Path where to create the file
        size_mb: Size of the file in megabytes
    """
    size_bytes = size_mb * 1024 * 1024
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "wb") as f:
        content = generate_random_content(size_bytes)
        f.write(content)


def create_many_small_files(
    base_dir: Path, num_files: int, size_bytes: int = 1024
) -> List[Path]:
    """
    Create many small files with random content.

    Args:
        base_dir: Directory where to create files
        num_files: Number of files to create
        size_bytes: Size of each file in bytes

    Returns:
        List of created file paths
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    for i in range(num_files):
        # Create subdirectories to simulate real project structure
        subdir = base_dir / f"dir_{i // 10}"
        subdir.mkdir(exist_ok=True)

        filepath = subdir / f"file_{i:05d}.txt"
        content = generate_random_content(size_bytes)

        with open(filepath, "wb") as f:
            f.write(content)

        created_files.append(filepath)

    return created_files


def create_deep_directory_structure(
    base_dir: Path, depth: int, files_per_level: int = 5
) -> List[Path]:
    """
    Create a deep directory structure with files at each level.

    Args:
        base_dir: Base directory for the structure
        depth: How many levels deep to create
        files_per_level: Number of files to create at each level

    Returns:
        List of all created file paths
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    def create_level(current_dir: Path, remaining_depth: int, level_index: int):
        # Create files at current level
        for i in range(files_per_level):
            filepath = current_dir / f"level_{level_index}_file_{i}.txt"
            content = generate_random_content(512)  # Small files
            with open(filepath, "wb") as f:
                f.write(content)
            created_files.append(filepath)

        # Create subdirectories and recurse
        if remaining_depth > 0:
            for i in range(2):  # Create 2 subdirs per level
                subdir = current_dir / f"subdir_{i}"
                subdir.mkdir(exist_ok=True)
                create_level(subdir, remaining_depth - 1, level_index + 1)

    create_level(base_dir, depth, 0)
    return created_files


def create_binary_files(base_dir: Path, num_files: int) -> List[Path]:
    """
    Create binary files with various types of content.

    Args:
        base_dir: Directory where to create files
        num_files: Number of binary files to create

    Returns:
        List of created file paths
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    for i in range(num_files):
        filepath = base_dir / f"binary_{i:03d}.bin"

        # Create different types of binary content
        if i % 3 == 0:
            # Highly compressible content (repeated patterns)
            content = b"A" * 100 + b"B" * 100 + b"C" * 100
        elif i % 3 == 1:
            # Random binary content
            content = bytes([random.randint(0, 255) for _ in range(300)])
        else:
            # Mixed content
            text_part = f"File {i} header\n".encode()
            binary_part = bytes([random.randint(0, 255) for _ in range(200)])
            content = text_part + binary_part

        with open(filepath, "wb") as f:
            f.write(content)

        created_files.append(filepath)

    return created_files


def cleanup_test_files(filepaths: List[Path]) -> None:
    """
    Clean up test files and empty directories.

    Args:
        filepaths: List of file paths to remove
    """
    directories_to_check = set()

    for filepath in filepaths:
        if filepath.exists():
            directories_to_check.add(filepath.parent)
            filepath.unlink()

    # Remove empty directories
    for directory in sorted(
        directories_to_check, key=lambda p: len(p.parts), reverse=True
    ):
        try:
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        except OSError:
            pass  # Directory not empty or can't be removed
