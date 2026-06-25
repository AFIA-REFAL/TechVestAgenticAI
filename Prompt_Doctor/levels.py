"""
prompt_doctor/levels.py

The 5-level ladder of prompt engineering mastery,
plus domains with per-level sample inputs.

Each domain has 5 tasks (one per level) that share the same theme.
The student picks ONE domain at level 1 and keeps it across all levels.
"""

LEVELS = {
    1: {
        "name": "Basic Prompting",
        "description": (
            "Focus on role definition, clear instruction, and task completeness."
        ),
        "principles": [
            "Output is relevant and correct.",
            "No missing parts.",
            "No irrelevant content."
        ],
    },
    2: {
        "name": "Structured Output",
        "description": (
            "Focus on output schemas (JSON / strict format) "
            "and deterministic formatting."
        ),
        "principles": [
            "Valid JSON every run.",
            "All required fields present.",
            "No extra/unstructured text."
        ],
    },
    3: {
        "name": "Few-shot Learning",
        "description": (
            "Focus on providing examples for ambiguous cases "
            "and pattern teaching."
        ),
        "principles": [
            "Correct handling of tricky inputs.",
            "Output matches pattern shown in examples."
        ],
    },
    4: {
        "name": "Reasoning Tasks",
        "description": (
            "Focus on multi-step reasoning, edge-case handling, "
            "and structured thinking prompts."
        ),
        "principles": [
            "Correct multi-step outputs.",
            "Handles hidden constraints.",
            "No logic breakdown in complex cases."
        ],
    },
    5: {
        "name": "Robust / Adversarial Prompting",
        "description": (
            "Focus on prompt resilience, noise handling, "
            "input sanitization instructions, and constraint enforcement."
        ),
        "principles": [
            "Stable outputs under messy/adversarial input.",
            "No hallucinated or broken formatting.",
            "Strict compliance with rules."
        ],
    },
}


