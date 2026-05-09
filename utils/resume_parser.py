import pdfplumber
import re

# Common skills for keyword matching
TECH_SKILLS = [
    'python', 'java', 'c++', 'javascript', 'html', 'css', 'react', 'node.js',
    'sql', 'mongodb', 'machine learning', 'data science', 'aws', 'docker',
    'kubernetes', 'git', 'flask', 'django', 'pandas', 'numpy', 'scikit-learn',
    'tensorflow', 'pytorch', 'tableau', 'power bi', 'excel', 'analytical',
    'rest api', 'graphql', 'spring boot', 'express', 'vue.js', 'angular',
    'typescript', 'go', 'rust', 'c#', 'php', 'swift', 'kotlin'
]

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file object."""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def analyze_resume(text, job_description=None):
    """Analyzes resume text for skills and calculates an ATS score using NLP."""
    try:
        # Load spaCy model
        import spacy
        from spacy.matcher import PhraseMatcher
        nlp = spacy.load("en_core_web_sm")
    except ImportError:
        # Fallback if spacy not installed
        nlp = None
    except Exception:
        # Fallback if model not downloaded
        nlp = None

    text_lower = text.lower()
    found_skills = []

    if nlp:
        doc = nlp(text_lower)
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(skill) for skill in TECH_SKILLS]
        matcher.add("Skills", patterns)
        
        matches = matcher(doc)
        found_skills = list(set([doc[start:end].text for match_id, start, end in matches]))
    else:
        # Fallback to regex
        for skill in TECH_SKILLS:
            if re.search(rf'\b{re.escape(skill)}\b', text_lower):
                found_skills.append(skill)

    # Job Description Matching Logic
    jd_score = 0
    jd_match_details = ""
    if job_description:
        jd_lower = job_description.lower()
        required_skills = []
        for skill in TECH_SKILLS:
            if skill in jd_lower:
                required_skills.append(skill)
        
        if required_skills:
            matched_required = [s for s in required_skills if s in found_skills]
            jd_score = (len(matched_required) / len(required_skills)) * 100
            jd_match_details = f"Matched {len(matched_required)} out of {len(required_skills)} skills required for this job."

    missing_skills = [skill for skill in TECH_SKILLS if skill not in found_skills]

    # Basic ATS Score calculation
    # Base score from skills
    skill_score = (len(found_skills) / 15) * 60 # Targeting 15 key skills for 60%
    
    # Structure score
    structure_score = 0
    sections = ["education", "experience", "projects", "skills", "certifications", "achievements", "contact"]
    for section in sections:
        if section in text_lower:
            structure_score += 5
    
    # Length score
    length_score = 5 if 200 < len(text.split()) < 1000 else 0
    
    total_score = min(100, int(skill_score + structure_score + length_score))

    return {
        "score": total_score,
        "jd_score": int(jd_score) if job_description else None,
        "jd_details": jd_match_details,
        "found_skills": sorted(found_skills),
        "missing_skills": missing_skills[:10],
        "word_count": len(text.split())
    }
