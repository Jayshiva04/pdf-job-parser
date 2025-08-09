from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from pdf_parser import JobPDFParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Notification PDF Summarizer",
    description="FastAPI backend to extract and summarize key information from government job notification PDFs",
    version="1.0.0"
)

# --- CORRECTED CORS CONFIGURATION ---
# Be more explicit with the allowed origins
origins = [
    "http://localhost:3000",
    "https://pdf-job-parser-frontend-dn9v.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- THE REST OF YOUR CODE REMAINS THE SAME ---

class JobInfo(BaseModel):
    job_title: Optional[str] = Field(None, description="Job title or position name")
    department: Optional[str] = Field(None, description="Department or organization")
    vacancies: Optional[str] = Field(None, description="Number of vacancies")
    eligibility: Optional[str] = Field(None, description="Eligibility criteria")
    salary: Optional[str] = Field(None, description="Salary or pay scale")
    application_deadline: Optional[str] = Field(None, description="Application deadline")
    application_url: Optional[str] = Field(None, description="Application URL or website")
    raw_text: Optional[str] = Field(None, description="Raw extracted text (first 1000 chars)")

class JobSummaryResponse(BaseModel):
    success: bool
    data: Optional[JobInfo] = None
    error: Optional[str] = None
    extraction_summary: Optional[Dict[str, Any]] = None

# Initialize PDF parser
pdf_parser = JobPDFParser()

@app.get("/")
async def root():
    return {
        "message": "Job Notification PDF Summarizer API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "/parse-pdf": "POST - Upload and parse PDF file",
            "/health": "GET - Health check endpoint"
        },
        "features": [
            "PDF text extraction using PyMuPDF",
            "Advanced pattern matching for job details",
            "Structured JSON output"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "parser": "PyMuPDF (fitz)",
        "version": "1.0.0"
    }

@app.post("/parse-pdf", response_model=JobSummaryResponse)
async def parse_pdf(file: UploadFile = File(...)):
    """
    Parse a PDF file and extract job information
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
            
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
        
        logger.info(f"Parsing PDF: {file.filename}, Size: {len(content)} bytes")
        
        job_info_dict = pdf_parser.parse_pdf(content)
        
        extraction_summary = {
            "file_name": file.filename,
            "file_size_bytes": len(content),
            "text_length": len(job_info_dict.get('raw_text', '')),
            "extracted_fields": {
                field: bool(value and str(value).strip()) 
                for field, value in job_info_dict.items() 
                if field != 'raw_text'
            },
            "parsing_timestamp": datetime.now().isoformat()
        }
        
        job_info = JobInfo(**job_info_dict)
        
        logger.info(f"Successfully parsed PDF: {file.filename}")
        
        return JobSummaryResponse(
            success=True,
            data=job_info,
            extraction_summary=extraction_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error parsing PDF: {str(e)}"
        logger.error(error_msg)
        return JobSummaryResponse(
            success=False,
            error=error_msg
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)