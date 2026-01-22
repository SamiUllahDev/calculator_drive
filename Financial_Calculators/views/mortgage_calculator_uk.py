from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from datetime import datetime

try:
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


def add_months(source_date, months):
    """
    Add months to a date (fallback implementation if python-dateutil is missing).
    """
    if HAS_DATEUTIL:
        return source_date + relativedelta(months=months)
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(
        source_date.day,
        [
            31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][month - 1],
    )
    return datetime(year, month, day)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MortgageCalculatorUk(View):
    """
    UK Mortgage Calculator.

    Features (kept slightly simpler than the main mortgage calculator):
    - Supports repayment and interest-only mortgages
    - Monthly payment calculation
    - Total interest and total paid
    - Amortization schedule (for repayment mortgages)
    """

    template_name = "financial_calculators/mortgage_calculator_uk.html"

    # Validation limits (GBP ranges but only numeric validation is enforced)
    MIN_PROPERTY_PRICE = 10000
    MAX_PROPERTY_PRICE = 100000000
    MIN_DEPOSIT = 0
    MIN_INTEREST_RATE = 0.01
    MAX_INTEREST_RATE = 25
    MIN_TERM_YEARS = 1
    MAX_TERM_YEARS = 40

    def get(self, request):
        """
        Render the calculator UI.
        """
        context = {
            "calculator_name": "UK Mortgage Calculator",
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Handle POST request for calculations.

        Expected fields (JSON body or form POST):
        - property_price
        - deposit
        - interest_rate (annual, %)
        - term_years
        - mortgage_type: "repayment" (default) or "interest_only"
        """
        try:
            data = (
                json.loads(request.body)
                if request.content_type == "application/json"
                else request.POST
            )

            # Parse inputs
            property_price = self._get_float(data, "property_price", 0)
            deposit = self._get_float(data, "deposit", 0)
            interest_rate = self._get_float(data, "interest_rate", 0)
            term_years = self._get_int(data, "term_years", 0)
            mortgage_type = data.get("mortgage_type", "repayment") or "repayment"

            errors = []

            # Basic validation
            if property_price < self.MIN_PROPERTY_PRICE:
                errors.append(
                    f"Property price must be at least £{self.MIN_PROPERTY_PRICE:,}."
                )
            elif property_price > self.MAX_PROPERTY_PRICE:
                errors.append(
                    f"Property price cannot exceed £{self.MAX_PROPERTY_PRICE:,}."
                )

            if deposit < self.MIN_DEPOSIT:
                errors.append("Deposit cannot be negative.")
            if deposit >= property_price and property_price > 0:
                errors.append("Deposit must be less than the property price.")

            if interest_rate < self.MIN_INTEREST_RATE:
                errors.append(
                    f"Interest rate must be at least {self.MIN_INTEREST_RATE}%."
                )
            elif interest_rate > self.MAX_INTEREST_RATE:
                errors.append(
                    f"Interest rate cannot exceed {self.MAX_INTEREST_RATE}%."
                )

            if term_years < self.MIN_TERM_YEARS or term_years > self.MAX_TERM_YEARS:
                errors.append(
                    f"Term must be between {self.MIN_TERM_YEARS} and {self.MAX_TERM_YEARS} years."
                )

            if mortgage_type not in ("repayment", "interest_only"):
                errors.append("Invalid mortgage type.")

            if errors:
                return JsonResponse({"success": False, "error": errors[0]}, status=400)

            # Core calculations
            loan_amount = max(property_price - deposit, 0)
            total_months = term_years * 12
            monthly_rate = (interest_rate / 100) / 12

            if loan_amount <= 0:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Loan amount must be greater than zero.",
                    },
                    status=400,
                )

            # Repayment mortgage: standard amortizing loan
            if mortgage_type == "repayment":
                if monthly_rate > 0:
                    rate_factor = np.power(1 + monthly_rate, total_months)
                    monthly_payment = loan_amount * (monthly_rate * rate_factor) / (
                        rate_factor - 1
                    )
                else:
                    monthly_payment = loan_amount / total_months

                # Generate amortization schedule
                schedule_data = self._generate_schedule(
                    loan_amount, monthly_rate, monthly_payment, total_months
                )
                schedule = schedule_data["schedule"]
                yearly_summary = schedule_data["yearly_summary"]

                total_interest = sum(p["interest"] for p in schedule)
                total_paid = loan_amount + total_interest
                last_payment = schedule[-1] if schedule else None
                payoff_date = last_payment["date"] if last_payment else "N/A"

            # Interest-only mortgage
            else:
                monthly_payment = loan_amount * monthly_rate
                total_interest = monthly_payment * total_months
                total_paid = loan_amount + total_interest

                # Interest-only: schedule only tracks interest payments,
                # principal repaid in a lump sum at the end.
                schedule = []
                yearly_summary = []
                balance = loan_amount
                start_date = datetime.now()
                year_interest = 0
                current_year = start_date.year

                for month_num in range(1, total_months + 1):
                    current_date = add_months(start_date, month_num - 1)
                    interest = balance * monthly_rate
                    principal = 0

                    schedule.append(
                        {
                            "month": month_num,
                            "date": current_date.strftime("%b %Y"),
                            "payment": round(monthly_payment, 2),
                            "principal": round(principal, 2),
                            "interest": round(interest, 2),
                            "balance": round(balance, 2),
                        }
                    )

                    year_interest += interest

                    if current_date.month == 12 or month_num == total_months:
                        yearly_summary.append(
                            {
                                "year": current_year,
                                "principal": 0.0,
                                "interest": round(year_interest, 2),
                                "start_balance": round(balance, 2),
                                "end_balance": round(balance, 2),
                            }
                        )
                        current_year += 1
                        year_interest = 0

                payoff_date = add_months(start_date, total_months - 1).strftime(
                    "%b %Y"
                )

            ltv_ratio = (loan_amount / property_price * 100) if property_price else 0

            response_data = {
                "success": True,
                "inputs": {
                    "property_price": round(property_price, 2),
                    "deposit": round(deposit, 2),
                    "loan_amount": round(loan_amount, 2),
                    "interest_rate": round(interest_rate, 3),
                    "term_years": term_years,
                    "mortgage_type": mortgage_type,
                    "ltv_ratio": round(ltv_ratio, 2),
                },
                "payment": {
                    "monthly": round(monthly_payment, 2),
                    "total_interest": round(total_interest, 2),
                    "total_paid": round(total_paid, 2),
                    "payoff_date": payoff_date,
                },
                "schedule": schedule[:120],  # limit to first 10 years for performance
                "yearly_summary": yearly_summary,
            }

            return JsonResponse(response_data)

        except Exception:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Calculation error. Please check your inputs and try again.",
                },
                status=400,
            )

    def _get_float(self, data, key, default=0):
        """
        Safely parse a float from the incoming data.
        """
        try:
            value = data.get(key, default)
            if value is None or value == "" or value == "null":
                return default
            return float(str(value).replace(",", "").replace("£", "").replace("$", ""))
        except (ValueError, TypeError):
            return default

    def _get_int(self, data, key, default=0):
        """
        Safely parse an int from the incoming data.
        """
        try:
            value = data.get(key, default)
            if value is None or value == "" or value == "null":
                return default
            return int(float(str(value).replace(",", "")))
        except (ValueError, TypeError):
            return default

    def _generate_schedule(self, loan_amount, monthly_rate, monthly_payment, total_months):
        """
        Generate a standard repayment mortgage amortization schedule.
        """
        schedule = []
        yearly_summary = []

        balance = loan_amount
        start_date = datetime.now()

        year_interest = 0
        year_principal = 0
        current_year = start_date.year
        year_start_balance = balance

        month_num = 0

        while balance > 0.01 and month_num < total_months + 240:
            month_num += 1
            current_date = add_months(start_date, month_num - 1)

            interest = balance * monthly_rate
            principal = monthly_payment - interest

            if principal > balance:
                principal = balance
                monthly_payment_effective = principal + interest
            else:
                monthly_payment_effective = monthly_payment

            balance = max(0, balance - principal)

            schedule.append(
                {
                    "month": month_num,
                    "date": current_date.strftime("%b %Y"),
                    "payment": round(monthly_payment_effective, 2),
                    "principal": round(principal, 2),
                    "interest": round(interest, 2),
                    "balance": round(balance, 2),
                }
            )

            year_interest += interest
            year_principal += principal

            if current_date.month == 12 or balance <= 0.01:
                yearly_summary.append(
                    {
                        "year": current_year,
                        "principal": round(year_principal, 2),
                        "interest": round(year_interest, 2),
                        "start_balance": round(year_start_balance, 2),
                        "end_balance": round(balance, 2),
                    }
                )
                current_year += 1
                year_interest = 0
                year_principal = 0
                year_start_balance = balance

            if balance <= 0.01:
                break

        return {
            "schedule": schedule,
            "yearly_summary": yearly_summary,
        }
