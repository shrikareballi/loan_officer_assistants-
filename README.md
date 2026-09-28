# Loan Office Assistant

A simple loan analysis tool built with **Flask (backend)** and **Streamlit (frontend)**.  
It calculates Debt-to-Income Ratio (DTI), Loan-to-Value Ratio (LTV), and Equated Monthly Installment (EMI).

---

## 🚀 Features
- Input loan details (income, debt, loan amount, property value, interest rate, tenure).
- Backend (Flask) performs calculations.
- Frontend (Streamlit) displays results in a clean UI.
- Metrics: DTI, LTV, EMI.

---

## 📂 Project Structure
loan_office_assistants-/
├── backend/
│   ├── app.py              # Flask server
│   ├── calculations.py     # Loan calculation logic
│   └── requirements.txt    # Backend dependencies
├── frontend/
│   └── frontend.py         # Streamlit UI
├── venv/                   # Virtual environment
├── README.md               # Project documentation

---

## ⚙️ Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd loan_office_assistants-
2.Create and activate a virtual environment:
   python -m venv venv
   venv\Scripts\activate   # On Windows
3.Install dependencies:
  pip install -r backend/requirements.txt
▶️ Running the App
1.Start the backend (Flask):
  cd backend
  python app.py
2.Start the frontend (Streamlit):
  cd ..
  streamlit run frontend/frontend.py
3.Open your browser:

Backend runs at: http://127.0.0.1:5000

Frontend runs at: http://localhost:8501

