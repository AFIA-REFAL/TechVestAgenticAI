"""
TechVest Recruitment Agent — LangChain Tools
=============================================
Four typed tools backed by Pydantic models and OpenRouter LLM calls.
"""

import os
import json
import re
from typing import Annotated

from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# ──────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────

class Project(BaseModel):
    name: str = Field(description="Name of the project")
    description: str = Field(description="Brief description of what was built")
    line_ref: str = Field(
        description="Excerpt or line from the resume describing this project"
    )


class CandidateProfile(BaseModel):
    name: str = Field(description="Full name of the candidate")
    years_experience: float = Field(description="Total years of professional experience")
    skills: list[str] = Field(description="List of technical skills mentioned")
    education: str = Field(description="Highest degree and institution")
    projects: list[Project] = Field(description="List of relevant projects with descriptions")


class CriterionScore(BaseModel):
    name: str = Field(description="Name of the rubric criterion")
    score: int = Field(description="Score 0–5 for this criterion", ge=0, le=5)
    evidence: str = Field(
        description="Direct citation from the candidate's profile supporting this score"
    )


class ScoreCard(BaseModel):
    scores: list[CriterionScore] = Field(description="Scores for each rubric criterion")
    weighted_total: float = Field(
        description="Weighted total score computed as sum(score * weight) across all criteria"
    )


# ──────────────────────────────────────────────
# LLM Client (OpenRouter)
# ──────────────────────────────────────────────

def _get_llm(
    model: str = "openai/gpt-4o-mini",
    temperature: float = 0.0,
) -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Please set it before running the recruitment pipeline."
        )
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )


def _has_openrouter_key() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _section_lines(resume_text: str, heading: str) -> list[str]:
    lines = resume_text.splitlines()
    capture = False
    section: list[str] = []
    heading = heading.strip().upper()

    for line in lines:
        stripped = line.strip()
        if stripped.upper() == heading:
            capture = True
            continue
        if capture:
            if stripped and stripped == stripped.upper() and len(stripped) <= 40 and not stripped.startswith("-"):
                break
            if stripped and set(stripped) <= {"-"}:
                continue
            section.append(line)

    return section


def _fallback_extract_name(resume_text: str) -> str:
    match = re.search(r"(?im)^\s*Name:\s*(.+?)\s*$", resume_text)
    if match:
        return match.group(1).strip()
    first_line = next((line.strip() for line in resume_text.splitlines() if line.strip()), "")
    return first_line or "Unknown Candidate"


def _fallback_extract_years_experience(resume_text: str) -> float:
    experience_lines = re.findall(
        r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\s*[–-]\s*(?:present|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})",
        resume_text,
    )
    if not experience_lines:
        return 1.5
    return round(min(5.0, 0.9 * len(experience_lines) + 1.0), 1)


def _fallback_extract_skills(resume_text: str) -> list[str]:
    skill_catalog = [
        "Python", "PyTorch", "TensorFlow", "LangChain", "LangGraph",
        "FastAPI", "Streamlit", "ChromaDB", "Pinecone", "Weaviate",
        "Qdrant", "Docker", "Git", "GitHub Actions", "RAGAS",
        "Hugging Face", "Transformers", "PEFT", "SQL", "Java",
        "Spring Boot", "Flask", "scikit-learn", "Pandas", "NumPy",
        "Matplotlib", "OpenAI", "Anthropic", "Ollama", "Kafka",
        "Elasticsearch", "VBA", "Excel", "JIRA", "Linux",
    ]
    lower_text = resume_text.lower()
    return [skill for skill in skill_catalog if skill.lower() in lower_text]


def _fallback_extract_education(resume_text: str) -> str:
    section = _section_lines(resume_text, "EDUCATION")
    lines = [line.strip(" -\t") for line in section if line.strip()]
    return lines[0] if lines else "Education not clearly stated"


def _fallback_extract_projects(resume_text: str) -> list[Project]:
    section = _section_lines(resume_text, "PROJECTS")
    projects: list[Project] = []
    current_name: str | None = None
    current_details: list[str] = []

    def flush_project() -> None:
        nonlocal current_name, current_details
        if current_name:
            evidence = next((line.strip(" -\t") for line in current_details if line.strip()), current_name)
            description = " ".join(line.strip(" -\t") for line in current_details[:2] if line.strip()) or current_name
            projects.append(Project(name=current_name, description=description, line_ref=evidence))
        current_name = None
        current_details = []

    for raw_line in section:
        line = raw_line.strip()
        if not line:
            continue
        if "|" in line and not line.startswith("-"):
            flush_project()
            current_name = line.split("|")[0].strip()
            continue
        if current_name:
            current_details.append(line)

    flush_project()
    return projects


