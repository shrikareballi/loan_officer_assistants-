def validate_inputs(data):
    if data['income'] <= 0 or data['loan_amount'] <= 0:
        raise ValueError("Income and loan amount must be positive.")
    if data['tenure'] <= 0:
        raise ValueError("Tenure must be greater than zero.")
    return True
