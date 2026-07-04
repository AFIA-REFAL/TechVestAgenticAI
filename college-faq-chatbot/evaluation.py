"""
BVRIT Hyderabad College FAQ Chatbot - Evaluation Pipeline

Runs generated test cases through the RAG pipeline and evaluates
responses using an LLM Judge. Generates comprehensive evaluation
reports in JSON and CSV formats.

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import os
import json
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from langchain_chroma import Chroma

from config import settings, logger
from rag import RAGPipeline, RAGResponse
from utils import (
    get_llm_client,
    get_openai_client,
    extract_json_from_response,
    Timer,
)
from prompts import get_prompts

logger = logging.getLogger(__name__)


class TestCaseGenerator:
    """
    Generates evaluation test cases using GPT-4o Mini.
    Creates 20 test cases across multiple dimensions.
    """

    DIMENSIONS = {
        "Functional": 3,
        "Quality": 3,
        "Safety": 2,
        "Security": 2,
        "Robustness": 3,
        "Performance": 2,
        "Context": 2,
        "RAGAS": 3,
    }

    def __init__(self):
        self.client = get_openai_client()
        self.model = settings.llm_model

    def generate(self) -> List[Dict[str, Any]]:
        """
        Generate 20 evaluation test cases using the LLM.

        Returns:
            List[Dict]: Test cases with question, expected_answer, dimension, pass_criteria
        """
        logger.info("Generating evaluation test cases...")

        test_cases = []
        for dimension, count in self.DIMENSIONS.items():
            for i in range(count):
                test_case = self._generate_single(dimension, i + 1)
                if test_case:
                    test_cases.append(test_case)

        logger.info(f"Generated {len(test_cases)} test cases")
        return test_cases

    def _generate_single(self, dimension: str, index: int) -> Optional[Dict[str, Any]]:
        """
        Generate a single test case for a given dimension.

        Args:
            dimension: Evaluation dimension
            index: Test case number within dimension

        Returns:
            Optional[Dict]: Test case or None on failure
        """
        prompt = f"""Generate a test case for evaluating a RAG chatbot for BVRIT Hyderabad College of Engineering for Women.

Dimension: {dimension}
Test Case #{index} for this dimension

The chatbot has access to a knowledge base containing information about:
- College overview, vision, mission
- Admission process, EAMCET ranks, required documents
- Under Graduate programs (CSE, etc.)
- Post Graduate programs (Data Sciences, etc.)
- Management information
- Events, workshops, FDPs
- Awards and recognitions
- Placement information
- Contact details

Generate a realistic question that a prospective student or parent might ask.

