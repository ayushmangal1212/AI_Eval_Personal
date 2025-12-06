"""
Enhanced Resume Parser
Extracts comprehensive information from resumes
"""

import re
import io
from datetime import datetime

try:
    import PyPDF2
except:
    PyPDF2 = None

try:
    import docx
except:
    docx = None

# Skill keywords database
SKILL_KEYWORDS = {
    'Python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'],
    'Java': ['java', 'spring', 'spring boot', 'hibernate', 'maven', 'gradle', 'junit'],
    'JavaScript': ['javascript', 'js', 'node', 'nodejs', 'react', 'angular', 'vue', 'typescript', 'express'],
    'Database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'database', 'nosql'],
    'DevOps': ['docker', 'kubernetes', 'k8s', 'jenkins', 'ci/cd', 'aws', 'azure', 'gcp', 'terraform', 'ansible'],
    'Frontend': ['html', 'css', 'sass', 'less', 'webpack', 'responsive', 'ui/ux', 'bootstrap', 'tailwind'],
    'Backend': ['api', 'rest', 'graphql', 'microservices', 'server', 'backend'],
    'Data Science': ['machine learning', 'ml', 'ai', 'data science', 'analytics', 'big data', 'spark', 'hadoop'],
    'Mobile': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin', 'mobile'],
    'Testing': ['testing', 'junit', 'pytest', 'selenium', 'test automation', 'qa'],
    'Tools': ['git', 'github', 'gitlab', 'jira', 'agile', 'scrum', 'linux', 'bash']
}

# Role keywords
ROLE_KEYWORDS = {
    'Java Developer': ['java developer', 'java engineer', 'backend java', 'spring developer'],
    'Python Developer': ['python developer', 'python engineer', 'django developer', 'flask developer'],
    'Frontend Developer': ['frontend developer', 'front-end', 'ui developer', 'react developer', 'angular developer'],
    'DevOps Engineer': ['devops', 'site reliability', 'sre', 'infrastructure engineer'],
    'Data Engineer': ['data engineer', 'etl developer', 'big data engineer'],
    'Database Administrator': ['dba', 'database administrator', 'database engineer']
}

