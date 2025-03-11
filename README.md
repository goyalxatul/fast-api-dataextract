# 🚀 FastAPI Data Extraction

A FastAPI-based API to extract and analyze text from medical records.

## 🔧 Setup & Run

### 1️⃣ Clone & Navigate
```sh
git clone https://github.com/goyalxatul/fast-api-dataextract.git
cd fast-api-dataextract
```

### 2️⃣ Create & Activate Virtual Environment  
#### **Windows:**
```sh
python -m venv .venv
.venv\Scripts\activate
```
#### **Mac/Linux:**
```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install Dependencies  
```sh
pip install --upgrade pip  
pip install -r requirements.txt
```

### 4️⃣ Download Spacy Model  
```sh
python -m spacy download en_core_web_md
```

### 5️⃣ Run the Server  
```sh
uvicorn main:app --reload
```
📌 **API Base URL:** `http://127.0.0.1:8000`  
📌 **Swagger Docs:** `http://127.0.0.1:8000/docs`  
📌 **ReDoc Docs:** `http://127.0.0.1:8000/redoc`  

## 📁 Project Structure  
```
fast-api-dataextract/
│── main.py           # FastAPI app
│── requirements.txt  # Dependencies
│── README.md         # Documentation
│── .venv/            # Virtual environment (not committed)
│── data/             # Folder for input files (if needed)
```

## 🔥 API Endpoints  
| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/extract/` | Uploads a medical record and extracts metadata |

### **Example Request (via `cURL`)**
```sh
curl -X 'POST' 'http://127.0.0.1:8000/extract/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample.pdf'
```

### **Example Response**
```json
{
  "timestamp": "2025-03-11T10:00:00",
  "document_type": "Medical Record",
  "extracted_data": {
    "Name": "John Doe",
    "Age": "45 years old",
    "Gender": "Male",
    "Illness": "Diabetes, Hypertension",
    "Doctor Name": "Dr. Smith",
    "Prescription": "Metformin 500mg, Lisinopril 10mg"
  }
}
```

## 📜 License  
MIT License. Contributions welcome! 🚀  
