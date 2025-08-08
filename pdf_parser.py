import fitz  # pymupdf
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import io
import logging

class JobPDFParser:
    """
    Advanced PDF parser for extracting job information from government job notifications using pymupdf (fitz)
    """
    def __init__(self):
        # Enhanced job title patterns
        self.job_title_keywords = [
            'OFFICER', 'ASSISTANT', 'MANAGER', 'DIRECTOR', 'ENGINEER', 
            'SPECIALIST', 'COORDINATOR', 'ADMINISTRATOR', 'CLERK', 
            'SUPERVISOR', 'ANALYST', 'CONSULTANT', 'ADVISOR', 'EXECUTIVE',
            'LECTURER', 'PROFESSOR', 'RESEARCHER', 'SCIENTIST', 'TECHNICIAN',
            'OPERATOR', 'DRIVER', 'GUARD', 'ATTENDANT', 'HELPER', 'WORKER',
            'INSPECTOR', 'JUNIOR', 'SENIOR', 'CHIEF', 'HEAD', 'DEPUTY'
        ]
        
        # Common government departments/organizations
        self.dept_keywords = [
            'RAILWAY', 'RAILWAYS', 'INDIAN RAILWAY', 'MINISTRY', 'DEPARTMENT',
            'BOARD', 'COMMISSION', 'CORPORATION', 'AUTHORITY', 'ORGANIZATION',
            'GOVERNMENT', 'CENTRAL', 'STATE', 'NATIONAL', 'PUBLIC SECTOR'
        ]

    def extract_all_text(self, pdf_content: bytes) -> str:
        """Extract all text from PDF using pymupdf"""
        text = []
        try:
            with fitz.open(stream=pdf_content, filetype="pdf") as doc:
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text.append(page_text)
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        return '\n'.join(text)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace and normalize
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and common PDF artifacts
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()

    def find_document_title(self, text: str) -> Optional[str]:
        """Extract the main document title/CEN number"""
        patterns = [
            r'CEN\s+NO\.?\s*(\d+/\d+)\s*\([^)]+\)',  # CEN NO. 02/2025 (TECHNICIAN CATEGORIES)
            r'NOTIFICATION\s+NO\.?\s*([^\n]+)',
            r'ADVERTISEMENT\s+NO\.?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def extract_job_title(self, text: str) -> Optional[str]:
        """Extract job title with improved logic"""
        # First, try to find the document title which often contains job category
        doc_title = self.find_document_title(text)
        if doc_title and '(' in doc_title:
            # Extract category from parentheses like "CEN NO. 02/2025 (TECHNICIAN CATEGORIES)"
            category_match = re.search(r'\(([^)]+)\)', doc_title)
            if category_match:
                category = category_match.group(1).strip()
                if len(category) > 5 and not category.isdigit():
                    return category
        
        # Look for specific job title patterns in vacancies section
        patterns = [
            # Pattern for "Name of Post" or similar in tables/sections
            r'(?:Name\s+of\s+(?:Post|Position)|Post\s+Name)[\s:]*([^\n\r]+?)(?=\s+(?:Grade|Level|Scale|\d|$))',
            
            # Pattern for job categories in headers
            r'(?:RECRUITMENT|NOTIFICATION|ADVERTISEMENT)\s+(?:FOR|OF)\s+([A-Z\s]+?)(?:POSTS?|CATEGORIES?)',
            
            # Pattern for direct job mentions
            r'(?:Applications?\s+(?:are\s+)?invited\s+for|Recruitment\s+to)\s+(?:the\s+)?(?:post\s+of\s+)?([A-Z][A-Z\s,-]+?)(?:\s+in|\s+under|\s+at|\.|$)',
            
            # Pattern for vacancy announcements
            r'VACANCY\s+(?:FOR|OF)\s+([A-Z][A-Z\s]+?)(?:\s+POST|\s+IN|\.|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    title = match.strip()
                    # Clean and validate the title
                    title = re.sub(r'\s+', ' ', title)
                    if (len(title) > 5 and 
                        not re.match(r'^\d+', title) and 
                        any(keyword in title.upper() for keyword in self.job_title_keywords)):
                        return title
        
        return None

    def extract_department(self, text: str) -> Optional[str]:
        """Extract department/organization information"""
        patterns = [
            # Railway patterns - simplified to avoid verbose definitions
            r'(RAILWAY\s+RECRUITMENT\s+BOARD)(?:\s|,|\n)',
            r'(RAILWAY\s+RECRUITMENT\s+CELL)(?:\s|,|\n)',
            r'(INDIAN\s+RAILWAYS?)(?:\s|,|\n)',
            
            # Ministry patterns
            r'(MINISTRY\s+OF\s+[A-Z\s&,]+?)(?:\s*,|\s*\n|\s*invites?)',
            
            # Department patterns
            r'(DEPARTMENT\s+OF\s+[A-Z\s&,]+?)(?:\s*,|\s*\n|\s*invites?)',
            
            # Organization patterns - shorter matches
            r'([A-Z\s]+(?:COMMISSION|BOARD|CORPORATION|AUTHORITY))(?:\s|,|\n)',
            
            # Government entity patterns
            r'(GOVERNMENT\s+OF\s+[A-Z\s]+?)(?:\s*,|\s*\n)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    dept = match.strip()
                    # Clean the department name and limit length
                    dept = re.sub(r'\s+', ' ', dept)
                    dept = re.sub(r'[,\n\r]+', '', dept)

    def extract_vacancies(self, text: str) -> Optional[str]:
        """Extract vacancy information with improved parsing"""
        # Look for vacancy sections or tables
        vacancy_section = self.extract_section_content(text, ['VACANCIES', 'VACANCY', 'NUMBER OF POSTS'])
        
        if vacancy_section:
            search_text = vacancy_section
        else:
            search_text = text
        
        patterns = [
            # Grand Total pattern (most accurate)
            r'Grand\s+Total[\s:]*(\d+)',
            
            # Total vacancies pattern
            r'Total\s+Vacancies\s+\(All\s+RRBs?\)[\s:]*(\d+)',
            
            # General total patterns
            r'(?:Total\s+)?(?:Vacancies?|Posts?|Positions?)[\s:]*(\d+)',
            
            # Number in vacancy announcements
            r'(\d+)\s+(?:Vacancies?|Posts?|Positions?)',
            
            # Specific vacancy mentions
            r'(?:Total\s+)?(?:No\.?\s+of\s+)?(?:Vacancies?|Posts?)[\s:]*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                # Return the highest valid number found (likely to be total)
                valid_numbers = [int(match) for match in matches if match.isdigit() and int(match) > 0]
                if valid_numbers:
                    return str(max(valid_numbers))
        
        return None

    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary/pay scale information"""
        # Look in specific sections first
        salary_section = self.extract_section_content(text, ['PAY SCALE', 'SALARY', 'PAY BAND', 'REMUNERATION'])
        
        if salary_section:
            search_text = salary_section
        else:
            search_text = text
        
        patterns = [
            # Pay Level with initial pay (7th Pay Commission format)
            r'Pay\s+Level[\s-]*(\d+)[\s\S]*?Initial\s+pay[^\d]*(\d+)',
            r'Level[\s-]*(\d+)[\s\S]*?(\d+)[\s\S]*?B-\d+',  # Level-5 29200 B-1 format
            
            # Pay Level patterns (7th Pay Commission)
            r'(?:Pay\s+)?Level[\s-]*(\d+)(?:\s+of\s+7th\s+Pay\s+Commission)?',
            
            # Pay Band patterns
            r'(?:Pay\s+Band|PB)[\s-]*(\d+)[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
            
            # Direct salary ranges with Rs.
            r'(?:Rs\.?|₹)\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)(?:\s*(?:per\s+month|p\.m\.?))?',
            
            # Scale patterns
            r'(?:Pay\s+)?Scale[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # For patterns that capture multiple groups (Level + Pay)
                    level, pay = matches[0]
                    if level and pay:
                        return f"Level-{level} (Rs. {pay})"
                    elif level:
                        return f"Level-{level}"
                    elif pay:
                        return f"Rs. {pay}"
                else:
                    return matches[0].strip()
        
        return None

    def extract_eligibility(self, text: str) -> Optional[str]:
        """Extract eligibility criteria"""
        # Look in specific sections first
        eligibility_section = self.extract_section_content(text, 
            ['EDUCATIONAL QUALIFICATIONS', 'ELIGIBILITY', 'QUALIFICATION', 'ESSENTIAL QUALIFICATIONS'])
        
        if eligibility_section:
            search_text = eligibility_section
        else:
            search_text = text
        
        patterns = [
            # Age requirement patterns (common in job notifications)
            r'Age\s+\(as\s+on[^)]+\):\s*([^.\n]+)',
            
            # Educational qualification patterns  
            r'(?:Essential\s+)?(?:Educational\s+)?(?:Qualification|Eligibility)[\s:]*([^.\n]+\.)',
            
            # Specific qualification requirements from tables
            r'(?:ITI|Diploma|Degree|Certificate|Course\s+Completed\s+Act\s+Apprenticeship)[^.\n]*',
            
            # Age limits for specific posts
            r'(\d{1,2}\s*(?:to|–|-)\s*\d{1,2}\s+years?\s+for\s+[A-Z][^.\n]+)',
            
            # Technical qualification mentions
            r'((?:ITI|Industrial\s+Training\s+Institute|Course\s+Completed\s+Act\s+Apprenticeship|CCAA)[^.\n]*)',
            
            # General eligibility patterns
            r'(?:Candidates?\s+(?:should|must)\s+(?:have|possess)\s+)([^.\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    eligibility = match.strip()
                    # Clean the eligibility text
                    eligibility = re.sub(r'\s+', ' ', eligibility)
                    eligibility = re.sub(r'[.\n\r]+$', '', eligibility)

    def extract_deadline(self, text: str) -> Optional[str]:
        """Extract application deadline"""
        # Look in important dates section first
        dates_section = self.extract_section_content(text, ['IMPORTANT DATES', 'DATES', 'LAST DATE'])
        
        if dates_section:
            search_text = dates_section
        else:
            search_text = text
        
        patterns = [
            # Most specific pattern for online application deadline
            r'(?:Applications?\s+complete\s+in\s+all\s+respects\s+must\s+be\s+submitted\s+ONLINE\s+ONLY\s+latest\s+by\s+)([^\n\r.]+)',
            
            # Last date for submission pattern
            r'(?:Last\s+date\s+)?for\s+Submission\s+of\s+Online\s+Application\s+(\d{1,2}-\d{1,2}-\d{4})\s*\(([^)]+)\)',
            
            # Simple date with time pattern
            r'(\d{1,2}-\d{1,2}-\d{4})\s+\((\d{1,2}:\d{2}\s+hours?)\)',
            
            # Specific date formats
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            
            # Month name dates
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # For patterns with multiple groups (date + time)
                    date_part = matches[0][0].strip()
                    time_part = matches[0][1].strip() if len(matches[0]) > 1 else ""
                    if time_part:
                        return f"{date_part} ({time_part})"
                    else:
                        return date_part
                else:
                    deadline = matches[0].strip()
                    # Clean and limit the deadline length
                    deadline = re.sub(r'\s+', ' ', deadline)
                    if 8 <= len(deadline) <= 50:  # Reasonable deadline length
                        return deadline
        
        return None

    def extract_application_url(self, text: str) -> Optional[str]:
        """Extract application URL or website"""
        patterns = [
            # Direct URLs
            r'(https?://[^\s\n\r]+)',
            
            # Website patterns
            r'(?:Website|Portal|URL)[\s:]*([^\s\n\r]+)',
            
            # www patterns
            r'(www\.[^\s\n\r]+)',
            
            # Apply online patterns
            r'(?:Apply\s+online\s+at|Online\s+application)[\s:]*([^\s\n\r]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0].strip()
                # Basic URL validation
                if '.' in url and len(url) > 5:
                    return url
        
        return None

    def extract_section_content(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract content from specific sections"""
        for section_name in section_names:
            # Create pattern to match section header
            pattern = rf'(?:^|\n)\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n\s*[A-Z][A-Z\s]*[:\n]|\n\s*\d+\.|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if len(section_content) > 20:  # Ensure meaningful content
                    return section_content
        return None

    def parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Main parsing function with improved extraction logic"""
        try:
            # Extract and clean text
            raw_text = self.extract_all_text(pdf_content)
            if not raw_text.strip():
                raise Exception("Could not extract text from PDF")
            
            cleaned_text = self.clean_text(raw_text)
            
            # Extract information using improved methods
            job_info = {
                'job_title': self.extract_job_title(cleaned_text),
                'department': self.extract_department(cleaned_text),
                'vacancies': self.extract_vacancies(cleaned_text),
                'eligibility': self.extract_eligibility(cleaned_text),
                'salary': self.extract_salary(cleaned_text),
                'application_deadline': self.extract_deadline(cleaned_text),
                'application_url': self.extract_application_url(cleaned_text),
                'raw_text': cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text
            }
            
            return job_info
            
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
                    # Avoid overly long matches with definitions
            if 5 < len(dept) < 50 and not re.search(r'[=:]', dept):
                        return dept
        
        return None

    def extract_vacancies(self, text: str) -> Optional[str]:
        """Extract vacancy information with improved parsing"""
        # Look for vacancy sections or tables
        vacancy_section = self.extract_section_content(text, ['VACANCIES', 'VACANCY', 'NUMBER OF POSTS'])
        
        if vacancy_section:
            text = vacancy_section
        
        patterns = [
            # Total vacancies pattern
            r'(?:Total\s+)?(?:Vacancies?|Posts?|Positions?)[\s:]*(\d+)',
            
            # Number in vacancy announcements
            r'(\d+)\s+(?:Vacancies?|Posts?|Positions?)',
            
            # Specific vacancy mentions
            r'(?:Total\s+)?(?:No\.?\s+of\s+)?(?:Vacancies?|Posts?)[\s:]*(\d+)',
            
            # Pattern for vacancy breakdowns (get total if available)
            r'(?:Grand\s+)?Total[\s:]*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first valid number found
                for match in matches:
                    if match.isdigit() and int(match) > 0:
                        return match
        
        return None

    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary/pay scale information"""
        # Look in specific sections first
        salary_section = self.extract_section_content(text, ['PAY SCALE', 'SALARY', 'PAY BAND', 'REMUNERATION'])
        
        if salary_section:
            search_text = salary_section
        else:
            search_text = text
        
        patterns = [
            # Pay Level patterns (7th Pay Commission)
            r'(?:Pay\s+)?Level[\s-]*(\d+)(?:\s+of\s+7th\s+Pay\s+Commission)?',
            
            # Pay Band patterns
            r'(?:Pay\s+Band|PB)[\s-]*(\d+)[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
            
            # Direct salary ranges
            r'(?:Rs\.?|₹)\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)(?:\s*(?:per\s+month|p\.m\.?))?',
            
            # Scale patterns
            r'(?:Pay\s+)?Scale[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
            
            # Basic pay patterns
            r'Basic\s+Pay[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # For patterns that capture multiple groups
                    salary_parts = [part for part in matches[0] if part.strip()]
                    return ' '.join(salary_parts)
                else:
                    return matches[0].strip()
        
        return None

    def extract_eligibility(self, text: str) -> Optional[str]:
        """Extract eligibility criteria"""
        # Look in specific sections
        eligibility_section = self.extract_section_content(text, 
            ['EDUCATIONAL QUALIFICATIONS', 'ELIGIBILITY', 'QUALIFICATION', 'ESSENTIAL QUALIFICATIONS'])
        
        if eligibility_section:
            search_text = eligibility_section
        else:
            search_text = text
        
        patterns = [
            # Educational qualification patterns
            r'(?:Essential\s+)?(?:Educational\s+)?(?:Qualification|Eligibility)[\s:]*([^.\n]+(?:\.|$))',
            
            # Degree patterns
            r'((?:Bachelor|Master|Graduate|Post\s+Graduate)[^.\n]+)',
            
            # Specific qualification mentions
            r'(?:Candidates?\s+(?:should|must)\s+(?:have|possess)\s+)([^.\n]+)',
            
            # ITI/Diploma patterns
            r'((?:ITI|Diploma|Certificate)[^.\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                eligibility = matches[0].strip()
                # Clean the eligibility text
                eligibility = re.sub(r'\s+', ' ', eligibility)
                eligibility = re.sub(r'[.\n\r]+$', '', eligibility)
                if len(eligibility) > 10:
                    return eligibility
        
        return None

    def extract_deadline(self, text: str) -> Optional[str]:
        """Extract application deadline"""
        # Look in important dates section first
        dates_section = self.extract_section_content(text, ['IMPORTANT DATES', 'DATES', 'LAST DATE'])
        
        if dates_section:
            search_text = dates_section
        else:
            search_text = text
        
        patterns = [
            # Last date patterns
            r'(?:Last\s+date|Closing\s+date|End\s+date)[\s:]*([^\n\r]+?)(?=\s*\n|$)',
            
            # Online application deadline
            r'(?:Last\s+date\s+for\s+)?(?:Online\s+)?(?:Application|Submission)[\s:]*([^\n\r]+?)(?=\s*\n|$)',
            
            # Specific date formats
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            
            # Date with time
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+(?:up\s+to\s+)?\d{1,2}:\d{2}\s*(?:hrs?|hours?)?)',
            
            # Month name dates
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{2,4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                deadline = matches[0].strip()
                # Clean the deadline
                deadline = re.sub(r'\s+', ' ', deadline)
                if len(deadline) > 5:
                    return deadline
        
        return None

    def extract_application_url(self, text: str) -> Optional[str]:
        """Extract application URL or website"""
        patterns = [
            # Direct URLs
            r'(https?://[^\s\n\r]+)',
            
            # Website patterns
            r'(?:Website|Portal|URL)[\s:]*([^\s\n\r]+)',
            
            # www patterns
            r'(www\.[^\s\n\r]+)',
            
            # Apply online patterns
            r'(?:Apply\s+online\s+at|Online\s+application)[\s:]*([^\s\n\r]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0].strip()
                # Basic URL validation
                if '.' in url and len(url) > 5:
                    return url
        
        return None

    def extract_section_content(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract content from specific sections"""
        for section_name in section_names:
            # Create pattern to match section header
            pattern = rf'(?:^|\n)\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n\s*[A-Z][A-Z\s]*[:\n]|\n\s*\d+\.|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if len(section_content) > 20:  # Ensure meaningful content
                    return section_content
        return None

    def parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Main parsing function with improved extraction logic"""
        try:
            # Extract and clean text
            raw_text = self.extract_all_text(pdf_content)
            if not raw_text.strip():
                raise Exception("Could not extract text from PDF")
            
            cleaned_text = self.clean_text(raw_text)
            
            # Extract information using improved methods
            job_info = {
                'job_title': self.extract_job_title(cleaned_text),
                'department': self.extract_department(cleaned_text),
                'vacancies': self.extract_vacancies(cleaned_text),
                'eligibility': self.extract_eligibility(cleaned_text),
                'salary': self.extract_salary(cleaned_text),
                'application_deadline': self.extract_deadline(cleaned_text),
                'application_url': self.extract_application_url(cleaned_text),
                'raw_text': cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text
            }
            
            return job_info
            
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
                    # Ensure meaningful content and reasonable length
            if 15 <= len(eligibility) <= 200 and not eligibility.startswith('Graduate Act apprentice'):
                        return eligibility
        
        # Fallback: Extract age requirements which are always present
        age_pattern = r'(\d{1,2}\s*–\s*\d{1,2}\s+years)'
        age_matches = re.findall(age_pattern, text)
        if age_matches:
            return f"Age: {age_matches[0]}"
        
        return None

    def extract_deadline(self, text: str) -> Optional[str]:
        """Extract application deadline"""
        # Look in important dates section first
        dates_section = self.extract_section_content(text, ['IMPORTANT DATES', 'DATES', 'LAST DATE'])
        
        if dates_section:
            search_text = dates_section
        else:
            search_text = text
        
        patterns = [
            # Most specific pattern for online application deadline
            r'(?:Applications?\s+complete\s+in\s+all\s+respects\s+must\s+be\s+submitted\s+ONLINE\s+ONLY\s+latest\s+by\s+)([^\n\r.]+)',
            
            # Last date for submission pattern
            r'(?:Last\s+date\s+)?for\s+Submission\s+of\s+Online\s+Application\s+(\d{1,2}-\d{1,2}-\d{4})\s*\(([^)]+)\)',
            
            # Simple date with time pattern
            r'(\d{1,2}-\d{1,2}-\d{4})\s+\((\d{1,2}:\d{2}\s+hours?)\)',
            
            # Specific date formats
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            
            # Month name dates
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # For patterns with multiple groups (date + time)
                    date_part = matches[0][0].strip()
                    time_part = matches[0][1].strip() if len(matches[0]) > 1 else ""
                    if time_part:
                        return f"{date_part} ({time_part})"
                    else:
                        return date_part
                else:
                    deadline = matches[0].strip()
                    # Clean and limit the deadline length
                    deadline = re.sub(r'\s+', ' ', deadline)
                    if 8 <= len(deadline) <= 50:  # Reasonable deadline length
                        return deadline
        
        return None

    def extract_application_url(self, text: str) -> Optional[str]:
        """Extract application URL or website"""
        patterns = [
            # Direct URLs
            r'(https?://[^\s\n\r]+)',
            
            # Website patterns
            r'(?:Website|Portal|URL)[\s:]*([^\s\n\r]+)',
            
            # www patterns
            r'(www\.[^\s\n\r]+)',
            
            # Apply online patterns
            r'(?:Apply\s+online\s+at|Online\s+application)[\s:]*([^\s\n\r]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0].strip()
                # Basic URL validation
                if '.' in url and len(url) > 5:
                    return url
        
        return None

    def extract_section_content(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract content from specific sections"""
        for section_name in section_names:
            # Create pattern to match section header
            pattern = rf'(?:^|\n)\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n\s*[A-Z][A-Z\s]*[:\n]|\n\s*\d+\.|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if len(section_content) > 20:  # Ensure meaningful content
                    return section_content
        return None

    def parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Main parsing function with improved extraction logic"""
        try:
            # Extract and clean text
            raw_text = self.extract_all_text(pdf_content)
            if not raw_text.strip():
                raise Exception("Could not extract text from PDF")
            
            cleaned_text = self.clean_text(raw_text)
            
            # Extract information using improved methods
            job_info = {
                'job_title': self.extract_job_title(cleaned_text),
                'department': self.extract_department(cleaned_text),
                'vacancies': self.extract_vacancies(cleaned_text),
                'eligibility': self.extract_eligibility(cleaned_text),
                'salary': self.extract_salary(cleaned_text),
                'application_deadline': self.extract_deadline(cleaned_text),
                'application_url': self.extract_application_url(cleaned_text),
                'raw_text': cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text
            }
            
            return job_info
            
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
                    # Avoid overly long matches with definitions
            if 5 < len(dept) < 50 and not re.search(r'[=:]', dept):
                        return dept
        
        return None

    def extract_vacancies(self, text: str) -> Optional[str]:
        """Extract vacancy information with improved parsing"""
        # Look for vacancy sections or tables
        vacancy_section = self.extract_section_content(text, ['VACANCIES', 'VACANCY', 'NUMBER OF POSTS'])
        
        if vacancy_section:
            text = vacancy_section
        
        patterns = [
            # Total vacancies pattern
            r'(?:Total\s+)?(?:Vacancies?|Posts?|Positions?)[\s:]*(\d+)',
            
            # Number in vacancy announcements
            r'(\d+)\s+(?:Vacancies?|Posts?|Positions?)',
            
            # Specific vacancy mentions
            r'(?:Total\s+)?(?:No\.?\s+of\s+)?(?:Vacancies?|Posts?)[\s:]*(\d+)',
            
            # Pattern for vacancy breakdowns (get total if available)
            r'(?:Grand\s+)?Total[\s:]*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first valid number found
                for match in matches:
                    if match.isdigit() and int(match) > 0:
                        return match
        
        return None

    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary/pay scale information"""
        # Look in specific sections first
        salary_section = self.extract_section_content(text, ['PAY SCALE', 'SALARY', 'PAY BAND', 'REMUNERATION'])
        
        if salary_section:
            search_text = salary_section
        else:
            search_text = text
        
        patterns = [
            # Pay Level patterns (7th Pay Commission)
            r'(?:Pay\s+)?Level[\s-]*(\d+)(?:\s+of\s+7th\s+Pay\s+Commission)?',
            
            # Pay Band patterns
            r'(?:Pay\s+Band|PB)[\s-]*(\d+)[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
            
            # Direct salary ranges
            r'(?:Rs\.?|₹)\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)(?:\s*(?:per\s+month|p\.m\.?))?',
            
            # Scale patterns
            r'(?:Pay\s+)?Scale[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
            
            # Basic pay patterns
            r'Basic\s+Pay[\s:]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\s*-\s*[0-9,]+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # For patterns that capture multiple groups
                    salary_parts = [part for part in matches[0] if part.strip()]
                    return ' '.join(salary_parts)
                else:
                    return matches[0].strip()
        
        return None

    def extract_eligibility(self, text: str) -> Optional[str]:
        """Extract eligibility criteria"""
        # Look in specific sections
        eligibility_section = self.extract_section_content(text, 
            ['EDUCATIONAL QUALIFICATIONS', 'ELIGIBILITY', 'QUALIFICATION', 'ESSENTIAL QUALIFICATIONS'])
        
        if eligibility_section:
            search_text = eligibility_section
        else:
            search_text = text
        
        patterns = [
            # Educational qualification patterns
            r'(?:Essential\s+)?(?:Educational\s+)?(?:Qualification|Eligibility)[\s:]*([^.\n]+(?:\.|$))',
            
            # Degree patterns
            r'((?:Bachelor|Master|Graduate|Post\s+Graduate)[^.\n]+)',
            
            # Specific qualification mentions
            r'(?:Candidates?\s+(?:should|must)\s+(?:have|possess)\s+)([^.\n]+)',
            
            # ITI/Diploma patterns
            r'((?:ITI|Diploma|Certificate)[^.\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                eligibility = matches[0].strip()
                # Clean the eligibility text
                eligibility = re.sub(r'\s+', ' ', eligibility)
                eligibility = re.sub(r'[.\n\r]+$', '', eligibility)
                if len(eligibility) > 10:
                    return eligibility
        
        return None

    def extract_deadline(self, text: str) -> Optional[str]:
        """Extract application deadline"""
        # Look in important dates section first
        dates_section = self.extract_section_content(text, ['IMPORTANT DATES', 'DATES', 'LAST DATE'])
        
        if dates_section:
            search_text = dates_section
        else:
            search_text = text
        
        patterns = [
            # Last date patterns
            r'(?:Last\s+date|Closing\s+date|End\s+date)[\s:]*([^\n\r]+?)(?=\s*\n|$)',
            
            # Online application deadline
            r'(?:Last\s+date\s+for\s+)?(?:Online\s+)?(?:Application|Submission)[\s:]*([^\n\r]+?)(?=\s*\n|$)',
            
            # Specific date formats
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            
            # Date with time
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+(?:up\s+to\s+)?\d{1,2}:\d{2}\s*(?:hrs?|hours?)?)',
            
            # Month name dates
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{2,4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                deadline = matches[0].strip()
                # Clean the deadline
                deadline = re.sub(r'\s+', ' ', deadline)
                if len(deadline) > 5:
                    return deadline
        
        return None

    def extract_application_url(self, text: str) -> Optional[str]:
        """Extract application URL or website"""
        patterns = [
            # Direct URLs
            r'(https?://[^\s\n\r]+)',
            
            # Website patterns
            r'(?:Website|Portal|URL)[\s:]*([^\s\n\r]+)',
            
            # www patterns
            r'(www\.[^\s\n\r]+)',
            
            # Apply online patterns
            r'(?:Apply\s+online\s+at|Online\s+application)[\s:]*([^\s\n\r]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0].strip()
                # Basic URL validation
                if '.' in url and len(url) > 5:
                    return url
        
        return None

    def extract_section_content(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract content from specific sections"""
        for section_name in section_names:
            # Create pattern to match section header
            pattern = rf'(?:^|\n)\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n\s*[A-Z][A-Z\s]*[:\n]|\n\s*\d+\.|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if len(section_content) > 20:  # Ensure meaningful content
                    return section_content
        return None

    def parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Main parsing function with improved extraction logic"""
        try:
            # Extract and clean text
            raw_text = self.extract_all_text(pdf_content)
            if not raw_text.strip():
                raise Exception("Could not extract text from PDF")
            
            cleaned_text = self.clean_text(raw_text)
            
            # Extract information using improved methods
            job_info = {
                'job_title': self.extract_job_title(cleaned_text),
                'department': self.extract_department(cleaned_text),
                'vacancies': self.extract_vacancies(cleaned_text),
                'eligibility': self.extract_eligibility(cleaned_text),
                'salary': self.extract_salary(cleaned_text),
                'application_deadline': self.extract_deadline(cleaned_text),
                'application_url': self.extract_application_url(cleaned_text),
                'raw_text': cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text
            }
            
            return job_info
            
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")