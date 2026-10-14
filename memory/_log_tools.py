# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 15:15:15 2026

@author: Cosimo Orlando
"""

import os
import re
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')

def parse_entries(content: str) -> list:
    """
    @brief Safely extracts entries from content.
    @param content The text content to parse.
    @return A list of entry strings.
    """
    lines = content.split('\n')
    entries = []
    current_entry = []
    for line in lines:
        if re.match(r'^## \[\d{4}-\d{2}-\d{2}\]', line):
            if current_entry:
                entries.append('\n'.join(current_entry).strip())
			# moved out 'if current_entry:' for code robustness
            current_entry = []
        if current_entry or re.match(r'^## \[\d{4}-\d{2}-\d{2}\]', line):
            current_entry.append(line)
    if current_entry:
        entries.append('\n'.join(current_entry).strip())
    return entries

def reindex_entries(entries: list, start_line: int) -> tuple:
    """
    @brief Recalculates line numbers and returns formatted text.
    @param entries The list of entry strings.
    @param start_line The starting line number.
    @return A tuple of (formatted text, final line number).
    """
    output = []
    current_line = start_line
    for entry_text in entries:
        entry_lines = entry_text.split('\n')
        start = current_line
        end = current_line + len(entry_lines) - 1
        
        header = re.sub(r'\s*\[Lines:.*?\]\s*$', '', entry_lines[0])
        entry_lines[0] = f"{header} [Lines: {start}-{end}]"
        
        output.append('\n'.join(entry_lines))
        current_line = end + 2
    return '\n\n'.join(output)

def get_log_entries() -> list:
    """
    @brief Retrieves log entries from log.md.
    @return A list of entry strings, or empty list if file not found.
    """
    if not os.path.exists("log.md"):
        return []
    with open("log.md", "r", encoding="utf-8") as f:
        return parse_entries(f.read())

def save_log_entries(entries: list) -> None:
    """
    @brief Saves reindexed entries to log.md.
    @param entries The list of entry strings to save.
    """
    new_content = reindex_entries(entries, 1)
    with open("log.md", "w", encoding="utf-8") as f:
        f.write(new_content)

# ---- SUPPORT FUNCTIONS FOR UNIQUENESS ----
def extract_title_and_date(entry_text: str) -> tuple:
    """
    @brief Extracts date and title from an entry text.
    @param entry_text The entry text to parse.
    @return A tuple of (date_str, title) or (None, None) if parsing fails.
    """
    header = entry_text.split('\n')[0]
    m = re.match(r'^## \[(\d{4}-\d{2}-\d{2})\] — (.+?) \[Lines: \d+-\d+\]', header)
    if not m:
        # Fallback: try without [Lines: ...] (possible during editing)
        m2 = re.match(r'^## \[(\d{4}-\d{2}-\d{2})\] — (.+)', header)
        if m2:
            return m2.group(1), m2.group(2).strip()
        return None, None
    return m.group(1), m.group(2).strip()

def is_duplicate(new_date: str, new_title: str, entries: list, exclude_index: int = None) -> bool:
    """
    @brief Checks if an entry with the same date and title already exists.
    @param new_date The date to check.
    @param new_title The title to check.
    @param entries The list of existing entries.
    @param exclude_index Optional index to exclude from check.
    @return True if duplicate exists, False otherwise.
    """
    for i, entry in enumerate(entries):
        if exclude_index is not None and i == exclude_index:
            continue
        d, t = extract_title_and_date(entry)
        if d == new_date and t == new_title:
            return True
    return False
# -------------------------------------------

# --- COMANDI CLI ---

def list_entries() -> str:
    """
    @brief Lists all entry headers in log.md.
    @return A string of entry headers, or empty string if no entries.
    """
    entries = get_log_entries()
    if not entries:
        return "" # No title, no errors, just blank.
    
    result = []
    for entry in entries:
        header = entry.split('\n')[0]
        result.append(header)
    return '\n'.join(result)

def read_entry(index: int) -> str:
    """
    @brief Reads the full entry at the given index.
    @param index The 1-based index of the entry.
    @return The entry text, or error message if index invalid.ù
    """
    entries = get_log_entries()
    if index < 1 or index > len(entries):
        return f"Error: Index {index} invalid. There are {len(entries)} entries."
    return entries[index-1]

def append_entry(file_path: str) -> str:
    """
    @brief Appends a new entry from a temp file to log.md.
    @param file_path Path to the temp file containing the new entry.
    @return Success message or error message.
    """
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    
    with open(file_path, "r", encoding="utf-8") as f:
        new_content = f.read().strip()
        
    if not re.match(r'^## \[\d{4}-\d{2}-\d{2}\]', new_content):
        return "Error: Content must start with '## [YYYY-MM-DD]'."

    # Extract date and title of the new entry
    new_date, new_title = extract_title_and_date(new_content)
    if not new_date:
        return "Error: Unable to extract date from header."

    entries = get_log_entries()
    # Duplicate Check
    if is_duplicate(new_date, new_title, entries):
        return f"Error: Duplicate entry for {new_date} with title '{new_title}'. Already present in log.md."

    entries.append(new_content)
    save_log_entries(entries)
    return "New entry added successfully to the bottom of log.md. Indices recalculated."

def edit_draft(targets: list) -> str:
    """
    @brief Writes the stdin draft to temp.md (the ONLY editable memory file).
    @param targets The target file argument(s). MUST be exactly [temp.md]; any other
           target (log.md, archive.md, old 'edit <index> <file>' habits) is refused
           with an instructive message instead of a cryptic argparse error.
    @return Success message or instructive refusal message.
    """
    if [os.path.basename(t) for t in targets] != ["temp.md"]:
        return ("Operation not allowed: edit works ONLY on temp.md. "
                "log.md/archive.md are PROGRESSIVE memory, NEVER rewritten. "
                "Corrections = NEW entry: run append temp.md.")

    new_content = sys.stdin.read().strip()
    if not new_content:
        return "Error: empty draft (stdin)."
    if not re.match(r'^## \[\d{4}-\d{2}-\d{2}\]', new_content):
        return "Error: Content must start with '## [YYYY-MM-DD]'."

    with open("temp.md", "w", encoding="utf-8") as f:
        f.write(new_content)
    return "Draft written to temp.md. Ready: run append temp.md."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool for managing log.md securely.")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="Show entry headers in log.md")
    
    # read
    read_parser = subparsers.add_parser("read", help="Read full entry N")
    read_parser.add_argument("index", type=int, help="Entry index (e.g., 1 for the first)")
    
    # append
    append_parser = subparsers.add_parser("append", help="Append a new entry from a file")
    append_parser.add_argument("file", type=str, help="Temp file containing the new entry")
    
    # edit
    edit_parser = subparsers.add_parser("edit", help="Write the stdin draft to temp.md (ONLY temp.md is a legal target)")
    edit_parser.add_argument("file", nargs="*", help="Target file (must be temp.md)")

    args = parser.parse_args()

    if args.command == "list":
        print(list_entries())
    elif args.command == "read":
        print(read_entry(args.index))
    elif args.command == "append":
        print(append_entry(args.file))
    elif args.command == "edit":
        print(edit_draft(args.file))
    else:
        parser.print_help()