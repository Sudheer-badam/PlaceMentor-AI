# PlaceMentor AI - Project Documentation 📚
**Developer: BADAM SUDHEER REDDY**
**ID: 2300033278 | KL UNIVERSITY**

## 1. Project Abstract
**PlaceMentor AI** is an intelligent career guidance platform designed to assist college students in their placement journey. By leveraging Machine Learning (Random Forest) and Data Analytics, the system provides personalized insights into placement probability, resume strength, and skill gaps. It features a comprehensive suite of tools including an ATS-based resume analyzer, an aptitude testing module, and a coding progress tracker, all accessible through a modern, responsive Streamlit-based web interface.

## 2. System Architecture
- **Frontend**: Streamlit (Python-based reactive web framework)
- **Backend Logic**: Python with Scikit-Learn for AI and Pandas for data processing.
- **Database**: SQLite3 for persistent storage of user profiles, quiz scores, and analysis history.
- **AI Engine**: Random Forest Classifier trained on academic and technical performance metrics.
- **Resume Engine**: NLP-based keyword matching for ATS scoring.

## 3. Mini Project Documentation
### Objectives:
- To automate the placement prediction process using student performance data.
- To provide a centralized platform for placement preparation (Aptitude + Coding).
- To assist students in optimizing their resumes for modern ATS (Applicant Tracking Systems).

### Modules:
1. **User Authentication**: Secure login/signup using SHA-256 hashing.
2. **AI Predictor**: Takes input like CGPA, Aptitude, and Skills to calculate placement odds.
3. **Resume Analyzer**: Scans PDF resumes for industry-standard keywords and calculates a compatibility score.
4. **Quiz System**: Interactive module to practice and log aptitude scores.
5. **Analytics Dashboard**: Visualizes student progress using Plotly and Matplotlib.

## 4. Viva Questions & Answers
**Q1: Why did you choose Random Forest for the prediction model?**
*A: Random Forest is an ensemble learning method that is highly robust to overfitting and handles both numerical and categorical data well, making it ideal for student performance datasets.*

**Q2: How does the Resume Analyzer calculate the ATS score?**
*A: It uses a keyword-matching algorithm that compares the extracted text from the PDF against a curated list of technical and soft skills. It also considers structural elements like the presence of "Education" and "Experience" sections.*

**Q3: What is the role of SQLite in this project?**
*A: SQLite is a lightweight, serverless database used to store user credentials, quiz history, and skill levels locally, ensuring data persistence without the need for a complex database server.*

**Q4: How do you handle password security?**
*A: Passwords are never stored in plain text. We use the SHA-256 hashing algorithm to convert passwords into unique hex strings before storing them in the database.*

## 5. Interview Explanation (Elevator Pitch)
"PlaceMentor AI is a full-stack career platform I developed to solve the lack of personalized guidance in college placements. I built it using Python and Streamlit, integrating a Random Forest model to predict placement probability with high accuracy. One of the key challenges I solved was building a custom Resume Parser that calculates ATS compatibility scores. The project follows a modular architecture, separating data logic, ML training, and UI components, making it highly scalable and easy to maintain."

## 6. Future Enhancements
- **AI Mock Interviews**: Integrating Speech-to-Text and NLP for real-time interview practice.
- **Job Recommendations**: Using Collaborative Filtering to suggest jobs based on skill profiles.
- **LinkedIn Integration**: Scrape professional details directly from LinkedIn.
- **Certificate Generator**: Auto-generate completion certificates for high quiz scores.
