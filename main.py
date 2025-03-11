import os
import spacy
import re
import textract
from fastapi import FastAPI, UploadFile, File
from datetime import datetime
import uvicorn

# Load NLP Model
nlp = spacy.load("en_core_web_md")

app = FastAPI()

def clean_text(file_path):
    """
    Extracts and cleans text from medical records (PDF/DOCX).
    """
    try:
        text = textract.process(file_path, method="tesseract", language="eng")
        text = text.decode("utf-8", errors="ignore")

        # Clean text
        text = text.replace("\r\n", " ").replace("\n", " ")
        text = re.sub(r"[^a-zA-Z0-9.,:;()\-\/\s]", "", text)
        text = re.sub(" +", " ", text)

        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def identify_document_type(text):
    """
    Determines whether the document is a Medical Record or an X-Ray Report.
    """
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
    """
    Extracts patient details like Name, Age, Gender, Illness, Doctor Name, and Prescription.
    """
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
            break  # Assuming first person entity is patient name

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
        # Extracting only key terms (first few words)
            illness_text = match.group(1).strip()
            patient_info["Illness"] = ", ".join(illness_text.split()[:3])  # Limits to first 3 words
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
    """
    API endpoint to upload a medical record file and extract metadata.
    """
    # Save file temporarily
    file_location = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Extract text from the file
    text = clean_text(file_location)

    if "Error extracting text" in text:
        return {"error": text}

    # Identify document type
    doc_type = identify_document_type(text)

    # Extract medical information if it's a medical record
    extracted_data = {}
    if doc_type == "Medical Record":
        extracted_data = extract_medical_info(text)

    # Delete the temporary file
    os.remove(file_location)

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