def _fallback_parse_resume(resume_text: str) -> CandidateProfile:
    return CandidateProfile(
        name=_fallback_extract_name(resume_text),
        years_experience=_fallback_extract_years_experience(resume_text),
        skills=_fallback_extract_skills(resume_text),
        education=_fallback_extract_education(resume_text),
        projects=_fallback_extract_projects(resume_text),
    )


def _criterion_map(rubric: dict) -> dict[str, dict]:
    return {criterion.get("name", ""): criterion for criterion in rubric.get("criteria", [])}


def _fallback_score_candidate(profile: CandidateProfile, rubric: dict) -> ScoreCard:
    criteria = _criterion_map(rubric)
    profile_dump = profile.model_dump()
    profile_text = json.dumps(profile_dump, indent=2).lower()
    skills_lower = {skill.lower() for skill in profile.skills}
    project_text = " ".join(
        f"{project.name} {project.description} {project.line_ref}".lower()
        for project in profile.projects
    )

    def score_criterion(name: str, score: int, evidence: str) -> CriterionScore:
        return CriterionScore(name=name, score=max(0, min(5, score)), evidence=evidence)

    scores: list[CriterionScore] = []

    python_ml_score = 0
    if "python" in skills_lower:
        python_ml_score += 1
    if any(skill in skills_lower for skill in {"pytorch", "tensorflow", "scikit-learn", "numpy", "pandas"}):
        python_ml_score += 1
    if any(term in profile_text for term in ["rag", "fine-tune", "classification", "evaluation", "ml"]):
        python_ml_score += 1
    if profile.years_experience >= 2.5:
        python_ml_score += 1
    if any(term in profile_text for term in ["published", "contributed", "blog", "experiments"]):
        python_ml_score += 1
    scores.append(
        score_criterion(
            "Python & ML Fundamentals",
            python_ml_score,
            next(
                (
                    evidence
                    for evidence in [
                        "Python listed as a skill" if "python" in skills_lower else "Python not explicitly listed",
                        "Deep-learning / ML tooling present" if any(skill in skills_lower for skill in {"pytorch", "tensorflow", "scikit-learn"}) else "No deep-learning framework listed",
                        profile.projects[0].line_ref if profile.projects else profile.education,
                    ]
                    if evidence
                ),
                profile.education,
            ),
        )
    )

    project_score = 0
    if profile.projects:
        project_score += 1
    if len(profile.projects) >= 2:
        project_score += 1
    if any(term in project_text for term in ["api", "dashboard", "deployed", "streamlit", "fastapi", "github"]):
        project_score += 1
    if any(term in profile_text for term in ["ci", "testing", "documentation", "blog", "open-source", "users"]):
        project_score += 1
    if any(term in project_text for term in ["real-world", "dataset", "fine-tuned", "end-to-end", "rag"]):
        project_score += 1
    scores.append(
        score_criterion(
            "Relevant Projects",
            project_score,
            profile.projects[0].line_ref if profile.projects else profile.education,
        )
    )

    tooling_score = 0
    if any(term in skills_lower for term in {"langchain", "langgraph"}):
        tooling_score += 1
    if any(term in skills_lower for term in {"chromadb", "pinecone", "weaviate", "qdrant"}):
        tooling_score += 1
    if any(term in skills_lower for term in {"docker", "git", "github actions"}):
        tooling_score += 1
    if any(term in profile_text for term in ["openai", "anthropic", "ollama", "hugging face"]):
        tooling_score += 1
    if any(term in profile_text for term in ["pipeline", "workflow", "production", "ci"]):
        tooling_score += 1
    scores.append(
        score_criterion(
            "Hands-on Tooling",
            tooling_score,
            next(
                (
                    evidence
                    for evidence in [
                        "LangChain / LangGraph usage" if any(term in skills_lower for term in {"langchain", "langgraph"}) else "No LangChain/LangGraph evidence",
                        "Docker / Git / CI usage" if any(term in skills_lower for term in {"docker", "git", "github actions"}) else "No Docker/Git evidence",
                    ]
                    if evidence
                ),
                profile.education,
            ),
        )
    )

    communication_score = 0
    if any(term in profile_text for term in ["blog", "readme", "documentation", "runbooks", "technical writing"]):
        communication_score += 1
    if any(term in profile_text for term in ["collaboration", "cross-team", "mentoring", "stakeholders"]):
        communication_score += 1
    if len(profile.projects) >= 2:
        communication_score += 1
    if any(term in profile_text for term in ["published", "reads", "github"]):
        communication_score += 1
    if profile.years_experience >= 3:
        communication_score += 1
    scores.append(
        score_criterion(
            "Communication Skills",
            communication_score,
            profile.projects[0].line_ref if profile.projects else profile.education,
        )
    )

    weighted_total = 0.0
    for score in scores:
        weight = float(criteria.get(score.name, {}).get("weight", 0.0))
        weighted_total += score.score * weight

    return ScoreCard(scores=scores, weighted_total=round(weighted_total, 4))


