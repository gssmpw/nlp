# Author: Dawson Ploudre

import os
import json
import re
from typing import Dict, List, Tuple, Set, Optional

def load_citations(citations_path: str) -> List[Dict]:
    """loads the citations from the JSON file."""
    with open(citations_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_response(response_path: str) -> str:
    """load the LLM's response"""
    with open(response_path, 'r', encoding='utf-8') as f:
        return f.read()

def normalize_text(text: str) -> str:
    """basic normalizing, removing punctuation and lowercasing"""
    return re.sub(r'[^\w\s]', '', text.lower())

def is_citation_mentioned(response_text: str, author: str, title: str) -> Tuple[bool, str]:
    """
    Check if the citation is mentioned in the response.
    Returns (is_mentioned, match_type) where match_type is 'author', 'title', 'both', or 'none'.
    Requires exact title matching (substring) to count as a title match.
    """
    response_text = normalize_text(response_text)
    
    # gets all of the author names since there can be multiple authors
    author_names = [normalize_text(name.strip()) for name in author.split('and')]
    authors_matched = []
    
    # checks if author name is mentioned
    for name in author_names:
        name_parts = name.split()
        if len(name_parts) > 1:
            # check for last name at minimum
            last_name = name_parts[-1]
            if len(last_name) > 3 and last_name in response_text:  # only check names with at least 4 characters
                authors_matched.append(name)
        else:
            # single name author
            if len(name) > 3 and name in response_text:
                authors_matched.append(name)
                
    # check title with substring matching
    normalized_title = normalize_text(title)
    title_matched = normalized_title in response_text
    
    if authors_matched and title_matched:
        return True, "both"
    elif authors_matched:
        return True, "author"
    elif title_matched:
        return True, "title"
    else:
        return False, "none"

def evaluate_paper_folder(folder_path: str) -> Dict:
    """
    Evaluate the accuracy of citation identification for a single paper folder.
    Returns a dictionary with accuracy metrics.
    """
    citations_path = os.path.join(folder_path, "citations.json")
    response_path = os.path.join(folder_path, "response.txt")
    
    if not (os.path.exists(citations_path) and os.path.exists(response_path)):
        return {"error": f"Missing files in {folder_path}"}
    
    citations = load_citations(citations_path)
    response_text = load_response(response_path)
    
    results = {
        "folder": folder_path,
        "total_citations": 0,
        "correct_citations": 0,
        "match_types": {"author": 0, "title": 0, "both": 0, "none": 0},
        "citation_details": []
    }
    
    for citation_group in citations:
        for paper in citation_group.get("papers", []):
            results["total_citations"] += 1
            
            author = paper.get("author", "")
            title = paper.get("title", "")
            key = paper.get("key", "unknown")
            
            is_mentioned, match_type = is_citation_mentioned(response_text, author, title)
            
            if is_mentioned:
                results["correct_citations"] += 1
            
            results["match_types"][match_type] += 1
            
            results["citation_details"].append({
                "key": key,
                "author": author,
                "title": title,
                "correctly_identified": is_mentioned,
                "match_type": match_type
            })
    
    if results["total_citations"] > 0:
        results["accuracy"] = results["correct_citations"] / results["total_citations"]
    else:
        results["accuracy"] = 0.0
        
    return results

def evaluate_all_papers(base_path: str) -> Dict:
    """
    Evaluate all paper folders under the base path.
    Returns a dictionary with overall and per-paper metrics.
    """
    overall_results = {
        "total_papers": 0,
        "total_citations": 0,
        "correct_citations": 0,
        "paper_results": [],
        "match_types": {"author": 0, "title": 0, "both": 0, "none": 0},
        "skipped_folders": 0
    }
    
    # Get all subdirectories that could be paper folders
    paper_folders = [os.path.join(base_path, d) for d in os.listdir(base_path) 
                    if os.path.isdir(os.path.join(base_path, d))]
    
    for folder in paper_folders:
        paper_result = evaluate_paper_folder(folder)
        
        # Skip folders with errors
        if "error" in paper_result:
            print(f"Warning: {paper_result['error']}")
            overall_results["skipped_folders"] += 1
            continue
            
        overall_results["total_papers"] += 1
        overall_results["total_citations"] += paper_result["total_citations"]
        overall_results["correct_citations"] += paper_result["correct_citations"]
        
        # Aggregate match types
        for match_type in paper_result["match_types"]:
            overall_results["match_types"][match_type] += paper_result["match_types"][match_type]
        
        # Store individual paper results
        overall_results["paper_results"].append(paper_result)
    
    # Calculate overall accuracy
    if overall_results["total_citations"] > 0:
        overall_results["overall_accuracy"] = overall_results["correct_citations"] / overall_results["total_citations"]
    else:
        overall_results["overall_accuracy"] = 0.0
        
    return overall_results

def print_results(results: Dict) -> None:
    """basic output function to print only necessary results"""
    print(f"Total citations: {results['total_citations']}")
    print(f"Correctly identified citations: {results['correct_citations']}")
    print(f"Overall accuracy: {results['overall_accuracy']:.2%}")
    print(f"Skipped folders due to missing files: {results['skipped_folders']}")

def main():
    papers_folder = "papers"
    
    # just to make sure, don't want to cause any issues if its ran with another folder name
    if not os.path.exists(papers_folder):
        print(f"Error: '{papers_folder}' directory not found.")
        return
    
    results = evaluate_all_papers(papers_folder)
    
    # output total accuracy results
    print_results(results)

if __name__ == "__main__":
    main()
