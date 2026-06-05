# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 01:04:33 2026

@author: Cosimo Orlando
"""

import os
import re
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')

def search_archive(keyword: str) -> str:
    """
    @brief Searches a keyword in archive.md and returns titles and line numbers.
    @param keyword The keyword or phrase to search.
    @return Matching entry headers, or 'No results' message.
    """
    if not os.path.exists("archive.md"): 
        return "Error: archive.md not found or empty."
    
    with open("archive.md", "r", encoding="utf-8") as f:
        content = f.read()
        
    entries = re.split(r'(?=^## \[\d{4}-\d{2}-\d{2}\])', content, flags=re.MULTILINE)
    results = []
    
    for entry in entries:
        if keyword.lower() in entry.lower():
            # Extract only the header (contains title and [Lines: X-Y])
            header = entry.split('\n')[0]
            results.append(header)
            
    if not results:
        return f"No results for '{keyword}'."
    return "Found in the following entries:\n" + '\n'.join(results)


def extract_lines(file_path: str, start_line: int, end_line: int) -> str:
    """
    @brief Extracts exact lines from a file.
    @param file_path The file to read.
    @param start_line The starting line number (1-based).
    @param end_line The ending line number (inclusive).
    @return The extracted line content.
    """
    if not os.path.exists(file_path): 
        return f"Error: File {file_path} not found."
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Handle indices (1-based for user/LLM, 0-based for Python)
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    
    extracted = lines[start_idx:end_idx]
    return ''.join(extracted).strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool for searching and extracting memory from the archive.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search a keyword in archive.md")
    search_parser.add_argument("keyword", type=str, help="The word or phrase to search")

    # Command: extract
    extract_parser = subparsers.add_parser("extract", help="Extract a range of lines from a file")
    extract_parser.add_argument("file", type=str, help="The file to read (e.g., archive.md)")
    extract_parser.add_argument("start", type=int, help="Starting line number")
    extract_parser.add_argument("end", type=int, help="Ending line number")

    args = parser.parse_args()

    # Execute based on selected command
    if args.command == "search":
        print(search_archive(args.keyword))
    elif args.command == "extract":
        print(extract_lines(args.file, args.start, args.end))
    else:
        parser.print_help()