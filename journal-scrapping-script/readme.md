# Journal Scraping Script

## Overview

This project focuses on scraping open access scholarly articles based on specific queries. It fetches articles through an API, extracts text from the PDFs, and summarizes the content. The goal is to provide concise abstracts for easy reference and analysis.

## Requirements

- Python 3.7+
- `requests`
- `pandas`
- `tqdm`
- `fitz` (PyMuPDF)
- `pdfplumber`
- `Groq` (Groq API Client)

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/yourrepository.git
    cd yourrepository
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    **`requirements.txt` content:**

    ```plaintext
    requests
    pandas
    tqdm
    PyMuPDF
    pdfplumber
    groq
    ```

## Usage

1. **Define your queries:**

    Modify the `queries` list in the `main` function to include your desired search terms.

2. **Run the script:**

    ```bash
    python script_name.py
    ```

    The script will perform the following steps for each query:
    - Format the query string.
    - Fetch results from the Unpaywall API.
    - Extract text from the PDFs using PyMuPDF and pdfplumber.
    - Summarize the extracted text.
    - Save the results to a CSV file named after the query.

## Functions

- `format_query_string(input_string)`: Formats the input string for URL usage, replacing spaces with `%20`.

- `process_results(json_data)`: Processes JSON data from the API response and extracts relevant details such as DOI, URL, published date, publisher, title, journal name, and more.

- `get_results(api_url, max_pages=4)`: Fetches results from the API with pagination. It retrieves data for up to `max_pages` pages and processes the results.

- `extract_text_from_pdf(pdf_url)`: Extracts text from a PDF using multiple methods (PyMuPDF and pdfplumber) with a timeout to ensure the process doesn't hang indefinitely.

- `summarize_text(text, client)`: Generates a summary for the provided text using the Groq API. The summary is an abstract that includes topics discussed, challenges addressed, and other important information.

- `processs(query)`: Executes the entire process for a given query. It formats the query, fetches results, extracts text from PDFs, generates summaries, and saves the results to a CSV file.

- `main()`: The main function that iterates over a list of queries and processes each one using the `processs` function.

---