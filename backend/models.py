from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    income = db.Column(db.Float, nullable=False)
    debt = db.Column(db.Float, nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    property_value = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    tenure = db.Column(db.Integer, nullable=False)