# ──────────────────────────────────────────────
# Tool 1 — parse_resume
# ──────────────────────────────────────────────

@tool
def parse_resume(resume_text: str) -> CandidateProfile:
    """
    Parse a plain-text resume into a structured CandidateProfile.

    Args:
        resume_text: The full plain-text content of a candidate's resume.

    Returns:
        A CandidateProfile with name, years_experience, skills, education,
        and projects (each with a name, description, and line_ref excerpt).
    """
    if not _has_openrouter_key():
        return _fallback_parse_resume(resume_text)

    llm = _get_llm().with_structured_output(CandidateProfile)

    prompt = (
        "You are an expert HR data extractor. Given a candidate's resume "
        "in plain text, extract the following structured fields:\n\n"
        "- **name**: Full name of the candidate.\n"
        "- **years_experience**: Total years of professional work "
        "experience (float). Sum up internships and full-time roles.\n"
        "- **skills**: A list of all technical skills explicitly mentioned "
        "(languages, frameworks, tools, libraries).\n"
        "- **education**: Highest degree, institution, and graduation "
        "year.\n"
        "- **projects**: A list of projects. For each project provide:\n"
        "    - name: Project title.\n"
        "    - description: 1–2 sentence summary of what was built.\n"
        "    - line_ref: A short direct quote from the resume that "
        "describes this project.\n\n"
        "Resume text:\n---\n" + resume_text + "\n---\n"
    )

    try:
        result = llm.invoke(prompt)
        return result
    except Exception:
        return _fallback_parse_resume(resume_text)


# ──────────────────────────────────────────────
# Tool 2 — score_candidate
# ──────────────────────────────────────────────

@tool
def score_candidate(
    profile: Annotated[CandidateProfile, "Structured profile from parse_resume"],
    rubric: Annotated[dict, "Rubric dict with 'criteria' list and 'notes' string"],
) -> ScoreCard:
    """
    Score a candidate profile against the job rubric.

    For each criterion in the rubric, the LLM assigns a 0–5 score
    (using the level descriptors) and provides a mandatory evidence
    string cited directly from the profile. The weighted total is
    computed as sum(score * weight) across all criteria.

    Args:
        profile: The CandidateProfile to evaluate.
        rubric: The scoring rubric containing criteria with weights
                and level descriptors.

    Returns:
        A ScoreCard with per-criterion scores + evidence and a
        computed weighted_total.
    """
    if not _has_openrouter_key():
        return _fallback_score_candidate(profile, rubric)

    llm = _get_llm().with_structured_output(ScoreCard)

    profile_json = profile.model_dump_json(indent=2)
    rubric_json = json.dumps(rubric, indent=2)

    prompt = (
        "You are a strict recruitment evaluator. You have been given a "
        "candidate's structured profile and a scoring rubric.\n\n"
        "For **each criterion** in the rubric, you MUST:\n"
        "1. Read the criterion name, weight, description, and 0–5 level "
        "descriptors.\n"
        "2. Assign a score (0–5) based on the candidate's profile.\n"
        "3. Provide an 'evidence' string that quotes a **specific** "
        "project, skill, or experience from the profile. Vague evidence "
        "is not acceptable.\n\n"
        "IMPORTANT: Every score MUST be accompanied by a direct citation "
        "from the candidate's profile. The citation should reference "
        "concrete details (e.g. \"built a RAG pipeline using LangChain\" "
        "or \"Python listed as advanced skill\").\n\n"
        "After scoring all criteria, compute the **weighted_total** as:\n"
        "    sum(criterion.score * criterion.weight) for all criteria\n\n"
        "Candidate Profile:\n---\n" + profile_json + "\n---\n\n"
        "Rubric:\n---\n" + rubric_json + "\n---\n"
        "Rubric notes: " + rubric.get("notes", "") + "\n---\n"
    )

    try:
        result = llm.invoke(prompt)
        return result
    except Exception:
        return _fallback_score_candidate(profile, rubric)


