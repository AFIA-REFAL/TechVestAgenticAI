"""
BVRIT Hyderabad College FAQ Chatbot — Computation Tools

Three tools that augment the RAG pipeline for queries the grounding
document alone cannot answer:

1. fee_calculator  — multi-year fee totals with hostel & scholarship
2. date_checker    — compare KB dates against today's real-time clock
3. percentage_calculator — placement rates, cutoff conversions, etc.

Each tool is defined as a plain Python function decorated for use with
LangChain's @tool decorator (or OpenAI function-calling format).

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================
# Pydantic schemas (used for LLM tool binding)
# ============================================================


class FeeCalculatorInput(BaseModel):
    """Input schema for fee_calculator tool."""
    annual_tuition_fee: float = Field(
        description="Annual tuition fee in INR for the specific BVRIT program "
                    "(e.g., CSE, ECE, EEE, CSE-AIML). Extracted from the fee "
                    "details section of the knowledge base."
    )
    annual_hostel_fee: float = Field(
        default=0.0,
        description="Annual hostel accommodation fee in INR for BVRIT Hyderabad "
                    "hostel. Set to 0 if the student is not asking about hostel."
    )
    number_of_years: int = Field(
        description="Duration of the program in years (4 for B.Tech, 2 for M.Tech at BVRIT)."
    )
    scholarship_percentage: float = Field(
        default=0.0,
        description="Scholarship or concession percentage (0–100) applicable to "
                    "the student. For example, 25 means 25% off the total tuition fee. "
                    "Set to 0 if no scholarship."
    )


class DateCheckerInput(BaseModel):
    """Input schema for date_checker tool."""
    target_date: str = Field(
        description="The date to compare, in ISO 8601 format (YYYY-MM-DD). "
                    "This is a BVRIT-specific date extracted from the knowledge "
                    "base, such as an admission deadline, exam date, or event date."
    )
    date_label: str = Field(
        description="A human-readable label for what this date represents, "
                    "e.g., 'EAMCET application deadline', 'BVRIT admission form "
                    "release', 'campus fest date'."
    )


class PercentageCalculatorInput(BaseModel):
    """Input schema for percentage_calculator tool."""
    numerator: float = Field(
        description="The part value — e.g., number of students placed, scholarship "
                    "discount amount, or marks obtained. Must be a non-negative "
                    "number extracted from the BVRIT knowledge base."
    )
    denominator: float = Field(
        description="The total or whole value — e.g., total number of students, "
                    "total fee amount, or maximum marks. Must be a positive number "
                    "extracted from the BVRIT knowledge base."
    )
    calculation_context: str = Field(
        description="A brief description of what this percentage represents in "
                    "the BVRIT context, e.g., 'placement rate for 2024 batch', "
                    "'scholarship discount on CSE tuition', 'EAMCET cutoff conversion'."
    )


# ============================================================
# Tool implementations
# ============================================================


def fee_calculator(
    annual_tuition_fee: float,
    number_of_years: int,
    annual_hostel_fee: float = 0.0,
    scholarship_percentage: float = 0.0,
) -> str:
    """
    Compute total BVRIT Hyderabad fee amounts across multiple academic years,
    including tuition, hostel, and scholarship discounts.

    Args:
        annual_tuition_fee: Yearly tuition in INR
        number_of_years: Duration of the programme (4 or 2)
        annual_hostel_fee: Yearly hostel fee in INR (0 if not applicable)
        scholarship_percentage: Discount percentage on tuition (0–100)

    Returns:
        str: A human-readable breakdown of the fee calculation.
    """
    total_tuition = annual_tuition_fee * number_of_years
    total_hostel = annual_hostel_fee * number_of_years
    total_before_scholarship = total_tuition + total_hostel

    scholarship_amount = total_tuition * (scholarship_percentage / 100.0)
    total_after_scholarship = total_before_scholarship - scholarship_amount

    lines = [
        f"📊 **BVRIT Fee Calculation**",
        f"",
        f"| Component | Amount |",
        f"|---|---|",
        f"| Annual Tuition | ₹{annual_tuition_fee:,.0f} |",
        f"| Programme Duration | {number_of_years} years |",
        f"| **Total Tuition ({number_of_years} yrs)** | **₹{total_tuition:,.0f}** |",
    ]

    if annual_hostel_fee > 0:
        lines.append(f"| Annual Hostel Fee | ₹{annual_hostel_fee:,.0f} |")
        lines.append(f"| **Total Hostel ({number_of_years} yrs)** | **₹{total_hostel:,.0f}** |")

    lines.append(f"| **Total (before scholarship)** | **₹{total_before_scholarship:,.0f}** |")

    if scholarship_percentage > 0:
        lines.append(f"| Scholarship Discount | {scholarship_percentage:.0f}% |")
        lines.append(f"| Scholarship Amount (on tuition) | ₹{scholarship_amount:,.0f} |")
        lines.append(f"| **Total (after scholarship)** | **₹{total_after_scholarship:,.0f}** |")
        lines.append(f"")
        lines.append(f"*You save ₹{scholarship_amount:,.0f} with the {scholarship_percentage:.0f}% scholarship.*")
    else:
        lines.append(f"| **Total** | **₹{total_before_scholarship:,.0f}** |")
        lines.append(f"")
        lines.append(f"*No scholarship applied. Contact the admissions office for available scholarships.*")

    lines.append(f"\n💡 *Note: Fees are payable annually. Does not include optional transport (₹45,000/yr), "
                 f"lab fee (₹15,000/yr), library fee (₹8,000/yr), exam fee (₹10,000/yr), "
                 f"activity fee (₹3,000/yr), and one-time fees (₹15,000).*")

    result = "\n".join(lines)
    logger.info(f"fee_calculator result:\n{result}")
    return result


def date_checker(target_date: str, date_label: str) -> str:
    """
    Compare a BVRIT-related date (admission deadline, exam date, event date)
    against today's date and report whether it is past, upcoming, or how many
    days remain.

    Args:
        target_date: Date in YYYY-MM-DD format
        date_label: Human-readable label for the date

    Returns:
        str: Status message about the date.
    """
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        return f"❌ Invalid date format '{target_date}'. Please use YYYY-MM-DD format."

    today = date.today()

    diff_days = (target - today).days

    if diff_days < 0:
        abs_diff = abs(diff_days)
        if abs_diff == 0:
            return f"📅 **{date_label}**: Today!"
        elif abs_diff == 1:
            return f"📅 **{date_label}**: Was **yesterday** ({target_date})."
        elif abs_diff < 30:
            return f"📅 **{date_label}**: Passed **{abs_diff} days ago** ({target_date})."
        else:
            months = abs_diff // 30
            return f"📅 **{date_label}**: Passed **{months} month(s) ago** ({target_date})."
    elif diff_days == 0:
        return f"📅 **{date_label}**: **Today!** ({target_date})."
    elif diff_days == 1:
        return f"📅 **{date_label}**: **Tomorrow!** ({target_date})."
    elif diff_days <= 7:
        return f"📅 **{date_label}**: **{diff_days} days away** ({target_date}). Act soon!"
    elif diff_days <= 30:
        weeks = diff_days // 7
        remaining = diff_days % 7
        return (f"📅 **{date_label}**: **{diff_days} days** ({weeks} week{'s' if weeks > 1 else ''}"
                f"{f', {remaining} day{'s' if remaining > 1 else ''}' if remaining else ''}) away "
                f"({target_date}).")
    else:
        months = diff_days // 30
        return f"📅 **{date_label}**: **{months} month(s)** away ({target_date})."


def percentage_calculator(
    numerator: float,
    denominator: float,
    calculation_context: str,
) -> str:
    """
    Compute percentage-based metrics from BVRIT Hyderabad data, such as
    placement rates, scholarship percentages, or admission cutoff conversions.

    Args:
        numerator: The part value (e.g., students placed)
        denominator: The total value (e.g., total students)
        calculation_context: Description of what this percentage represents

    Returns:
        str: Human-readable percentage result with the calculation shown.
    """
    if denominator <= 0:
        return f"❌ **{calculation_context}**: Cannot calculate — denominator must be positive (got {denominator})."

    percentage = (numerator / denominator) * 100.0

    # Format result
    if percentage == int(percentage):
        pct_str = f"{int(percentage)}%"
    else:
        pct_str = f"{percentage:.1f}%"

    lines = [
        f"📈 **Percentage Calculation: {calculation_context}**",
        f"",
        f"| Component | Value |",
        f"|---|---|",
        f"| Part (numerator) | {numerator:,.0f} |",
        f"| Total (denominator) | {denominator:,.0f} |",
        f"| **Result** | **{pct_str}** |",
        f"",
        f"*{numerator:,.0f} ÷ {denominator:,.0f} × 100 = {pct_str}*",
    ]

    result = "\n".join(lines)
    logger.info(f"percentage_calculator ({calculation_context}): {pct_str}")
    return result


# ============================================================
# Tool registry
# ============================================================

TOOL_REGISTRY = {
    "fee_calculator": {
        "fn": fee_calculator,
        "description": (
            "Compute total BVRIT Hyderabad fee amounts across multiple academic "
            "years, including tuition, hostel, and scholarship discounts. Use this "
            "when a student asks about total cost of a programme, fee breakdown by "
            "year, hostel + tuition combined cost, or fee savings from a scholarship "
            "or EAMCET rank-based concession. Only call this for BVRIT-specific "
            "fee-related calculations — do NOT call this for general arithmetic or "
            "non-fee math problems."
        ),
    },
    "date_checker": {
        "fn": date_checker,
        "description": (
            "Compare a BVRIT-related date (admission deadline, exam date, event "
            "date, application closing date) against today's date and report whether "
            "it is past, upcoming, or how many days remain. Use this when a student "
            "asks if a deadline is still open, how many days are left for an exam, "
            "or whether an event has already passed. Only call this for BVRIT-specific "
            "dates extracted from the knowledge base — do NOT call this for general "
            "date formatting, date-to-string conversion, or non-BVRIT date questions."
        ),
    },
    "percentage_calculator": {
        "fn": percentage_calculator,
        "description": (
            "Compute percentage-based metrics from BVRIT Hyderabad data, such as "
            "placement rates (students placed ÷ total students), scholarship "
            "percentages (discount off total fee), admission cutoff conversion "
            "(raw marks converted to percentage), or any other rate calculation "
            "derived from the BVRIT knowledge base. Use this when a student asks "
            "about placement percentage, scholarship rate, cutoff percentage, or "
            "any proportion/rate based on BVRIT numbers. Only call this for "
            "BVRIT-specific percentage calculations — do NOT call this for simple "
            "percentage-of-a-number problems that the LLM can compute in-head, or "
            "for non-BVRIT percentage calculations."
        ),
    },
}


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Return tool definitions in OpenAI function-calling format,
    suitable for passing to `llm.bind_tools()` or the OpenRouter API.

    Returns:
        List[dict]: Tool definitions with name, description, and parameters schema.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "fee_calculator",
                "description": TOOL_REGISTRY["fee_calculator"]["description"],
                "parameters": FeeCalculatorInput.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "date_checker",
                "description": TOOL_REGISTRY["date_checker"]["description"],
                "parameters": DateCheckerInput.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "percentage_calculator",
                "description": TOOL_REGISTRY["percentage_calculator"]["description"],
                "parameters": PercentageCalculatorInput.model_json_schema(),
            },
        },
    ]


def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool by name with the given arguments and return its result.

    Args:
        tool_name: Name of the tool to execute.
        arguments: Dictionary of argument names to values.

    Returns:
        str: Tool execution result text.

    Raises:
        ValueError: If the tool name is unknown.
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}")

    tool_fn = TOOL_REGISTRY[tool_name]["fn"]
    logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
    result = tool_fn(**arguments)
    logger.info(f"Tool '{tool_name}' result: {result[:200]}...")
    return result