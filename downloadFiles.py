import requests
import time
import xml.etree.ElementTree as ET
import csv

BASE_URL = "http://export.arxiv.org/api/query?"
CATEGORY = "cs"  # Computer Science
START_DATE = "2025-02-01"
END_DATE = "2025-02-29"
MAX_RESULTS = 300  # max allowed per request
PDF_DOWNLOAD = False  # Set True if you want to download PDFs

def parse_entry(entry):
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
    title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
    summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
    published = entry.find('atom:published', ns).text
    authors = ', '.join([author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)])
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return arxiv_id, title, summary, published, authors, pdf_url

def fetch_papers():
    results = []
    start = 0
    total_results = 1  # just to enter the loop

    while start < total_results:
        query = f"search_query=cat:{CATEGORY}+AND+submittedDate:[202502010000+TO+202502292359]&start={start}&max_results={MAX_RESULTS}"
        response = requests.get(BASE_URL + query)
        root = ET.fromstring(response.content)

        if start == 0:
            total_results_tag = root.find('{http://a9.com/-/spec/opensearch/1.1/}totalResults')
            total_results = int(total_results_tag.text)
            print(f"Total results: {total_results}")

        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            results.append(parse_entry(entry))

        print(f"Fetched {len(results)} of {total_results}")
        start += MAX_RESULTS
        time.sleep(3)  # be polite to the server

    return results

def save_to_csv(papers, filename='cs_papers_feb_2025.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ArXiv ID', 'Title', 'Summary', 'Published Date', 'Authors', 'PDF URL'])
        writer.writerows(papers)
    print(f"Saved {len(papers)} papers to {filename}")

def download_pdfs(papers, folder='pdfs'):
    import os
    os.makedirs(folder, exist_ok=True)
    for arxiv_id, _, _, _, _, pdf_url in papers:
        pdf_path = os.path.join(folder, f"{arxiv_id}.pdf")
        if not os.path.exists(pdf_path):
            print(f"Downloading {arxiv_id}...")
            r = requests.get(pdf_url)
            with open(pdf_path, 'wb') as f:
                f.write(r.content)
            time.sleep(2)

if __name__ == "__main__":
    papers = fetch_papers()
    save_to_csv(papers)
    if PDF_DOWNLOAD:
        download_pdfs(papers)
