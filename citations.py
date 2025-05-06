#!/usr/bin/env python3
# Author: Dawson Ploudre
import os
import re
import glob
from pathlib import Path


def find_papers_with_required_files(base_dir="papers"):
    """Find papers that have both relatedwork.tex and a .bib file."""
    paper_dirs = []
    
    # check each subdir for required files
    for paper_dir in os.listdir(base_dir):
        full_path = os.path.join(base_dir, paper_dir)
        
        if not os.path.isdir(full_path):
            continue
            
        relatedwork_path = os.path.join(full_path, "relatedwork.tex")
        if not os.path.isfile(relatedwork_path):
            continue
            
        # should find any .bib file
        bib_files = glob.glob(os.path.join(full_path, "*.bib"))
        if not bib_files:
            continue
            
        paper_dirs.append({
            "dir": full_path,
            "relatedwork": relatedwork_path,
            "bib": bib_files[0]  #grab first one
        })
    
    return paper_dirs


def extract_citations(tex_file):
    """Pull out citation keys from a .tex file."""
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # should find all citations
    citation_pattern = r'\\cite[pt]?(?:\[.*?\])?{([^}]+)}'
    matches = re.findall(citation_pattern, content)
    
    # keep everything in order
    citation_keys = []
    for match in matches:
        keys = [key.strip() for key in match.split(',')]
        citation_keys.extend(keys)
    
    return citation_keys


def parse_bib_file(bib_file):
    """Parse a .bib file and extract the entries."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    content = None
    
    # Try different encodings until one works
    for encoding in encodings:
        try:
            with open(bib_file, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"  Successfully read with {encoding} encoding")
            break
        except UnicodeDecodeError:
            print(f"  Failed to read with {encoding} encoding")
            continue
    
    if content is None:
        print(f"  WARNING: Couldn't read {bib_file} with any encoding. Skipping.")
        return {}
    
    # Get all BibTeX entries
    entries = {}
    entry_pattern = r'@(\w+){([^,]+),([^@]+)}'
    matches = re.finditer(entry_pattern, content, re.DOTALL)
    
    for match in matches:
        entry_type = match.group(1)
        citation_key = match.group(2)
        entry_content = match.group(3)
        
        entries[citation_key] = {
            'type': entry_type,
            'content': entry_content.strip(),
            'raw': f"@{entry_type}{{{citation_key},{entry_content}}}"
        }
    
    return entries


def extract_author_and_year(bib_entry):
    """Get author and year from a BibTeX entry."""
    try:
        # Get the author(s)
        author_match = re.search(r'author\s*=\s*[{"](.*?)[}"],', bib_entry, re.IGNORECASE | re.DOTALL)
        if not author_match:
            return None
        
        author_text = author_match.group(1)
        
        # cleans up junk, so much regex please help
        author_text = re.sub(r'\\[a-zA-Z]+', '', author_text)
        author_text = re.sub(r'[{}]', '', author_text)
        
        # Handle multiple authors
        authors = author_text.split(' and ')
        
        # Get first author's last name
        first_author = authors[0].strip()
        last_name = first_author.split(',')[0] if ',' in first_author else first_author.split()[-1]
        
        # adds "et al." for multiple authors
        author_citation = last_name
        if len(authors) > 1:
            author_citation += " et al."
        
        # should extract the year
        year_match = re.search(r'year\s*=\s*[{"](\d{4})[}"],', bib_entry, re.IGNORECASE) # I HATE regex
        if not year_match:
            return None
        
        year = year_match.group(1)
        
        return f"({author_citation}, {year})"
    
    except Exception as e:
        print(f"    Error extracting citation info: {str(e)}")
        return None


def generate_formatted_citations(citation_keys, bib_entries):
    """Turn citation keys into proper in-text citations."""
    formatted_citations = []
    
    for key in citation_keys:
        if key in bib_entries:
            citation = extract_author_and_year(bib_entries[key]['content'])
            formatted_citations.append(citation if citation else "0")
        else:
            formatted_citations.append("0")
    
    return formatted_citations


def create_citation_file_for_paper(paper_dir, formatted_citations):
    """Save formatted citations to a file."""
    paper_name = os.path.basename(paper_dir)
    output_file = os.path.join(paper_dir, "citations.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # One citation per line
        for citation in formatted_citations:
            f.write(f"{citation}\n")
    
    print(f"  Created {output_file} with {len(formatted_citations)} formatted citations")
    return True


def main():
    paper_dirs = find_papers_with_required_files()
    
    if not paper_dirs:
        print("No papers found with both relatedwork.tex and .bib files.")
        return
    
    # Process each paper
    success_count = 0
    total_citation_count = 0
    
    for paper in paper_dirs:
        paper_dir = paper["dir"]
        print(f"Processing: {paper_dir}")
        
        try:
            # Get citation keys in order
            citation_keys = extract_citations(paper["relatedwork"])
            print(f"  Found {len(citation_keys)} citations")
            
            # Parse the BibTeX file
            bib_entries = parse_bib_file(paper["bib"])
            print(f"  Parsed {len(bib_entries)} BibTeX entries")
            
            # Format the citations
            formatted_citations = generate_formatted_citations(citation_keys, bib_entries)
            print(f"  Generated {len(formatted_citations)} formatted citations")
            
            if create_citation_file_for_paper(paper_dir, formatted_citations):
                success_count += 1
                total_citation_count += len(formatted_citations)
            
        except Exception as e:
            print(f"  ERROR processing {paper_dir}: {str(e)}")
    
    # end summary
    print(f"\nSUMMARY:")
    print(f"- Successfully processed {success_count}/{len(paper_dirs)} papers")
    print(f"- Found {total_citation_count} citations total")
    print(f"- Created {success_count} citations.txt files")


if __name__ == "__main__":
    main()
