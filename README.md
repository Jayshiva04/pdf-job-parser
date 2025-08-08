# Job Notification PDF Parser

A FastAPI backend designed to intelligently extract and summarize key information from various government job notification PDFs into a structured JSON format. This project uses a heuristic-based parsing approach with `PyMuPDF` to create a generic and adaptable solution.

## Features

  - **Dynamic PDF Parsing**: Extracts text from PDF documents using `PyMuPDF (fitz)`.
  - **Heuristic-Based Extraction**: Uses a list of adaptable regular expressions to find key information, rather than being hardcoded to a single format.
  - **Structured JSON Output**: Summarizes complex job notifications into a clean, easy-to-use JSON object.
  - **Adaptable Logic**: Designed to work across multiple job notification formats with a high degree of accuracy.
  - **FastAPI Backend**: Built with a modern, high-performance Python web framework.

## API Endpoints

| Method | Endpoint     | Description                                               |
| ------ | ------------ | --------------------------------------------------------- |
| `POST` | `/parse-pdf` | Upload a PDF file to extract and summarize job details.   |
| `GET`  | `/health`    | A simple health check endpoint to confirm the API is live. |
| `GET`  | `/`          | Returns a welcome message and basic API information.      |

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd pdf-job-parser
    ```

2.  **Create and activate a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the FastAPI server:**

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

    The API will be available at `http://localhost:8000`.

## Usage

You can test the main endpoint by sending a `POST` request with a PDF file.

### Example `curl` command:

```bash
curl -X POST "http://localhost:8000/parse-pdf" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/job_notification.pdf"
```