# ──────────────────────────────────────────────
# Tool 3 — check_availability (mock, no LLM)
# ──────────────────────────────────────────────

@tool
def check_availability(
    candidate_name: Annotated[str, "Full name of the candidate"],
    week: Annotated[str, "Week identifier e.g. '2026-07-13' or 'next week'"],
) -> list[str]:
    """
    Check interview slot availability for a candidate in a given week.

    This is a mock tool — it returns hardcoded time slots.

    Args:
        candidate_name: Name of the candidate to schedule.
        week: Week identifier (e.g. "2026-07-13" or "next week").

    Returns:
        A list of available interview slot strings.
    """
    slots = [
        f"{candidate_name} — {week} — Mon 10:00–11:00 IST",
        f"{candidate_name} — {week} — Wed 14:00–15:00 IST",
        f"{candidate_name} — {week} — Fri 16:00–17:00 IST",
    ]
    return slots


# ──────────────────────────────────────────────
# Tool 4 — propose_interview (write tool, no auto-confirm)
# ──────────────────────────────────────────────

@tool
def propose_interview(
    candidate_name: Annotated[str, "Full name of the candidate"],
    slot: Annotated[str, "Selected interview slot string from check_availability"],
) -> dict:
    """
    Propose an interview slot for a candidate.

    This is a write tool that creates a proposal requiring human approval.
    It does NOT auto-confirm the interview.

    Args:
        candidate_name: Name of the candidate.
        slot: The chosen interview slot string.

    Returns:
        A confirmation dict with status "pending_human_approval" and
        proposal details.
    """
    return {
        "candidate_name": candidate_name,
        "proposed_slot": slot,
        "status": "pending_human_approval",
        "message": (
            f"Interview proposal for {candidate_name} at {slot} has been "
            "submitted. A human reviewer must approve before the slot is "
            "confirmed."
        ),
    }


# ──────────────────────────────────────────────
# __main__ — Test each tool once
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import traceback

    # Import data constants from sibling file
    sys.path.insert(0, os.path.dirname(__file__) or ".")
    from data import RESUMES, RUBRIC

    print("=" * 72)
    print("TechVest Recruitment Tools — Smoke Test")
    print("=" * 72)

    # ---- Test parse_resume with Priya's resume ----
    print("\n>> Tool 1: parse_resume (Priya)")
    try:
        profile = parse_resume.invoke({"resume_text": RESUMES["Priya"]})
        print(f"  Name:              {profile.name}")
        print(f"  Years Experience:  {profile.years_experience}")
        print(f"  Skills:            {', '.join(profile.skills[:6])}...")
        print(f"  Education:         {profile.education}")
        print(f"  Projects:          {len(profile.projects)} extracted")
        for p in profile.projects:
            print(f"    - {p.name}: {p.description[:80]}...")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()

    # ---- Test score_candidate with Priya's profile ----
    print("\n>> Tool 2: score_candidate (Priya)")
    try:
        scorecard = score_candidate.invoke({
            "profile": profile,
            "rubric": RUBRIC,
        })
        print(f"  Weighted Total:  {scorecard.weighted_total:.2f} / 5.00")
        for cs in scorecard.scores:
            print(f"    {cs.name}: {cs.score}/5 — evidence: {cs.evidence[:60]}...")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()

    # ---- Test check_availability ----
    print("\n>> Tool 3: check_availability (Priya)")
    try:
        slots = check_availability.invoke({
            "candidate_name": "Priya Mehta",
            "week": "2026-07-20",
        })
        for s in slots:
            print(f"  - {s}")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()

    # ---- Test propose_interview ----
    print("\n>> Tool 4: propose_interview (Priya)")
    try:
        result = propose_interview.invoke({
            "candidate_name": "Priya Mehta",
            "slot": slots[0],
        })
        print(f"  Status:         {result['status']}")
        print(f"  Proposed Slot:  {result['proposed_slot']}")
        print(f"  Message:        {result['message']}")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()

    print("\n" + "=" * 72)
    print("Smoke test complete.")
    print("=" * 72)