"""
BVRIT Hyderabad College FAQ Chatbot - RAGAS Evaluation Module

Calculates RAGAS metrics for evaluating RAG pipeline quality:
- Faithfulness: How factually accurate the answer is given the context
- Answer Relevancy: How relevant the answer is to the question
- Context Precision: How precise the retrieved context is
- Context Recall: How much relevant context was retrieved

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import pandas as pd
from datasets import Dataset

from config import settings, logger
from utils import get_openai_client

logger = logging.getLogger(__name__)


class RAGASEvaluator:
    """
    Evaluates RAG pipeline using RAGAS metrics.
    Calculates Faithfulness, Answer Relevancy, Context Precision,
    and Context Recall.
    """

    def __init__(self):
        """Initialize the RAGAS evaluator."""
        self.client = get_openai_client()
        self.metrics: Dict[str, float] = {}
        self.raw_scores: Dict[str, List[float]] = {
            "faithfulness": [],
            "answer_relevancy": [],
            "context_precision": [],
            "context_recall": [],
        }

    def evaluate(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[List[str]],
    ) -> Dict[str, float]:
        """
        Calculate RAGAS metrics for a set of Q&A pairs.

        Args:
            questions: List of user questions
            answers: List of generated answers
            contexts: List of lists of retrieved context chunks
            ground_truths: List of lists of ground truth answers

        Returns:
            Dict: RAGAS metrics scores
        """
        logger.info("Calculating RAGAS metrics...")

        # Create dataset
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
        dataset = Dataset.from_dict(data)

        # Calculate metrics using LLM-based evaluation
        for i in range(len(questions)):
            logger.info(f"Evaluating RAGAS for Q{i+1}/{len(questions)}...")

            faithfulness = self._calculate_faithfulness(
                answers[i], contexts[i]
            )
            answer_relevancy = self._calculate_answer_relevancy(
                questions[i], answers[i]
            )
            context_precision = self._calculate_context_precision(
                questions[i], contexts[i]
            )
            context_recall = self._calculate_context_recall(
                contexts[i], ground_truths[i]
            )

            self.raw_scores["faithfulness"].append(faithfulness)
            self.raw_scores["answer_relevancy"].append(answer_relevancy)
            self.raw_scores["context_precision"].append(context_precision)
            self.raw_scores["context_recall"].append(context_recall)

        # Calculate averages
        self.metrics = {
            "faithfulness": self._safe_average(self.raw_scores["faithfulness"]),
            "answer_relevancy": self._safe_average(self.raw_scores["answer_relevancy"]),
            "context_precision": self._safe_average(self.raw_scores["context_precision"]),
            "context_recall": self._safe_average(self.raw_scores["context_recall"]),
        }

        logger.info(f"RAGAS Metrics: {json.dumps(self.metrics, indent=2)}")
        return self.metrics

    def _calculate_faithfulness(
        self, answer: str, contexts: List[str]
    ) -> float:
        """
        Calculate Faithfulness score.
        Measures how factually accurate the answer is given the context.

        Args:
            answer: Generated answer
            contexts: Retrieved context chunks

        Returns:
            float: Faithfulness score (0-1)
        """
        context_text = "\n".join(contexts) if contexts else ""

        prompt = f"""Evaluate the faithfulness of the following answer based on the provided context.

Context:
{context_text[:2000]}

Answer:
{answer[:1000]}

Rate the faithfulness from 0.0 to 1.0 where:
- 1.0 = All claims in the answer are directly supported by the context
- 0.5 = Some claims are supported, some are not
- 0.0 = No claims are supported by the context

Output ONLY a number between 0.0 and 1.0:"""

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Faithfulness evaluation failed: {e}")
            return 0.5

    def _calculate_answer_relevancy(
        self, question: str, answer: str
    ) -> float:
        """
        Calculate Answer Relevancy score.
        Measures how relevant the answer is to the question.

        Args:
            question: User question
            answer: Generated answer

        Returns:
            float: Answer Relevancy score (0-1)
        """
        prompt = f"""Evaluate the relevancy of the following answer to the question.

Question:
{question}

Answer:
{answer[:1000]}

Rate the relevancy from 0.0 to 1.0 where:
- 1.0 = The answer directly and completely addresses the question
- 0.5 = The answer partially addresses the question
- 0.0 = The answer is completely irrelevant to the question

Output ONLY a number between 0.0 and 1.0:"""

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Answer relevancy evaluation failed: {e}")
            return 0.5

    def _calculate_context_precision(
        self, question: str, contexts: List[str]
    ) -> float:
        """
        Calculate Context Precision score.
        Measures how precise the retrieved context is for the question.

        Args:
            question: User question
            contexts: Retrieved context chunks

        Returns:
            float: Context Precision score (0-1)
        """
        if not contexts:
            return 0.0

        prompt = f"""Evaluate the precision of the retrieved context for answering the question.

Question:
{question}

Retrieved Context Chunks:
{chr(10).join([f'Chunk {i+1}: {c[:300]}' for i, c in enumerate(contexts)])}

Rate the precision from 0.0 to 1.0 where:
- 1.0 = All retrieved chunks are highly relevant to the question
- 0.5 = Some chunks are relevant, some are not
- 0.0 = No chunks are relevant to the question

Output ONLY a number between 0.0 and 1.0:"""

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Context precision evaluation failed: {e}")
            return 0.5

    def _calculate_context_recall(
        self, contexts: List[str], ground_truths: List[str]
    ) -> float:
        """
        Calculate Context Recall score.
        Measures how much of the ground truth is covered by the context.

        Args:
            contexts: Retrieved context chunks
            ground_truths: Ground truth answers

        Returns:
            float: Context Recall score (0-1)
        """
        if not contexts or not ground_truths:
            return 0.0

        context_text = "\n".join(contexts)[:2000]
        ground_truth_text = "\n".join(ground_truths)[:1000]

        prompt = f"""Evaluate how well the retrieved context covers the ground truth information.

Ground Truth:
{ground_truth_text}

Retrieved Context:
{context_text}

Rate the recall from 0.0 to 1.0 where:
- 1.0 = All information in the ground truth is present in the context
- 0.5 = Some information is present, some is missing
- 0.0 = No information from the ground truth is in the context

Output ONLY a number between 0.0 and 1.0:"""

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Context recall evaluation failed: {e}")
            return 0.5

    @staticmethod
    def _safe_average(values: List[float]) -> float:
        """
        Calculate average safely, returning 0 for empty lists.

        Args:
            values: List of float values

        Returns:
            float: Average value
        """
        return sum(values) / len(values) if values else 0.0

    def get_metrics(self) -> Dict[str, float]:
        """
        Get the calculated RAGAS metrics.

        Returns:
            Dict: RAGAS metrics
        """
        return self.metrics

    def get_raw_scores(self) -> Dict[str, List[float]]:
        """
        Get raw per-question scores.

        Returns:
            Dict: Raw scores per metric
        """
        return self.raw_scores


def calculate_ragas_metrics(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[List[str]],
) -> Dict[str, float]:
    """
    Convenience function to calculate RAGAS metrics.

    Args:
        questions: List of questions
        answers: List of generated answers
        contexts: List of retrieved context lists
        ground_truths: List of ground truth lists

    Returns:
        Dict: RAGAS metrics
    """
    evaluator = RAGASEvaluator()
    return evaluator.evaluate(questions, answers, contexts, ground_truths)