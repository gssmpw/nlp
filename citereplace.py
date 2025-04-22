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
    filename='citation_replacement.log'
)

# get all of the papers
PAPERS_DIR = "papers"

# these are the citation commands I have found skimming through papers
CITATION_COMMANDS = [
    "cite",
    "citet",
    "citep", 
    "citealp",
    "citeauthor",
    "citeyear",
    "citetext",
    "citenum",
    "citeyearpar",
    "citealt",
    "citestyle"
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

def replace_citations(folder):
    try:
        relatedwork_file = os.path.join(folder, "relatedwork.tex")
        replacedcite_file = os.path.join(folder, "replacedcite.tex")
        
        # bail if original file doesn't exist
        if not os.path.exists(relatedwork_file):
            return False
            
        # read the file
        with open(relatedwork_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        modified_content = content
        found_citations = False
        
        # super regex - match ANY citation command pattern
        for cmd in CITATION_COMMANDS:
            # matches both with and without tilde
            pattern = r'~?\\' + cmd + r'\{[^\}]*\}'
            if re.search(pattern, modified_content):
                found_citations = True
                modified_content = re.sub(pattern, '____', modified_content)
        
        # also catch natbib's weird optional argument formats like \citep[e.g.][p.~215]{citation}
        natbib_pattern = r'~?\\cite[tp]\[[^\]]*\](?:\[[^\]]*\])?\{[^\}]*\}'
        if re.search(natbib_pattern, modified_content):
            found_citations = True
            modified_content = re.sub(natbib_pattern, '____', modified_content)
        
        # handles edge case where no citations are found
        if not found_citations:
            logging.info(f"No citations found in {relatedwork_file}")
            return False
        
        # write to new file - don't touch the original
        with open(replacedcite_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
            
        logging.info(f"Created {replacedcite_file} with replaced citations")
        return True
    except Exception as e:
        logging.error(f"Error processing {folder}: {str(e)}")
        return False

def main():
    logging.info("Starting citation replacement process")
    
    # sanity check
    papers_path = Path(PAPERS_DIR)
    if not papers_path.exists() or not papers_path.is_dir():
        logging.error(f"Papers directory {PAPERS_DIR} not found or is not a directory")
        print(f"Error: Papers directory {PAPERS_DIR} not found")
        return
    
    # get all the folders
    paper_folders = find_paper_folders(PAPERS_DIR)
    if not paper_folders:
        logging.error("No paper folders found")
        print("Error: No paper folders found")
        return

    files_processed = 0
    files_created = 0
    
    for i, folder in enumerate(paper_folders):
        # progress update because it might take a while, not as long as RWextract though
        if (i + 1) % 100 == 0:
            print(f"Progress: {i+1}/{len(paper_folders)} folders")
            
        # check if relatedwork.tex exists
        relatedwork_file = os.path.join(folder, "relatedwork.tex")
        if os.path.exists(relatedwork_file):
            files_processed += 1
            success = replace_citations(folder)
            if success:
                files_created += 1
    
    # Final output so we know what happened
    logging.info(f"Completed processing {files_processed} relatedwork.tex files")
    logging.info(f"Created {files_created} replacedcite.tex files")
    print(f"\nDone! Processed {files_processed} relatedwork.tex files.")
    print(f"Created {files_created} replacedcite.tex files with citations replaced.")
    print(f"Check 'citation_replacement.log' for any issues.")

if __name__ == "__main__":
    main()

