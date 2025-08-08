#!/usr/bin/env python3
"""
Test script for the Job PDF Parser
This script demonstrates the parser functionality with sample job notification text.
"""

from pdf_parser import JobPDFParser
import json

def test_parser():
    """
    Test the PDF parser with sample job notification text
    """
    # Sample job notification text
    sample_text = """
    GOVERNMENT OF INDIA
    MINISTRY OF SCIENCE AND TECHNOLOGY
    
    RECRUITMENT NOTIFICATION
    
    Applications are invited for the post of RESEARCH SCIENTIST in the Department of Biotechnology.
    
    Job Title: Research Scientist
    Department: Department of Biotechnology
    Number of Posts: 5
    
    Essential Qualification: 
    - Ph.D. in Biotechnology or related field
    - Minimum 3 years of research experience
    
    Pay Scale: Level 10 (Rs. 56,100 - 1,77,500)
    
    Last Date for Application: 31st December 2024
    
    Apply Online at: https://www.dbt.gov.in/careers
    
    For more details, visit: www.dbt.gov.in
    """
    
    # Initialize parser
    parser = JobPDFParser()
    
    print("=== Job PDF Parser Test ===\n")
    print("Sample Job Notification Text:")
    print("-" * 50)
    print(sample_text)
    print("-" * 50)
    
    # Extract information
    print("\nExtracted Information:")
    print("-" * 50)
    
    job_title = parser.extract_job_title(sample_text)
    department = parser.extract_department(sample_text)
    vacancies = parser.extract_vacancies(sample_text)
    eligibility = parser.extract_eligibility(sample_text)
    salary = parser.extract_salary(sample_text)
    deadline = parser.extract_deadline(sample_text)
    url = parser.extract_application_url(sample_text)
    
    print(f"Job Title: {job_title}")
    print(f"Department: {department}")
    print(f"Vacancies: {vacancies}")
    print(f"Eligibility: {eligibility}")
    print(f"Salary: {salary}")
    print(f"Application Deadline: {deadline}")
    print(f"Application URL: {url}")
    
    # Test with another sample
    print("\n" + "=" * 50)
    print("Testing with another sample...")
    print("=" * 50)
    
    sample_text_2 = """
    STATE GOVERNMENT OF MAHARASHTRA
    PUBLIC WORKS DEPARTMENT
    
    VACANCY NOTICE
    
    Position: Assistant Engineer
    Total Posts: 12
    
    Minimum Qualification: B.E./B.Tech in Civil Engineering
    
    Salary: Rs. 45,000 - 65,000 per month
    
    Applications received till: 15/01/2025
    
    Website: www.maharashtra.gov.in/pwd
    """
    
    print("\nSample Text 2:")
    print("-" * 30)
    print(sample_text_2)
    print("-" * 30)
    
    job_title_2 = parser.extract_job_title(sample_text_2)
    department_2 = parser.extract_department(sample_text_2)
    vacancies_2 = parser.extract_vacancies(sample_text_2)
    eligibility_2 = parser.extract_eligibility(sample_text_2)
    salary_2 = parser.extract_salary(sample_text_2)
    deadline_2 = parser.extract_deadline(sample_text_2)
    url_2 = parser.extract_application_url(sample_text_2)
    
    print(f"\nJob Title: {job_title_2}")
    print(f"Department: {department_2}")
    print(f"Vacancies: {vacancies_2}")
    print(f"Eligibility: {eligibility_2}")
    print(f"Salary: {salary_2}")
    print(f"Application Deadline: {deadline_2}")
    print(f"Application URL: {url_2}")

if __name__ == "__main__":
    test_parser() 