class EnhancedResumeParser:
    """Enhanced resume parser with comprehensive extraction"""
    
    def __init__(self):
        self.text = ""
        self.extracted_data = {}
    
    def parse_file(self, file_bytes, filename):
        """
        Parse resume from file bytes
        
        Args:
            file_bytes: Resume file content as bytes
            filename: Name of the file
            
        Returns:
            dict: Extracted resume data
        """
        # Extract text from file
        self.text = self._extract_text(file_bytes, filename)
        
        # Extract various fields
        self.extracted_data = {
            'name': self._extract_name(),
            'email': self._extract_email(),
            'phone': self._extract_phone(),
            'skills': self._extract_skills(),
            'experience_years': self._extract_experience(),
            'education': self._extract_education(),
            'suggested_role': self._suggest_role(),
            'certifications': self._extract_certifications(),
            'languages': self._extract_languages(),
            'summary': self._extract_summary(),
            'raw_text': self.text[:500]  # First 500 chars for preview
        }
        
        return self.extracted_data
    
    def _extract_text(self, file_bytes, filename):
        """Extract text from PDF, DOCX, or TXT file"""
        text = ""
        fname = (filename or "").lower()
        
        try:
            if fname.endswith('.pdf') and PyPDF2:
                try:
                    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                    pages = []
                    for p in reader.pages:
                        try:
                            pages.append(p.extract_text() or "")
                        except:
                            continue
                    text = "\n".join(pages)
                except:
                    text = file_bytes.decode('utf-8', errors='ignore')
            elif fname.endswith('.docx') and docx:
                try:
                    doc = docx.Document(io.BytesIO(file_bytes))
                    text = "\n".join([p.text for p in doc.paragraphs])
                except:
                    text = file_bytes.decode('utf-8', errors='ignore')
            else:
                text = file_bytes.decode('utf-8', errors='ignore')
        except:
            text = file_bytes.decode('utf-8', errors='ignore')
        
        return text
    
    def _extract_name(self):
        """Extract candidate name from resume"""
        lines = [ln.strip() for ln in self.text.splitlines() if ln.strip()]
        
        # Look for "Name:" pattern
        for ln in lines[:10]:
            if re.search(r"^name[:\-\s]", ln, re.I):
                name = re.sub(r"^name[:\-\s]*", "", ln, flags=re.I).strip()
                if name:
                    return name
        
        # First line that looks like a name (2-4 words, letters only)
        for ln in lines[:5]:
            parts = ln.split()
            if 1 < len(parts) <= 4 and all(re.match(r"^[A-Za-z\-']+$", p) for p in parts):
                return ln.strip()
        
        return "Unknown"
    
    def _extract_email(self):
        """Extract email address"""
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", self.text)
        return email_match.group(0) if email_match else ""
    
    def _extract_phone(self):
        """Extract phone number"""
        # Match various phone formats
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{10}',
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, self.text)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_skills(self):
        """Extract technical skills using keyword matching"""
        text_lower = self.text.lower()
        found_skills = []
        
        for category, keywords in SKILL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Capitalize properly
                    if keyword == keyword.lower():
                        found_skills.append(keyword.title())
                    else:
                        found_skills.append(keyword)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def _extract_experience(self):
        """Extract years of experience"""
        # Look for patterns like "5 years", "5+ years", "5-7 years"
        exp_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\s*-\s*\d+\s*(?:years?|yrs?)',
            r'experience[:\s]+(\d+)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, self.text, re.I)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_education(self):
        """Extract education information"""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'(B\.?Tech|Bachelor|B\.?E\.?|B\.?S\.?|M\.?Tech|Master|M\.?S\.?|M\.?B\.?A|PhD|Ph\.?D)',
            r'(Computer Science|Information Technology|Engineering|Mathematics|Statistics)'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, self.text, re.I)
            education.extend(matches)
        
        return list(set(education))
    
    def _suggest_role(self):
        """Suggest best matching role based on resume content"""
        text_lower = self.text.lower()
        role_scores = {}
        
        for role, keywords in ROLE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            role_scores[role] = score
        
        # Also check skill-based matching
        skills = self._extract_skills()
        if 'Java' in str(skills) or 'Spring' in str(skills):
            role_scores['Java Developer'] = role_scores.get('Java Developer', 0) + 3
        if 'Python' in str(skills) or 'Django' in str(skills) or 'Flask' in str(skills):
            role_scores['Python Developer'] = role_scores.get('Python Developer', 0) + 3
        if 'React' in str(skills) or 'Angular' in str(skills) or 'Vue' in str(skills):
            role_scores['Frontend Developer'] = role_scores.get('Frontend Developer', 0) + 3
        if 'Docker' in str(skills) or 'Kubernetes' in str(skills):
            role_scores['DevOps Engineer'] = role_scores.get('DevOps Engineer', 0) + 3
        
        # Return role with highest score
        if role_scores:
            return max(role_scores, key=role_scores.get)
        
        return "Python Developer"  # Default
    
    def _extract_certifications(self):
        """Extract certifications"""
        cert_keywords = ['certified', 'certification', 'certificate', 'aws', 'azure', 'gcp', 'oracle', 'cisco']
        certifications = []
        
        lines = self.text.splitlines()
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in cert_keywords):
                certifications.append(line.strip())
        
        return certifications[:5]  # Limit to 5
    
    def _extract_languages(self):
        """Extract programming/spoken languages"""
        lang_patterns = [
            r'languages?[:\s]+([\w\s,]+)',
            r'programming languages?[:\s]+([\w\s,]+)'
        ]
        
        for pattern in lang_patterns:
            match = re.search(pattern, self.text, re.I)
            if match:
                langs = match.group(1).split(',')
                return [lang.strip() for lang in langs[:5]]
        
        return []
    
    def _extract_summary(self):
        """Extract professional summary"""
        summary_keywords = ['summary', 'objective', 'profile', 'about']
        lines = self.text.splitlines()
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Get next 3-5 lines as summary
                summary_lines = lines[i+1:i+6]
                summary = ' '.join([l.strip() for l in summary_lines if l.strip()])
                if len(summary) > 50:
                    return summary[:300] + "..." if len(summary) > 300 else summary
        
        # If no summary section, return first paragraph
        paragraphs = [p.strip() for p in self.text.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            return paragraphs[0][:300] + "..." if len(paragraphs[0]) > 300 else paragraphs[0]
        
        return ""

# Global parser instance
resume_parser = EnhancedResumeParser()
