"""
5-turn Coreference Resolution Test for BVRIT FAQ Chatbot.

Test script that runs the exact conversation:
Turn 1: "What B.Tech branches does BVRIT offer?"
Turn 2: "Tell me more about the first one."
Turn 3: "What's the fee for that branch?"
Turn 4: "My name is Priya."
Turn 5: "What's my name and which branch was I asking about?"

Requires: The RAG pipeline to be initialized (ingested knowledge base).
"""
import sys
import os
import json
import logging

# Ensure we can import from the project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Silence verbose loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)

from ingest import run_ingestion
from rag import create_rag_pipeline, RAGResponse


def run_test():
    print("\n" + "=" * 70)
    print("BVRIT CHATBOT - 5-TURN COREFERENCE RESOLUTION TEST")
    print("=" * 70)

    # Initialize the pipeline
    print("\n[INIT] Ingesting knowledge base and creating RAG pipeline...")
    try:
        ingestor = run_ingestion()
        rag = create_rag_pipeline(
            vector_store=ingestor.vector_store,
            debug=False,
        )
        print("[INIT] Pipeline ready.\n")
    except Exception as e:
        print(f"[FATAL] Failed to initialize: {e}")
        sys.exit(1)

    # Conversation state
    messages = []  # list of {"role": "user"/"assistant", "content": str}
    results = []

    # ================================================================
    # TURN 1: "What B.Tech branches does BVRIT offer?"
    # ================================================================
    turn = 1
    question = "What B.Tech branches does BVRIT offer?"
    print(f"{'─' * 70}")
    print(f"TURN {turn}: {question}")
    print(f"{'─' * 70}")

    messages.append({"role": "user", "content": question})
    response: RAGResponse = rag.answer(question, chat_history=messages[:-1])
    messages.append({"role": "assistant", "content": response.answer})

    print(f"\nANSWER: {response.answer}\n")
    results.append({"turn": turn, "question": question, "answer": response.answer})

    # ================================================================
    # TURN 2: "Tell me more about the first one."
    # ================================================================
    turn = 2
    question = "Tell me more about the first one."
    print(f"{'─' * 70}")
    print(f"TURN {turn}: {question}")
    print(f"{'─' * 70}")

    messages.append({"role": "user", "content": question})
    response: RAGResponse = rag.answer(question, chat_history=messages[:-1])
    messages.append({"role": "assistant", "content": response.answer})

    print(f"\nANSWER: {response.answer}\n")
    results.append({"turn": turn, "question": question, "answer": response.answer})

    # ================================================================
    # TURN 3: "What's the fee for that branch?"
    # ================================================================
    turn = 3
    question = "What's the fee for that branch?"
    print(f"{'─' * 70}")
    print(f"TURN {turn}: {question}")
    print(f"{'─' * 70}")

    messages.append({"role": "user", "content": question})
    response: RAGResponse = rag.answer(question, chat_history=messages[:-1])
    messages.append({"role": "assistant", "content": response.answer})

    print(f"\nANSWER: {response.answer}\n")
    results.append({"turn": turn, "question": question, "answer": response.answer})

    # ================================================================
    # TURN 4: "My name is Priya."
    # ================================================================
    turn = 4
    question = "My name is Priya."
    print(f"{'─' * 70}")
    print(f"TURN {turn}: {question}")
    print(f"{'─' * 70}")

    messages.append({"role": "user", "content": question})
    response: RAGResponse = rag.answer(question, chat_history=messages[:-1])
    messages.append({"role": "assistant", "content": response.answer})

    print(f"\nANSWER: {response.answer}\n")
    results.append({"turn": turn, "question": question, "answer": response.answer})

    # ================================================================
    # TURN 5: "What's my name and which branch was I asking about?"
    # ================================================================
    turn = 5
    question = "What's my name and which branch was I asking about?"
    print(f"{'─' * 70}")
    print(f"TURN {turn}: {question}")
    print(f"{'─' * 70}")

    messages.append({"role": "user", "content": question})
    response: RAGResponse = rag.answer(question, chat_history=messages[:-1])
    messages.append({"role": "assistant", "content": response.answer})

    print(f"\nANSWER: {response.answer}\n")
    results.append({"turn": turn, "question": question, "answer": response.answer})

    # ================================================================
    # PASS/FAIL ANALYSIS
    # ================================================================
    print("=" * 70)
    print("RESULTS & PASS/FAIL ANALYSIS")
    print("=" * 70)

    analysis = []
    answer2_lower = results[1]["answer"].lower() if len(results) > 1 else ""
    answer3_lower = results[2]["answer"].lower() if len(results) > 2 else ""
    answer5_lower = results[3]["answer"].lower() if len(results) > 3 else ""

    # Turn 2: Must answer about CSE (Computer Science & Engineering) — the first branch
    if len(results) >= 2:
        turn2_pass = "cse" in answer2_lower or "computer science" in answer2_lower or "computer science & engineering" in answer2_lower or "computer science and engineering" in answer2_lower
        analysis.append({
            "turn": 2,
            "criteria": "Answers about CSE (first branch in list)",
            "pass": turn2_pass,
            "detail": f"Answer mentions CSE/Computer Science: {turn2_pass}",
        })
    else:
        analysis.append({"turn": 2, "criteria": "Answers about CSE", "pass": False, "detail": "No answer available"})

    # Turn 3: Must give CSE's fee
    if len(results) >= 3:
        turn3_pass = "cse" in answer3_lower or "computer science" in answer3_lower or "computer science & engineering" in answer3_lower or "computer science and engineering" in answer3_lower
        turn3_pass = turn3_pass and ("fee" in answer3_lower or "₹" in answer3_lower or "rs" in answer3_lower or "rupees" in answer3_lower or "cost" in answer3_lower or "tuition" in answer3_lower)
        analysis.append({
            "turn": 3,
            "criteria": "Gives CSE's fee",
            "pass": turn3_pass,
            "detail": f"Answer mentions CSE + fee information: {turn3_pass}",
        })
    else:
        analysis.append({"turn": 3, "criteria": "Gives CSE's fee", "pass": False, "detail": "No answer available"})

    # Turn 5: Must say "Priya" and "CSE"
    if len(results) >= 5:
        answer5_lower = results[4]["answer"].lower()
        has_priya = "priya" in answer5_lower
        has_cse = "cse" in answer5_lower or "computer science" in answer5_lower or "computer science & engineering" in answer5_lower or "computer science and engineering" in answer5_lower
        turn5_pass = has_priya and has_cse
        analysis.append({
            "turn": 5,
            "criteria": "Says 'Priya' and 'CSE'",
            "pass": turn5_pass,
            "detail": f"Contains 'Priya': {has_priya}, Contains 'CSE/CS': {has_cse}",
        })
    else:
        analysis.append({"turn": 5, "criteria": "Says 'Priya' and 'CSE'", "pass": False, "detail": "No answer available"})

    # Print analysis
    all_pass = True
    for a in analysis:
        status = "✅ PASS" if a["pass"] else "❌ FAIL"
        if not a["pass"]:
            all_pass = False
        print(f"\nTurn {a['turn']}: {status}")
        print(f"  Criteria: {a['criteria']}")
        print(f"  Detail:   {a['detail']}")

    print(f"\n{'=' * 70}")
    if all_pass:
        print("🎉 OVERALL RESULT: ALL TESTS PASSED")
    else:
        print("❌ OVERALL RESULT: SOME TESTS FAILED")
    print(f"{'=' * 70}")

    # Save results to JSON
    output = {
        "test_script": "5-turn coreference resolution",
        "pass_criteria": {
            "turn_2": "Answers about CSE (the first in the list)",
            "turn_3": "Gives CSE's fee",
            "turn_5": "Says 'Priya' and 'CSE'",
        },
        "all_passed": all_pass,
        "analysis": analysis,
        "conversation": results,
    }

    output_path = "test_results_coreference.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    run_test()