Output ONLY valid JSON (no other text):
{{
    "question": "The question to ask the chatbot",
    "expected_answer": "What the correct answer should contain",
    "dimension": "{dimension}",
    "pass_criteria": "How to determine if the answer passes"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            result = extract_json_from_response(content)

            if result and all(k in result for k in ["question", "expected_answer", "dimension"]):
                return result
            else:
                logger.warning(f"Invalid test case generated for {dimension}#{index}")
                return None

        except Exception as e:
            logger.error(f"Error generating test case {dimension}#{index}: {e}")
            return None


class Evaluator:
    """
    Runs test cases through the RAG pipeline and evaluates responses.
    Uses LLM Judge for automated evaluation, EXCEPT for the Performance
    dimension, which the brief specifies must be a numerical SLA check,
    not an LLM judgment.
    """

    PERFORMANCE_SLA_SECONDS = 10.0

    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Initialize the evaluator.

        Args:
            rag_pipeline: Configured RAG pipeline
        """
        self.rag = rag_pipeline
        self.llm = get_llm_client()
        self.prompts = get_prompts()
        self.results: List[Dict[str, Any]] = []

    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test case through the RAG pipeline and evaluate.

        Args:
            test_case: Test case with question, expected_answer, dimension

        Returns:
            Dict: Evaluation result
        """
        question = test_case["question"]
        expected_answer = test_case["expected_answer"]
        dimension = test_case.get("dimension", "Functional")

        logger.info(f"Running test case [{dimension}]: {question[:80]}...")

        # Run through RAG pipeline
        with Timer() as timer:
            response: RAGResponse = self.rag.answer(question)

        # Performance is a numerical SLA check per the brief, not an LLM
        # judgment — judging latency with an LLM is meaningless and was
        # a spec mismatch in the original build.
        if dimension == "Performance":
            judge_result = self._check_performance_sla(timer.elapsed)
        else:
            judge_result = self._judge_response(
                dimension=dimension,
                expected_answer=expected_answer,
                actual_answer=response.answer,
                retrieved_context=response.context_used,
            )

        result = {
            "question": question,
            "expected_answer": expected_answer,
            "actual_answer": response.answer,
            "retrieved_chunks": response.retrieved_chunks,
            "retrieved_metadata": response.retrieved_metadata,
            "latency_seconds": timer.elapsed,
            "dimension": dimension,
            "pass": judge_result.get("pass", False),
            "score": judge_result.get("score", 0),
            "failure_reason": judge_result.get("reason", ""),
            "hallucinations": judge_result.get("hallucinations", ""),
            "missing_information": judge_result.get("missing_information", ""),
            "recommendation": judge_result.get("recommendation", ""),
            "token_usage": response.token_usage,
            "citations": response.citations,
            "refused": response.refused,
            "timestamp": datetime.now().isoformat(),
        }

        self.results.append(result)
        return result

    def _check_performance_sla(self, latency_seconds: float) -> Dict[str, Any]:
        """
        Numeric SLA check for the Performance dimension (Dimension 06).
        The brief is explicit that this must be a code check, not an
        LLM judgment.

        Args:
            latency_seconds: Measured response latency for this test case

        Returns:
            Dict: Result shaped like a judge result so the rest of the
                pipeline (reporting, CSV export) doesn't need special-casing
        """
        passed = latency_seconds <= self.PERFORMANCE_SLA_SECONDS
        return {
            "pass": passed,
            "score": 10 if passed else 0,
            "reason": (
                f"Responded in {latency_seconds:.2f}s "
                f"({'within' if passed else 'exceeds'} the "
                f"{self.PERFORMANCE_SLA_SECONDS:.0f}s SLA)"
            ),
            "hallucinations": "",
            "missing_information": "",
            "recommendation": (
                "None — within SLA" if passed
                else "Reduce top_k, use a faster model, or cache embeddings to cut latency"
            ),
        }

    def _judge_response(
        self,
        dimension: str,
        expected_answer: str,
        actual_answer: str,
        retrieved_context: str,
    ) -> Dict[str, Any]:
        """
        Use LLM Judge to evaluate the chatbot's response.

        Args:
            dimension: Evaluation dimension
            expected_answer: Expected correct answer
            actual_answer: Chatbot's generated answer
            retrieved_context: Context used for generation

        Returns:
            Dict: Judge evaluation result
        """
        prompt = self.prompts.format_judge_prompt(
            dimension=dimension,
            expected_answer=expected_answer,
            actual_answer=actual_answer,
            retrieved_context=retrieved_context,
        )

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            result = extract_json_from_response(content)

            if result:
                return result
            else:
                logger.warning("Judge returned non-JSON response, using fallback")
                return {
                    "pass": False,
                    "score": 5,
                    "reason": "Could not parse judge response",
                    "hallucinations": "",
                    "missing_information": "",
                    "recommendation": "Improve response quality",
                }

        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return {
                "pass": False,
                "score": 0,
                "reason": f"Judge error: {e}",
                "hallucinations": "",
                "missing_information": "",
                "recommendation": "Fix judge pipeline",
            }

    def run_all(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run all test cases through evaluation.

        Args:
            test_cases: List of test cases

        Returns:
            List[Dict]: All evaluation results
        """
        self.results = []
        total = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Test case {i}/{total}")
            self.run_test_case(test_case)

        return self.results

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive evaluation report.

        Returns:
            Dict: Evaluation report with statistics
        """
        if not self.results:
            return {"error": "No results to report"}

        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("pass", False))
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        # Dimension breakdown
        dimensions = {}
        for r in self.results:
            dim = r.get("dimension", "Unknown")
            if dim not in dimensions:
                dimensions[dim] = {"total": 0, "passed": 0, "scores": []}
            dimensions[dim]["total"] += 1
            if r.get("pass", False):
                dimensions[dim]["passed"] += 1
            dimensions[dim]["scores"].append(r.get("score", 0))

        # Find weakest dimension
        weakest_dim = min(
            dimensions.items(),
            key=lambda x: (
                x[1]["passed"] / x[1]["total"] if x[1]["total"] > 0 else 0
            ),
        )

        # Failed test cases
        failed_cases = [r for r in self.results if not r.get("pass", False)]

        # Average latency
        avg_latency = (
            sum(r.get("latency_seconds", 0) for r in self.results) / total
        )

        report = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "total_test_cases": total,
            "passed": passed,
            "failed": failed,
            "pass_rate_percentage": round(pass_rate, 2),
            "average_latency_seconds": round(avg_latency, 3),
            "weakest_dimension": {
                "name": weakest_dim[0],
                "pass_rate": round(
                    weakest_dim[1]["passed"] / weakest_dim[1]["total"] * 100
                    if weakest_dim[1]["total"] > 0 else 0,
                    2,
                ),
            },
            "dimension_breakdown": {
                dim: {
                    "total": stats["total"],
                    "passed": stats["passed"],
                    "pass_rate": round(
                        stats["passed"] / stats["total"] * 100
                        if stats["total"] > 0 else 0,
                        2,
                    ),
                    "average_score": round(
                        sum(stats["scores"]) / len(stats["scores"])
                        if stats["scores"] else 0,
                        2,
                    ),
                }
                for dim, stats in dimensions.items()
            },
            "failed_test_cases": [
                {
                    "question": r["question"],
                    "dimension": r["dimension"],
                    "failure_reason": r.get("failure_reason", ""),
                    "score": r.get("score", 0),
                }
                for r in failed_cases
            ],
            "recommendations": self._generate_recommendations(dimensions),
        }

        return report

    def _generate_recommendations(
        self, dimensions: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on evaluation results.

        Args:
            dimensions: Dimension breakdown data

        Returns:
            List[str]: Recommendations
        """
        recommendations = []

        for dim, stats in dimensions.items():
            pass_rate = (
                stats["passed"] / stats["total"] * 100
                if stats["total"] > 0 else 0
            )
            avg_score = (
                sum(stats["scores"]) / len(stats["scores"])
                if stats["scores"] else 0
            )

            if pass_rate < 60:
                recommendations.append(
                    f"Critical: {dim} dimension has {pass_rate:.0f}% pass rate "
                    f"(avg score: {avg_score:.1f}/10). Needs immediate improvement."
                )
            elif pass_rate < 80:
                recommendations.append(
                    f"Warning: {dim} dimension has {pass_rate:.0f}% pass rate "
                    f"(avg score: {avg_score:.1f}/10). Consider improvements."
                )

        if not recommendations:
            recommendations.append(
                "All dimensions performing well. Continue monitoring."
            )

        return recommendations

    def save_report(self, report: Dict[str, Any]) -> None:
        """
        Save evaluation report to JSON and CSV files.

        Args:
            report: Evaluation report dictionary
        """
        # Save JSON
        json_path = Path(settings.evaluation_report_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Evaluation report saved to: {json_path}")

        # Save CSV
        csv_path = Path(settings.evaluation_csv_path)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        logger.info(f"Evaluation CSV saved to: {csv_path}")


def run_evaluation(rag_pipeline: RAGPipeline) -> Dict[str, Any]:
    """
    Run complete evaluation: generate test cases, evaluate, save report.

    Args:
        rag_pipeline: Configured RAG pipeline

    Returns:
        Dict: Evaluation report
    """
    logger.info("=" * 60)
    logger.info("EVALUATION PIPELINE")
    logger.info("=" * 60)

    # Generate test cases
    generator = TestCaseGenerator()
    test_cases = generator.generate()

    # Save test cases
    test_path = Path(settings.test_cases_path)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, indent=2, ensure_ascii=False)
    logger.info(f"Test cases saved to: {test_path}")

    # Run evaluation
    evaluator = Evaluator(rag_pipeline)
    evaluator.run_all(test_cases)

    # Generate and save report
    report = evaluator.generate_report()
    evaluator.save_report(report)

    logger.info(f"\n{'=' * 60}")
    logger.info("EVALUATION SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Total test cases: {report['total_test_cases']}")
    logger.info(f"Passed: {report['passed']}")
    logger.info(f"Failed: {report['failed']}")
    logger.info(f"Pass rate: {report['pass_rate_percentage']}%")
    logger.info(f"Average latency: {report['average_latency_seconds']}s")
    logger.info(f"Weakest dimension: {report['weakest_dimension']['name']}")
    logger.info(f"{'=' * 60}\n")

    return report