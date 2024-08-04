import requests
import pandas as pd
from tqdm import tqdm
import fitz  # PyMuPDF
from groq import Groq
import time
import pdfplumber
from io import BytesIO
import threading

def format_query_string(input_string):
    words = input_string.split()
    if len(words) == 1:
        return input_string
    else:
        return '%20'.join(words)

def process_results(json_data):
    result_details = []
    results = json_data.get('results', [])
    
    for result in results:
        response = result.get('response', {})
        
        details = {
            "doi": response.get('doi'),
            "doi_url": response.get('doi_url'),
            "url": response.get('best_oa_location', {}).get('url'),
            "url_for_landing_page": response.get('best_oa_location', {}).get('url_for_landing_page'),
            "url_for_pdf": response.get('best_oa_location', {}).get('url_for_pdf'),
            "published_date": response.get('published_date'),
            "publisher": response.get('publisher'),
            "title": response.get('title'),
            "journal_name": response.get('journal_name'),
            "journal_issns": response.get('journal_issns'),
            "updated": response.get('updated'),
            "year": response.get('year')
        }
        
        result_details.append(details)
    
    return result_details

def get_results(api_url, max_pages=4):
    all_results = []
    for page in range(1, max_pages + 1):
        paginated_url = f"{api_url}&page={page}"
        print(f"Fetching data from the API, page {page}...")
        response = requests.get(paginated_url)
        
        if response.status_code == 200:
            data = response.json()
            results = process_results(data)
            all_results.extend(results)
        else:
            #print(f"Error: Unable to fetch data from the API on page {page}")
            break
    
    return all_results

class TimeoutError(Exception):
    pass

def extract_text_from_pdf(pdf_url):
    def get_pdf_content(url):
        try:
            response = requests.get(url, stream=True, timeout=30)  # Timeout for individual request
            response.raise_for_status()  # Check for HTTP errors
            if 'pdf' not in response.headers.get('Content-Type', '').lower():
                return None  # Not a PDF
            return response.content
        except requests.RequestException as e:
            # Log request error
            #print(f"Error fetching PDF from URL: {e}")
            return None

    def extract_text_with_pymupdf(pdf_content):
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text if text.strip() else None
        except Exception as e:
            # Log extraction error
            #print(f"Error extracting text with PyMuPDF: {e}")
            return None

    def extract_text_with_pdfplumber(pdf_content):
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text if text.strip() else None
        except Exception as e:
            # Log extraction error
            #print(f"Error extracting text with pdfplumber: {e}")
            return None

    # Function to run with timeout
    def run_with_timeout(func, args, timeout):
        result = [None]

        def target():
            result[0] = func(*args)

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError("Function execution timed out")

        return result[0]

    try:
        # Step 1: Get PDF content from URL with timeout
        pdf_content = run_with_timeout(get_pdf_content, (pdf_url,), 30)
        if not pdf_content:
            return None

        # Step 2: Try extracting text with different methods
        extraction_methods = [extract_text_with_pymupdf, extract_text_with_pdfplumber]
        for method in extraction_methods:
            text = method(pdf_content)
            if text:
                return text

        # If all methods fail, return None
        return None

    except TimeoutError:
        #print("Function execution timed out")
        return None


def summarize_text(text, client):
    time.sleep(3)
    try:
        excerpt = text[:1000] if len(text) > 1000 else text
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f'''You are given the first few pages of a scholarly article. 
                                    Your job is to PREPARE AN ABSTRACT in 50-60 words which should as include the topics disscused, challenges adressed,
                                    and other important information as given to you. DO NOT MENTION YOU ARE PREPARING AN ABSTRACT FROM A GIVEN TEXT.
                                    
                                    Only answer from the details we provide to you below. Be confident in the details you include or you may choose not to include.
                                    Also strictly follow the output pattern.

                                    Here is a the first few pages of the pdf: {excerpt}
                                    
                                    Output:

                                    "Abstract:
                                    The scholarly article discusses various .......
                                     
                                    
                                    "
                                    ''',
                }
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def processs(query):
    f_query = format_query_string(query)

    api_url = f"https://api.unpaywall.org/v2/search?query={f_query}&is_oa=true&email=research@kreat.ai"

    results = get_results(api_url, max_pages=4)

    if results is not None:
        print("Converting results to DataFrame...")
        df = pd.DataFrame(results)

        print("Extracting text from PDFs...")
        tqdm.pandas(desc="Processing PDFs")
        df['pdf_text'] = df['url_for_pdf'].progress_apply(extract_text_from_pdf)

        # Insert NA values where text extraction failed
        df['pdf_text'] = df['pdf_text'].apply(lambda x: x if x is not None else pd.NA)

        # Initialize the Groq client
        client = Groq(api_key='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')

        print("Generating summaries for PDFs...")
        df['summary'] = df['pdf_text'].progress_apply(lambda text: summarize_text(text, client) if text is not pd.NA else pd.NA)

        # Filter out rows where 'pdf_text' is NA
        df = df[df['pdf_text'].notna()]

        output_csv = f"{query}.csv"
        print(f"Saving results to {output_csv}...")
        df.to_csv(output_csv, index=False)

        print("Process completed successfully.")

def main():
    queries = ['Electric Vehicle','Electric Vehicle Battery','Lithium Battery Electric Vehicle','Hydrogen Cell']
    for query in queries:
        processs(query)


if __name__ == "__main__":
    main()
