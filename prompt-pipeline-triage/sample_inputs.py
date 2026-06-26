"""
sample_inputs.py
Three test inputs for the pipeline:
  - CLEAN_INPUT_1: a normal complaint, all fields present, angry sentiment
  - CLEAN_INPUT_2: a different issue type/sentiment, to show variety
  - BROKEN_INPUT:  deliberately missing order_id, mixed language / garbled
"""

CLEAN_INPUT_1 = """\
Hi, this is Maria Gomez. I ordered a blender (order #58213-A) NINE days ago \
and it still hasn't shipped. Your tracking page just says "processing" the \
whole time. This is honestly ridiculous, I needed this for a birthday gift \
that already happened. I want a real answer, not a copy-paste apology.\
"""

CLEAN_INPUT_2 = """\
hey there :) quick question -- i was charged twice for my subscription this \
month (order ORD-99281), once on the 2nd and again on the 14th. i'm sure \
it's just a glitch, no big deal, just want to get one of those refunded \
whenever you get a chance. thanks so much, you guys are great otherwise!\
"""

# Deliberately broken: no order id given at all, and the message mixes in
# a chunk of garbled / non-English text plus a typo-laden, hard-to-parse
# complaint. This is the input used to demonstrate graceful degradation:
# Stage 1 should set order_id=null, add it to missing_fields, and may set
# is_garbled=true; Stage 2 should fall back to P3/general; Stage 3 should
# ask the customer for the missing order info rather than invent it.
BROKEN_INPUT = """\
asdkj my pakage NEVER ARRIVE!!! ya no se que pasa con esto, llevo esperando \
no se cuantos dias, esto es una porqueria total. fix it NOW pls. no tengo \
numero de orden a la mano ni nada, solo compre algo la semana pasada o tal \
vez fue hace dos semanas no recuerdo bien. asjdklasjdk.\
"""

SAMPLE_INPUTS = {
    "Clean example 1 (shipping delay, angry)": CLEAN_INPUT_1,
    "Clean example 2 (double charge, casual/friendly)": CLEAN_INPUT_2,
    "Broken example (no order ID, mixed language, garbled)": BROKEN_INPUT,
}
