# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 15:16:07 2026

@author: Cosimo Orlando
"""

import re
import os
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')

def parse_entries(content: str) -> list:
    """
	@brief Safely extracts entries, ignoring misplaced text.
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
            current_entry = []
        if current_entry or re.match(r'^## \[\d{4}-\d{2}-\d{2}\]', line):
            current_entry.append(line)
    if current_entry:
        entries.append('\n'.join(current_entry).strip())
    return entries

def reindex_entries(entries: list, start_line: int) -> tuple:
    """
	@brief Recalculates line numbers and returns formatted text and final line.
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
        
        # Update the header
        header = re.sub(r'\s*\[Lines:.*?\]\s*$', '', entry_lines[0])
        entry_lines[0] = f"{header} [Lines: {start}-{end}]"
        
        output.append('\n'.join(entry_lines))
        current_line = end + 2 # +2 for \n\n between entries
    
    return '\n\n'.join(output), current_line

def compress_memory() -> str:
    """
    @brief Moves old entries from log.md to archive.md and updates indices.
    @return Success message or status message.
    """
    log_file = "log.md"
    archive_file = "archive.md"
    
    if not os.path.exists(log_file): 
        return "Error: log.md not found."

    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()

    entries = parse_entries(log_content)

    # Extract unique days from `## [YYYY-MM-DD]` (preserves order)
    dates_ordered = []
    dates_set = set()
    for entry in entries:
        header = entry.split('\n')[0]
        m = re.search(r'\[\d{4}-\d{2}-\d{2}\]', header)
        if m and m.group() not in dates_set:
            dates_ordered.append(m.group())
            dates_set.add(m.group())

    if len(dates_set) <= 3:
        return f"No action: log.md has only {len(dates_set)} unique days."

    # Keep last 3 unique days (all entries from those dates)
    keep_dates = set(dates_ordered[-3:])
    to_keep = [e for e in entries if re.search(r'\[\d{4}-\d{2}-\d{2}\]', e.split('\n')[0]).group() in keep_dates]
    to_archive = [e for e in entries if e not in to_keep]

    # --- ARCHIVE HANDLING ---
    archive_start_line = 1
    archive_existing_content = ""
    
    if os.path.exists(archive_file):
        with open(archive_file, 'r', encoding='utf-8') as f:
            archive_existing_content = f.read().strip()
            if archive_existing_content:
                archive_start_line = len(archive_existing_content.split('\n')) + 2

    new_archive_text, _ = reindex_entries(to_archive, archive_start_line)

    with open(archive_file, 'a', encoding='utf-8') as f:
        if archive_existing_content: 
            f.write('\n\n')
        f.write(new_archive_text)

    # --- LOG.MD HANDLING ---
    new_log_text, _ = reindex_entries(to_keep, 1)

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(new_log_text)

    return f"Compression OK. {len(to_archive)} entries moved to archive.md. log.md contains the last {len(to_keep)} entries. Line indices updated."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compresses log.md by moving older entries to archive.md and recalculating line numbers.")
    args = parser.parse_args()
    
    # Execute compression and print result to terminal
    risultato = compress_memory()
    print(risultato)