import os
import re
import fitz  # PyMuPDF for PDF text extraction
import spacy
from docx import Document
from fastapi import FastAPI, UploadFile, File
from datetime import datetime
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Load NLP model
nlp = spacy.load("en_core_web_md")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, restrict to specific ones in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file without using OCR."""
    try:
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text("text") for page in doc])
        return clean_text(text) if text.strip() else "Error: Empty PDF or scanned PDF."
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return clean_text(text)
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

def clean_text(text):
    """Cleans extracted text by removing unwanted characters."""
    text = text.replace("\r\n", " ").replace("\n", " ")
    text = re.sub(r"[^a-zA-Z0-9.,:;()\-\/\s]", "", text)
    text = re.sub(" +", " ", text)
    return text.strip()

def identify_document_type(text):
    """Determines if the document is a Medical Record or an X-Ray Report."""
    text = text.lower()
    
    medical_keywords = ["prescription", "diagnosis", "patient", "medical history", "treatment", "doctor", "hospital", "disease", "medications"]
    xray_keywords = ["x-ray", "radiology", "chest x-ray", "mri", "ct scan", "ultrasound", "scan report", "radiologist"]

    if any(keyword in text for keyword in medical_keywords):
        return "Medical Record"
    elif any(keyword in text for keyword in xray_keywords):
        return "X-Ray Report"
    else:
        return "Unknown Document Type"

def extract_medical_info(text):
    """Extracts patient details like Name, Age, Gender, Illness, Doctor Name, and Prescription."""
    doc = nlp(text)

    patient_info = {
        "Name": "Not Found",
        "Age": "Not Found",
        "Gender": "Not Found",
        "Illness": "Not Found",
        "Doctor Name": "Not Found",
        "Prescription": "Not Found"
    }

    # Extract Name
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            patient_info["Name"] = ent.text
            break

    # Extract Age
    age_match = re.search(r"(\b\d{1,2}\s?(years|yrs|y/o|years old)\b)", text, re.IGNORECASE)
    if age_match:
        patient_info["Age"] = age_match.group()

    # Extract Gender
    if "male" in text.lower():
        patient_info["Gender"] = "Male"
    elif "female" in text.lower():
        patient_info["Gender"] = "Female"

    # Extract Illness / Diagnosis
    illness_keywords = ["diagnosis", "condition", "disease", "illness", "symptoms"]
    for keyword in illness_keywords:
        match = re.search(rf"{keyword}\s*:\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
        if match:
            illness_text = match.group(1).strip()
            patient_info["Illness"] = ", ".join(illness_text.split()[:3])
            break

    # Extract Doctor Name
    doctor_match = re.search(r"(Dr\.?\s?[A-Za-z]+\s?[A-Za-z]*)", text)
    if doctor_match:
        patient_info["Doctor Name"] = doctor_match.group()

    # Extract Prescription
    prescription_match = re.search(r"prescription\s*:\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
    if prescription_match:
        patient_info["Prescription"] = prescription_match.group(1).strip()

    return patient_info

@app.post("/extract/")
async def extract_metadata(file: UploadFile = File(...)):
    """API endpoint to extract text and metadata from uploaded files."""
    file_location = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Extract text based on file type
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_location)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_location)
    else:
        os.remove(file_location)
        return {"error": "Unsupported file format"}

    os.remove(file_location)  # Clean up after processing

    if "Error" in text:
        return {"error": text}

    doc_type = identify_document_type(text)
    
    # Extract medical information if it's a medical record
    extracted_data = extract_medical_info(text) if doc_type == "Medical Record" else {}

    return {
        "timestamp": datetime.utcnow(),
        "document_type": doc_type,
        "extracted_data": extracted_data
    }

@app.get("/")
async def root():
    return {"message": "Welcome to MediTrust Extraction API!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)





