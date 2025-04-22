#!/usr/bin/env python3
# Author: Dawson Ploudre

import os
import re
import logging
from pathlib import Path

# setup logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='related_work_extraction.log'
)

# access all of the papers
PAPERS_DIR = "papers"
SECTION_NAMES = [
    "related work", 
    "related_work",
    "relatedwork",
    "related research",
    "prior work",
    "previous work",
    "literature review",
    "background and related work",
    "related studies"
]

def find_paper_folders(root_dir):
    logging.info(f"Searching for paper folders in {root_dir}")
    try:
        paper_folders = [os.path.join(root_dir, d) for d in os.listdir(root_dir) 
                         if os.path.isdir(os.path.join(root_dir, d))]
        logging.info(f"Found {len(paper_folders)} paper folders")
        return paper_folders
    except Exception as e:
        logging.error(f"Error finding paper folders: {str(e)}")
        return []

def find_tex_files(folder):
    tex_files = []
    try:
        for file in os.listdir(folder):
            if file.lower().endswith('.tex'):
                tex_files.append(os.path.join(folder, file))
        return tex_files
    except Exception as e:
        logging.error(f"Error finding .tex files in {folder}: {str(e)}")
        return []

def extract_related_work(tex_file):
    try:
        with open(tex_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        section_patterns = []
        for name in SECTION_NAMES:
            section_patterns.append(r'\\section\*?{(' + name + r'.*?)}(.*?)(?=\\section|\\chapter|\\end{document}|$)')
            section_patterns.append(r'\\section\*?{(?:\d+\.|[IVX]+\.)\s*(' + name + r'.*?)}(.*?)(?=\\section|\\chapter|\\end{document}|$)')
            section_patterns.append(r'\\section\*?{(' + name.upper() + r'.*?)}(.*?)(?=\\section|\\chapter|\\end{document}|$)')
            section_patterns.append(r'\\section\*?{(' + name.title() + r'.*?)}(.*?)(?=\\section|\\chapter|\\end{document}|$)')
        
        for name in SECTION_NAMES:
            section_patterns.append(r'\\subsection\*?{(' + name + r'.*?)}(.*?)(?=\\section|\\subsection|\\chapter|\\end{document}|$)')
            section_patterns.append(r'\\subsection\*?{(' + name.upper() + r'.*?)}(.*?)(?=\\section|\\subsection|\\chapter|\\end{document}|$)')
            section_patterns.append(r'\\subsection\*?{(' + name.title() + r'.*?)}(.*?)(?=\\section|\\subsection|\\chapter|\\end{document}|$)')
        
        # crazy regex hell!! but it works ¯\_(Ä)_/¯
        for pattern in section_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                title = match.group(1)
                section_content = match.group(2).strip()
                if section_content:
                    return f"\\section{{{title}}}\n{section_content}"
        
        return None
    except Exception as e:
        logging.error(f"Error extracting related work from {tex_file}: {str(e)}")
        return None

def process_paper_folder(paper_folder):
    logging.info(f"Processing folder: {paper_folder}")
    tex_files = find_tex_files(paper_folder)
    
    if not tex_files:
        logging.warning(f"No .tex files found in {paper_folder}")
        return False
    
    # This should access all of the tex files and check for related works
    for tex_file in tex_files:
        related_work = extract_related_work(tex_file)
        if related_work:
            output_file = os.path.join(paper_folder, "relatedwork.tex")
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(related_work)
                logging.info(f"Related work extracted and saved to {output_file}")
                return True
            except Exception as e:
                logging.error(f"Error writing to {output_file}: {str(e)}")
    
    logging.warning(f"No related work section found in any .tex file in {paper_folder}")
    return False

def main():
    logging.info("Starting related work extraction process")
    
    papers_path = Path(PAPERS_DIR)
    if not papers_path.exists() or not papers_path.is_dir():
        logging.error(f"Papers directory {PAPERS_DIR} not found or is not a directory")
        print(f"Error: Papers directory {PAPERS_DIR} not found")
        return
    
    paper_folders = find_paper_folders(PAPERS_DIR)
    if not paper_folders:
        logging.error("No paper folders found")
        print("Error: No paper folders found")
        return
    
    # logs the processing, 10k+ papers - gonna take forever so want a progress update
    success_count = 0
    for i, folder in enumerate(paper_folders):
        print(f"Processing {i+1}/{len(paper_folders)}: {os.path.basename(folder)}")
        success = process_paper_folder(folder)
        if success:
            success_count += 1
    
    logging.info(f"Completed processing {len(paper_folders)} folders")
    logging.info(f"Successfully extracted related work from {success_count} papers")
    print(f"\nCompleted! Processed {len(paper_folders)} paper folders.")
    print(f"Successfully extracted related work from {success_count} papers.")
    print(f"See 'related_work_extraction.log' for details.")

if __name__ == "__main__":
    main()
