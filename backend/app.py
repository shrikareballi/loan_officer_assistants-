from flask import Flask, request, jsonify
from flask_cors import CORS

from calculations import (
    calculate_dti,
    calculate_ltv,
    calculate_emi
)

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({
        "message": "Loan Officer Assistant API is running"
    })


@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json

    income = float(data["monthly_income"])
    debt = float(data["monthly_debt"])
    loan = float(data["loan_amount"])
    property_value = float(data["property_value"])
    interest = float(data["interest_rate"])
    tenure = int(data["tenure"])

    dti = calculate_dti(debt, income)
    ltv = calculate_ltv(loan, property_value)
    emi = calculate_emi(loan, interest, tenure)

    return jsonify({
        "dti": round(dti, 2),
        "ltv": round(ltv, 2),
        "emi": round(emi, 2)
    })


if __name__ == "__main__":
    app.run(debug=True)