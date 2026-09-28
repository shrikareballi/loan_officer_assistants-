from flask import Flask, request, jsonify
from backend.models import db, LoanApplication
from backend.calculations import calculate_dti, calculate_ltv, calculate_emi
from backend.utils import validate_inputs

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loans.db'
db.init_app(app)

@app.route('/apply', methods=['POST'])
def apply_loan():
    data = request.json
    try:
        validate_inputs(data)
        loan = LoanApplication(**data)
        db.session.add(loan)
        db.session.commit()
        return jsonify({"message": "Loan application saved!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