DOMAINS = {
    "Healthcare": {
        "description": (
            "Symptom summarization (non-diagnostic), medical report simplification, "
            "appointment message drafting, wellness instruction formatting."
        ),
        "tasks": {
            1: (
                "Summarize the following patient symptoms in a clear, structured format: "
                "Patient reports intermittent headaches for 3 weeks, fatigue, "
                "and occasional dizziness."
            ),
            2: (
                "Format a medical appointment reminder message for a patient. "
                "Include patient name, date, time, location, "
                "and preparation instructions as a structured JSON object."
            ),
            3: (
                "Classify the urgency of the following patient messages as "
                "'routine', 'urgent', or 'emergency'.\n\n"
                "Examples:\n"
                "- 'I have a mild cough' -> routine\n"
                "- 'Chest pain radiating to arm' -> emergency\n"
                "- 'Persistent low-grade fever for 5 days' -> urgent\n\n"
                "Now classify: "
                "'I twisted my ankle and it\\'s swollen but I can walk.'"
            ),
            4: (
                "Analyze this medication schedule for potential issues:\n"
                "Patient A takes Metformin 500mg twice daily with meals, "
                "Lisinopril 10mg once daily in morning, "
                "and Ibuprofen 400mg as needed for pain.\n"
                "Identify conflicts, timing concerns, and provide recommendations."
            ),
            5: (
                "Extract and structure the following information from this noisy "
                "clinical note, ignoring irrelevant content:\n\n"
                "'Pt c/o SOB x3 days, also mentioned they like gardening. "
                "Hx of asthma, HTN. Meds: albuterol PRN, lisinopril 10mg. "
                "Allergies: NKDA. Vitals: BP 138/88, HR 92, RR 20, SpO2 95% on RA. "
                "Oh and they have a cat named Whiskers.'\n\n"
                "Return only a structured summary."
            ),
        },
    },
    "Legal": {
        "description": (
            "Contract clause summarization, legal text simplification, "
            "compliance checklist generation, document structure extraction. "
            "⚠ No legal advice generation."
        ),
        "tasks": {
            1: (
                "Summarize the following contract clause in plain language:\n"
                "'The Party of the First Part shall indemnify and hold harmless "
                "the Party of the Second Part from any and all claims, damages, "
                "losses, and expenses arising out of or related to the breach "
                "of this Agreement by the Party of the First Part.'"
            ),
            2: (
                "Extract key terms from this contract section and return them "
                "as a structured JSON object:\n"
                "'Term: 12 months. Renewal: automatic unless 30-day notice given. "
                "Termination: for cause with 14-day cure period. "
                "Fees: $500/month payable on the 1st.'"
            ),
            3: (
                "Classify the following contract provisions by type "
                "(liability, payment, confidentiality, termination).\n\n"
                "Examples:\n"
                "- 'Party A shall not disclose confidential information' "
                "-> confidentiality\n"
                "- 'Payment shall be made within 30 days' -> payment\n\n"
                "Now classify:\n"
                "'Either party may terminate this agreement with 30 days notice.'"
            ),
            4: (
                "Identify potential risks and issues in this non-disclosure "
                "agreement clause:\n\n"
                "'Confidential information includes all information disclosed "
                "by either party, except information that:\n"
                "(a) is or becomes publicly available through no fault of the "
                "receiving party;\n"
                "(b) was already known to the receiving party;\n"
                "(c) is independently developed by the receiving party.'\n\n"
                "Explain why each exception could be a risk."
            ),
            5: (
                "Process this noisy legal document excerpt. Ignore annotations, "
                "cross-outs, and margin notes. Extract only the operative clauses "
                "and structure them:\n\n"
                "'This AGREEMENT (the \"Agreement\") is entered into "
                "[strikethrough: on this 15th day] as of Jan 1, 2024. "
                "/// MARGIN NOTE: check effective date /// "
                "BETWEEN: ABC Corp (\"Company\") and John Doe (\"Consultant\"). "
                "Company engages Consultant for 6 months. "
                "Company will pay $10,000 total. "
                "/// STRIKETHROUGH: payable in installments /// "
                "Consultant will deliver final report by June 30.'"
            ),
        },
    },
    "Customer Support": {
        "description": (
            "Ticket classification, complaint summarization, "
            "response drafting, refund / escalation structuring."
        ),
        "tasks": {
            1: (
                "Classify the following customer support ticket by category "
                "and priority:\n"
                "'I ordered a laptop 2 weeks ago and it still hasn't shipped. "
                "Order #12345. I need it by Friday for a work trip.'"
            ),
            2: (
                "Summarize this customer complaint and return the summary as "
                "a structured JSON with fields: issue_type, customer_tone, "
                "required_action:\n\n"
                "'I am absolutely furious! I received my order but it's "
                "completely wrong - I ordered a blue medium shirt and got "
                "a red small. This is the THIRD time this has happened. "
                "I want a refund immediately and someone needs to explain "
                "why your company can't get a simple order right!'"
            ),
            3: (
                "Draft a response to the following customer complaint "
                "following the examples.\n\n"
                "Example 1: Complaint about late delivery -> "
                "Response: Apologize, explain delay, offer discount.\n"
                "Example 2: Complaint about defective product -> "
                "Response: Apologize, request photos, offer replacement.\n\n"
                "Now respond to:\n"
                "'I was charged twice for the same order "
                "and customer service hasn't responded to my emails.'"
            ),
            4: (
                "Analyze this customer support escalation and determine the "
                "appropriate resolution path. Consider the company's policies:\n"
                "- refunds within 30 days\n"
                "- replacements within 90 days\n"
                "- compensation only for verified errors\n\n"
                "'Customer bought premium subscription 45 days ago. "
                "The feature they paid for (unlimited storage) never worked "
                "properly. They've contacted support 4 times with no resolution. "
                "They're demanding a full refund and threatening chargeback.'"
            ),
            5: (
                "Process this customer chat transcript. Filter out filler words, "
                "typos, and irrelevant tangents. Extract the core issue, "
                "customer sentiment trend, and required action:\n\n"
                "'So ummm I bought this thing like a week ago? Actually no "
                "2 weeks. idk. Anyway it's broken. Like totally broken. "
                "Oh also can you believe the weather lately? So anyway "
                "I need a new one sent. Or a refund. Whatever. Also I'm "
                "really frustrated cause I've called like 3 times already smh.'"
            ),
        },
    },
    "Education": {
        "description": (
            "Quiz generation, concept explanation, "
            "essay feedback formatting, flashcard creation."
        ),
        "tasks": {
            1: (
                "Create 3 quiz questions about the water cycle "
                "for 5th-grade students. Include the questions and correct answers."
            ),
            2: (
                "Explain the concept of photosynthesis as a structured JSON "
                "with fields: concept_name, definition, key_components (array), "
                "and simple_analogy."
            ),
            3: (
                "Generate flashcards following this format.\n\n"
                "Example 1: Q: 'What is the capital of France?' A: 'Paris'\n"
                "Example 2: Q: 'What is 2+2?' A: '4'\n\n"
                "Now generate 3 flashcards about the causes of World War II."
            ),
            4: (
                "Evaluate this student essay paragraph for argument strength, "
                "evidence use, and logical flow. Then provide a structured "
                "critique with specific suggestions for improvement:\n\n"
                "'The Industrial Revolution was good because it created many "
                "inventions. People got jobs in factories. Some people say "
                "it was bad but I think it was mostly good. There were many "
                "changes during this time.'"
            ),
            5: (
                "Extract key concepts, definitions, and relationships from "
                "this noisy study notes text. Ignore [typos], random CAPS, "
                "and irrelevant tangents. Output a clean, structured study guide:\n\n"
                "'The mitochondria is [sp] the powerhouse of the cell!!! "
                "This is SO important for bio exam. Anyway. It produces ATP "
                "through cellular respiration. lol my friend says it's like "
                "a battery. ALSO DON'T FORGET: chloroplasts do photosynthesis "
                "in plants. OMG I'M SO TIRED. Oh and ribosomes make proteins. "
                "The end.'"
            ),
        },
    },
    "Finance": {
        "description": (
            "Expense categorization, budget summarization, "
            "transaction labeling, risk explanation (non-advisory)."
        ),
        "tasks": {
            1: (
                "Categorize the following expenses into categories "
                "(Housing, Food, Transportation, Entertainment, "
                "Utilities, Other):\n"
                "'Rent $1200, Groceries $350, Gas $60, "
                "Netflix $15, Electricity $85, Restaurant dinner $45.'"
            ),
            2: (
                "Summarize this monthly budget and return as a structured JSON "
                "with total_income, total_expenses, savings_rate, "
                "and a category_breakdown:\n\n"
                "'Income: $5000. Rent: $1400, Food: $600, Transport: $200, "
                "Utilities: $250, Entertainment: $100, "
                "Savings: $1450, Other: $200.'"
            ),
            3: (
                "Label each transaction as 'essential', 'discretionary', "
                "or 'recurring_bill' following these examples.\n\n"
                "Examples:\n"
                "- 'Mortgage payment $1500' -> essential\n"
                "- 'Netflix $15' -> recurring_bill\n"
                "- 'Starbucks latte $5' -> discretionary\n\n"
                "Now label:\n"
                "- 'Electric bill $95'\n"
                "- 'Amazon purchase $67'\n"
                "- 'Gym membership $50'\n"
                "- 'Restaurant dinner $80'\n"
                "- 'Insurance premium $200'"
            ),
            4: (
                "Analyze this investment portfolio for risk concentration, "
                "diversification issues, and asset allocation concerns.\n"
                "Note: This is educational only, not financial advice.\n\n"
                "'Portfolio: 80% in Tech stocks (AAPL, GOOGL, MSFT, AMZN, "
                "META), 10% in Bitcoin, 5% in cash, 5% in a single real "
                "estate ETF.'"
            ),
            5: (
                "Process this noisy financial data. Filter out duplicates, "
                "correct obvious typos, and categorize each transaction. "
                "Ignore personal notes and irrelevant entries:\n\n"
                "'Jan 5 - Starbucks - $5.75 - morning coffee lol\n"
                "Jan 5 - Starbucks - $5.75 - duplicate whoops\n"
                "Jan 6 - AMZN WEB SRVCS - $13.43 - AWS subscription\n"
                "Jan 7 - MCDONALDS - $12.50 - had a craving\n"
                "Jan 8 - PAYCHECK - $2500.00 - finally!!!\n"
                "Jan 9 - ROYAL BANK MTG - $1800 - mortgage\n"
                "Jan 10 - NETFLIX - $15.99'"
            ),
        },
    },
}