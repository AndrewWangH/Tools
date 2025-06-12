import os
import csv
from datetime import datetime

def mortgage_calculator(loan_amount, annual_interest_rate, loan_years, payment_method="equal_installment"):
    """
    Calculate the monthly payment and total payment for a loan
    
    Parameters:
        loan_amount: Total loan amount (in currency units)
        annual_interest_rate: Annual interest rate (e.g., 0.05 for 5%)
        loan_years: Loan term in years
        payment_method: "equal_installment" for equal monthly payment (等额本息)
                        "equal_principal" for equal principal payment (等额本金)
        
    Returns:
        If payment_method is "equal_installment":
            monthly_payment: Fixed amount to be paid monthly
            total_payment: Total amount paid over the entire loan period
            monthly_details: List of tuples (month, payment, principal, interest, remaining_balance)
        
        If payment_method is "equal_principal":
            first_month_payment: Payment amount for the first month
            last_month_payment: Payment amount for the last month
            total_payment: Total amount paid over the entire loan period
            monthly_details: List of tuples (month, payment, principal, interest, remaining_balance)
    """
    # Convert annual interest rate to monthly
    monthly_interest_rate = annual_interest_rate / 12
    # Number of monthly payments
    total_months = loan_years * 12
    monthly_details = []
    
    if payment_method == "equal_installment":
        # 等额本息 (Equal monthly installment)
        if monthly_interest_rate == 0:
            monthly_payment = loan_amount / total_months
        else:
            # Formula for calculating monthly payment in an amortized loan
            monthly_payment = loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** total_months / ((1 + monthly_interest_rate) ** total_months - 1)
        
        # Calculate total payment over loan term
        total_payment = monthly_payment * total_months
        
        # Calculate monthly payment details
        remaining_balance = loan_amount
        for month in range(1, total_months + 1):
            interest_payment = remaining_balance * monthly_interest_rate
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment
            
            # Adjust for potential floating-point errors in the final payment
            if month == total_months:
                if abs(remaining_balance) < 0.01:  # Small tolerance
                    principal_payment += remaining_balance
                    remaining_balance = 0
            
            monthly_details.append((month, monthly_payment, principal_payment, interest_payment, remaining_balance))
        
        return monthly_payment, total_payment, monthly_details
    
    elif payment_method == "equal_principal":
        # 等额本金 (Equal principal payment)
        # Monthly principal payment (constant)
        monthly_principal = loan_amount / total_months
        
        # Calculate payment details for each month
        remaining_balance = loan_amount
        first_month_payment = None
        last_month_payment = None
        total_payment = 0
        
        for month in range(1, total_months + 1):
            interest_payment = remaining_balance * monthly_interest_rate
            monthly_payment = monthly_principal + interest_payment
            remaining_balance -= monthly_principal
            
            total_payment += monthly_payment
            
            if month == 1:
                first_month_payment = monthly_payment
            if month == total_months:
                last_month_payment = monthly_payment
            
            monthly_details.append((month, monthly_payment, monthly_principal, interest_payment, remaining_balance))
        
        return first_month_payment, last_month_payment, total_payment, monthly_details
    
    else:
        raise ValueError("Invalid payment method. Use 'equal_installment' or 'equal_principal'.")

def print_payment_schedule(monthly_details, num_months_to_show=5):
    """
    Print the payment schedule details
    
    Parameters:
        monthly_details: List of tuples (month, payment, principal, interest, remaining_balance)
        num_months_to_show: Number of months to show from beginning and end
    """
    print("\nMonthly Payment Schedule:")
    print("-" * 80)
    print(f"{'Month':<6} {'Payment':<12} {'Principal':<12} {'Interest':<12} {'Remaining Balance':<15}")
    print("-" * 80)
    
    total_months = len(monthly_details)
    
    # Show first few months
    for i in range(min(num_months_to_show, total_months)):
        month, payment, principal, interest, balance = monthly_details[i]
        print(f"{month:<6d} {payment:<12.2f} {principal:<12.2f} {interest:<12.2f} {balance:<15.2f}")
    
    # If there are more months than we want to show, print ellipsis
    if total_months > 2 * num_months_to_show:
        print("...")
    
    # Show last few months
    if num_months_to_show < total_months:
        for i in range(max(num_months_to_show, total_months - num_months_to_show), total_months):
            month, payment, principal, interest, balance = monthly_details[i]
            print(f"{month:<6d} {payment:<12.2f} {principal:<12.2f} {interest:<12.2f} {balance:<15.2f}")
    
    print("-" * 80)

def export_payment_schedule_to_csv(monthly_details, filepath, payment_method):
    """
    Export the payment schedule details to a CSV file
    
    Parameters:
        monthly_details: List of tuples (month, payment, principal, interest, remaining_balance)
        filepath: The path to save the CSV file
        payment_method: The payment method (equal_installment or equal_principal)
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write header
        csv_writer.writerow(['Month', 'Payment', 'Principal', 'Interest', 'Remaining Balance'])
        
        # Write data
        for month, payment, principal, interest, balance in monthly_details:
            csv_writer.writerow([month, f"{payment:.2f}", f"{principal:.2f}", 
                                f"{interest:.2f}", f"{balance:.2f}"])
    
    print(f"\nPayment schedule for {payment_method} exported to {filepath}")

# Usage example
if __name__ == "__main__":
    loan_amount = 1300000  # 1.3 million units
    annual_rate = 0.026    # 2.6%
    term_years = 20       # 15 years
    
    # Create timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define log directory
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
    
    print(f"Loan details: {loan_amount} units, {annual_rate*100}% annual rate, {term_years} years")
    
    # 等额本息方式 (Equal installment)
    monthly, total, monthly_details_equal_installment = mortgage_calculator(loan_amount, annual_rate, term_years, "equal_installment")
    print("\nEqual Installment Method (等额本息):")
    print(f"Monthly payment: {monthly:.2f}")
    print(f"Total payment: {total:.2f}")
    print(f"Interest paid: {total-loan_amount:.2f}")
    print_payment_schedule(monthly_details_equal_installment)
    
    # Export equal installment schedule to CSV
    equal_installment_csv = os.path.join(log_dir, f"equal_installment_{timestamp}.csv")
    # export_payment_schedule_to_csv(monthly_details_equal_installment, equal_installment_csv, "Equal Installment (等额本息)")
    
    # 等额本金方式 (Equal principal)
    first_payment, last_payment, total, monthly_details_equal_principal = mortgage_calculator(loan_amount, annual_rate, term_years, "equal_principal")
    print("\nEqual Principal Method (等额本金):")
    print(f"First month payment: {first_payment:.2f}")
    print(f"Last month payment: {last_payment:.2f}")
    print(f"Total payment: {total:.2f}")
    print(f"Interest paid: {total-loan_amount:.2f}")
    print_payment_schedule(monthly_details_equal_principal)
    
    # Export equal principal schedule to CSV
    equal_principal_csv = os.path.join(log_dir, f"equal_principal_{timestamp}.csv")
    #export_payment_schedule_to_csv(monthly_details_equal_principal, equal_principal_csv, "Equal Principal (等额本金)")
    
    # 打印完整的还款计划
    # print("\n完整的等额本息还款计划:")
    # print_payment_schedule(monthly_details_equal_installment, term_years * 12)
    
    print("\n完整的等额本金还款计划:")
    print_payment_schedule(monthly_details_equal_principal, term_years * 12)