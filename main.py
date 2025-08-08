from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
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

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class TextParseRequest(BaseModel):
    text: str = Field(..., description="Text content to parse")

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
            "/parse-text": "POST - Parse text content",
            "/health": "GET - Health check endpoint"
        },
        "features": [
            "PDF text extraction using PyMuPDF",
            "Advanced pattern matching for job details",
            "Section-aware content extraction",
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
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
            
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check file size (limit to 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
        
        # Log parsing attempt
        logger.info(f"Parsing PDF: {file.filename}, Size: {len(content)} bytes")
        
        # Parse PDF using the improved parser
        job_info_dict = pdf_parser.parse_pdf(content)
        
        # Create extraction summary for debugging
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
        
        # Convert to JobInfo model
        job_info = JobInfo(**job_info_dict)
        
        logger.info(f"Successfully parsed PDF: {file.filename}")
        
        return JobSummaryResponse(
            success=True,
            data=job_info,
            extraction_summary=extraction_summary
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Error parsing PDF: {str(e)}"
        logger.error(error_msg)
        return JobSummaryResponse(
            success=False,
            error=error_msg
        )

@app.post("/parse-text", response_model=JobSummaryResponse)
async def parse_text(request: TextParseRequest):
    """
    Parse text content and extract job information
    """
    try:
        text = request.text
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text content is required")
        
        if len(text) > 100000:  # 100KB text limit
            raise HTTPException(status_code=400, detail="Text too long (max 100KB)")
        
        logger.info(f"Parsing text, Length: {len(text)} characters")
        
        # Use the parser's individual extraction methods
        job_info_dict = {
            'job_title': pdf_parser.extract_job_title(text),
            'department': pdf_parser.extract_department(text),
            'vacancies': pdf_parser.extract_vacancies(text),
            'eligibility': pdf_parser.extract_eligibility(text),
            'salary': pdf_parser.extract_salary(text),
            'application_deadline': pdf_parser.extract_deadline(text),
            'application_url': pdf_parser.extract_application_url(text),
            'raw_text': text[:1000] + "..." if len(text) > 1000 else text
        }
        
        # Create extraction summary
        extraction_summary = {
            "input_type": "text",
            "text_length": len(text),
            "extracted_fields": {
                field: bool(value and str(value).strip()) 
                for field, value in job_info_dict.items() 
                if field != 'raw_text'
            },
            "parsing_timestamp": datetime.now().isoformat()
        }
        
        job_info = JobInfo(**job_info_dict)
        
        logger.info("Successfully parsed text content")
        
        return JobSummaryResponse(
            success=True,
            data=job_info,
            extraction_summary=extraction_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error parsing text: {str(e)}"
        logger.error(error_msg)
        return JobSummaryResponse(
            success=False,
            error=error_msg
        )

@app.get("/test-extraction/{field}")
async def test_extraction(field: str, text: str = ""):
    """
    Test individual field extraction for debugging
    """
    if not text:
        return {"error": "Text parameter is required"}
    
    try:
        if field == "job_title":
            result = pdf_parser.extract_job_title(text)
        elif field == "department":
            result = pdf_parser.extract_department(text)
        elif field == "vacancies":
            result = pdf_parser.extract_vacancies(text)
        elif field == "eligibility":
            result = pdf_parser.extract_eligibility(text)
        elif field == "salary":
            result = pdf_parser.extract_salary(text)
        elif field == "deadline":
            result = pdf_parser.extract_deadline(text)
        elif field == "url":
            result = pdf_parser.extract_application_url(text)
        else:
            return {"error": f"Unknown field: {field}"}
        
        return {
            "field": field,
            "result": result,
            "found": bool(result),
            "text_length": len(text)
        }
    
    except Exception as e:
        return {"error": f"Error testing {field}: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)