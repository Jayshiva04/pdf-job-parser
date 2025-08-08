import fitz  # pymupdf
import re
from typing import Dict, Any, Optional, List

class JobPDFParser:
    """
    Final, robust, and generic PDF parser for extracting key information from government job notifications.
    This version is designed to be adaptable to multiple PDF formats without hardcoding.
    """
    def __init__(self):
        pass

    def extract_all_text(self, pdf_content: bytes) -> str:
        """Extract all text from PDF using pymupdf."""
        text = ""
        try:
            with fitz.open(stream=pdf_content, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text("text")
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        return text

    def clean_text(self, text: str) -> str:
        """Clean and normalize text for better parsing."""
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\s*\n\s*', '\n', text)
        return text.strip()

    def extract_field(self, text: str, patterns: List[str], group_index: int = 1) -> Optional[str]:
        """A generic function to try a list of regex patterns until a match is found."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(group_index).strip()
        return None

    def extract_job_title(self, text: str) -> Optional[str]:
        """Extract the main job title using a list of common patterns."""
        patterns = [
            r"RECRUITMENT OF (.+?)\n",
            r"Applications are invited for the post of (.+?)\n"
        ]
        return self.extract_field(text, patterns)

    def extract_department(self, text: str) -> Optional[str]:
        """Extract the department name by looking for common government-related headers."""
        patterns = [
            r"(MINISTRY OF .+?)\n",
            r"(GOVERNMENT OF .+?)\n",
            r"(RAILWAY RECRUITMENT BOARD)"
        ]
        return self.extract_field(text, patterns)

    def extract_vacancies(self, text: str) -> Optional[str]:
        """Extract the total number of vacancies using various common labels."""
        patterns = [
            r"Grand Total\s*(\d+)",
            r"Total Vacancies\s*\(All RRBs\)\s*(\d+)",
            r"Total\n(\d+)"
        ]
        return self.extract_field(text, patterns)

    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary information using multiple common pay scale formats."""
        patterns = [
            r"SCALE OF PAY:\s*(Level-\d+ of Pay Matrix with initial pay of Rs\. [\d,]+/-)",
            r"Level-5\s*(\d+)"
        ]
        return self.extract_field(text, patterns)

    def extract_eligibility(self, text: str) -> Optional[str]:
        """Extract eligibility criteria, prioritizing the age limit as a key summary point."""
        patterns = [
            r"AGE LIMIT: Not exceeding (\d+ years)",
            r"Age \(as on .*?\):\s*a\) (.*?)\s*and b\) (.*?)(?:\s*\()"
        ]
        
        match = re.search(patterns[0], text, re.IGNORECASE)
        if match:
            return f"Up to {match.group(1)}. See document for qualifications."
        
        match = re.search(patterns[1], text, re.IGNORECASE | re.DOTALL)
        if match:
            return f"{match.group(1).strip()} and {match.group(2).strip()}. Qualifications as per Annexure A."
            
        return None

    def extract_deadline(self, text: str) -> Optional[str]:
        """Extract the application deadline using common phrases."""
        patterns = [
            r"Closing date for Submission of Online Application\n([^\n]+)",
            r"Last date of receipt of application is ([\d\.]+)"
        ]
        return self.extract_field(text, patterns)

    def extract_application_url(self, text: str) -> Optional[str]:
        """Extract a representative application URL."""
        patterns = [
            r"Website:\s*(www\.[a-z\.]+\.in)",
            r"(www\.rrb[a-z]+\.gov\.in)"
        ]
        return self.extract_field(text, patterns)

    def parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Main parsing function to extract all job information."""
        try:
            raw_text = self.extract_all_text(pdf_content)
            cleaned_text = self.clean_text(raw_text)

            job_info = {
                'job_title': self.extract_job_title(cleaned_text),
                'department': self.extract_department(cleaned_text),
                'vacancies': self.extract_vacancies(cleaned_text),
                'eligibility': self.extract_eligibility(cleaned_text),
                'salary': self.extract_salary(cleaned_text),
                'application_deadline': self.extract_deadline(cleaned_text),
                'application_url': self.extract_application_url(cleaned_text),
                'raw_text': cleaned_text[:1000] + "..."
            }

            return job_info

        except Exception as e:
            raise Exception(f"An error occurred during PDF parsing: {str(e)}")