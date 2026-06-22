# Product Specification — AI Quiz Generator

**Version:** 2.0  
**Date:** June 2026  
**Author:** AFIA-REFAL  
**Project:** TechVest Agentic AI — Academic Year 2025–26  
**Status:** Implemented

---

## 1. Purpose and Background

### 1.1 Problem Statement

Students and educators who use digital documents — PowerPoint slides, PDF handouts, Word notes, or plain text — as their primary study materials have no fast, automated way to convert that content into assessment material. Creating MCQs manually is time-consuming, often misses key concepts, and produces questions of inconsistent quality and difficulty.

### 1.2 Solution

AI Quiz Generator is a single-page web application that accepts any supported document and uses a large language model to automatically extract key concepts and generate high-quality MCQs. Users can configure difficulty and question count, take an interactive quiz, and receive AI-powered feedback explaining their mistakes.

### 1.3 Goals

| Goal | Success Metric |
|---|---|
| Support multiple document formats | Accept .pptx, .pdf, .docx, and .txt without errors |
| Automate MCQ generation from document content | Questions generated in < 30 seconds for a typical document |
| Support multiple difficulty levels | 3 distinct tiers with measurably different question types |
| Deliver interactive quiz experience | One-question-per-screen, timer, progress bar |
| Provide learning feedback | AI explanation generated for every wrong answer |
| Professional, intuitive UI | No user documentation required to operate the app |

---

## 2. Scope

### 2.1 In Scope

- Upload and parse `.pptx`, `.pdf`, `.docx`, and `.txt` files (up to 25 MB)
- AI-generated multiple-choice questions (4 options, single correct answer)
- Three difficulty modes: Simple, Medium, Complex
- Configurable question count: 5 to 30
- Interactive quiz with navigation (Next / Back)
- Live elapsed timer during quiz
- Results screen: score, per-question review, AI explanations for wrong answers
- Session analytics: quizzes taken, average score, best score, total questions
- Quiz history log for the current session
- Settings page showing current configuration

### 2.2 Out of Scope

- User authentication and persistent accounts
- Cloud storage of quiz history across sessions
- Support for image-based PDFs or scanned documents (no OCR)
- Multi-language support
- Manual question editing before quiz start
- Sharing or exporting quizzes

---

## 3. Users and Personas

### 3.1 Primary User — Student

- Uploads lecture slides, PDF handouts, or Word notes before an exam
- Wants to test their knowledge quickly with varied difficulty
- Values immediate, clear feedback on what they got wrong and why

### 3.2 Secondary User — Educator / Instructor

- Uses the tool to preview what questions an AI generates from their material
- May use it to verify coverage of key concepts across any document format
- Values the accuracy and relevance of generated questions

---

## 4. Functional Requirements

### 4.1 File Upload (FR-01)

| ID | Requirement |
|---|---|
| FR-01-01 | The system SHALL accept `.pptx`, `.pdf`, `.docx`, and `.txt` files via drag-and-drop or file browser |
| FR-01-02 | The system SHALL reject files larger than 25 MB with a clear error message |
| FR-01-03 | The system SHALL reject file types not in the supported list |
| FR-01-04 | The system SHALL display a section/page count and word count after successful parsing |
| FR-01-05 | The system SHALL show a format-appropriate icon for the uploaded file type |
| FR-01-06 | The system SHALL display an animated AI processing screen during extraction with format-specific stage labels |

### 4.2 Document Parsing (FR-02)

| ID | Requirement |
|---|---|
| FR-02-01 | `.pptx` files SHALL be parsed using `python-pptx`; each slide becomes one content section |
| FR-02-02 | `.pdf` files SHALL be parsed using `pypdf`; each page becomes one content section |
| FR-02-03 | `.docx` files SHALL be parsed using `python-docx`; paragraphs SHALL be grouped into sections of ~12 paragraphs |
| FR-02-04 | `.txt` files SHALL be decoded as UTF-8 and split into chunks of ~250 words |
| FR-02-05 | Sections with no extractable text SHALL be silently skipped |

### 4.3 Quiz Configuration (FR-03)

| ID | Requirement |
|---|---|
| FR-03-01 | The system SHALL allow users to select between 5 and 30 questions via a slider |
| FR-03-02 | The system SHALL offer three difficulty levels: Simple, Medium, Complex |
| FR-03-03 | The system SHALL display a hint description for the selected difficulty |
| FR-03-04 | The system SHALL display the source filename and content stats on the config screen |

### 4.4 Question Generation (FR-04)

| ID | Requirement |
|---|---|
| FR-04-01 | The system SHALL generate exactly the requested number of MCQs |
| FR-04-02 | Each question SHALL have exactly 4 options (A, B, C, D) with one correct answer |
| FR-04-03 | Questions SHALL be tagged with a topic label derived from the content |
| FR-04-04 | The system SHALL apply difficulty-specific prompt instructions to the AI |
| FR-04-05 | The system SHALL display a loading spinner during generation |

### 4.5 Quiz Interaction (FR-05)

| ID | Requirement |
|---|---|
| FR-05-01 | The system SHALL display one question per screen |
| FR-05-02 | The system SHALL highlight the selected option visually |
| FR-05-03 | The system SHALL allow forward and backward navigation between questions |
| FR-05-04 | The system SHALL display a progress bar showing completion percentage |
| FR-05-05 | The system SHALL display an elapsed timer in MM:SS format |
| FR-05-06 | The system SHALL show a topic label above each question |

### 4.6 Results (FR-06)

| ID | Requirement |
|---|---|
| FR-06-01 | The system SHALL display the total score as correct/total and as a percentage |
| FR-06-02 | The system SHALL display an encouraging performance message based on score range |
| FR-06-03 | The system SHALL list every question with the user's answer and the correct answer |
| FR-06-04 | The system SHALL generate a 1–2 sentence AI explanation for each wrong answer |
| FR-06-05 | The system SHALL allow the user to retake the same quiz or upload a new document |

### 4.7 Navigation Pages (FR-07)

| ID | Requirement |
|---|---|
| FR-07-01 | A left icon dock SHALL provide navigation to Home, Analytics, History, Settings |
| FR-07-02 | The Analytics page SHALL show: quizzes taken, avg score, best score, total questions |
| FR-07-03 | The History page SHALL list all completed quiz sessions with filename, format, difficulty, score |
| FR-07-04 | The Settings page SHALL display current AI model, provider, supported file types, and limits |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement |
|---|---|
| NFR-01-01 | Question generation SHALL complete within 30 seconds for a typical document |
| NFR-01-02 | File parsing SHALL complete within 5 seconds for a 25 MB file |
| NFR-01-03 | Page transitions SHALL be instantaneous (< 200 ms) |

### 5.2 Security

| ID | Requirement |
|---|---|
| NFR-02-01 | The API key SHALL never be embedded in source code |
| NFR-02-02 | The API key SHALL be loaded from a `.env` file excluded from version control |
| NFR-02-03 | No user data SHALL be stored outside of in-memory session state |

### 5.3 Usability

| ID | Requirement |
|---|---|
| NFR-03-01 | The application SHALL be usable without any documentation |
| NFR-03-02 | All interactive elements SHALL provide clear visual feedback on interaction |
| NFR-03-03 | Error messages SHALL be descriptive and actionable |
| NFR-03-04 | The upload zone SHALL clearly communicate all accepted file types |

### 5.4 Compatibility

| ID | Requirement |
|---|---|
| NFR-04-01 | The application SHALL run on Python 3.10+ on Windows, macOS, and Linux |
| NFR-04-02 | The UI SHALL render correctly in modern Chromium-based browsers |

---

## 6. User Flows

### 6.1 Happy Path

```
Start → Upload document (.pptx/.pdf/.docx/.txt)
→ [AI extracts content] → Set questions + difficulty
→ [AI generates MCQs] → Answer Q1…Qn → Submit
→ View score + explanations
```

### 6.2 Upload Error Flow

```
Upload file → File > 25 MB OR unsupported type OR no extractable text
→ Error message shown → User uploads a different file
```

### 6.3 Generation Error Flow

```
Generate Questions → API error or malformed JSON
→ Error message shown → User clicks Retry
```

---

## 7. Constraints

- The application requires an active internet connection to call the OpenRouter API.
- Image-based PDFs (scanned documents without embedded text) will yield no extractable content — OCR is not supported.
- Password-protected PDF and DOCX files are not supported.
- Session history is lost when the browser tab is closed or the server restarts.
- The AI model may occasionally return malformed JSON; the app handles this with a retry prompt.

---

## 8. Acceptance Criteria

1. A `.pptx`, `.pdf`, `.docx`, and `.txt` file each produce the requested number of well-formed MCQs.
2. Selecting a difficulty level produces noticeably different question types.
3. Selecting an answer highlights it and does not show the answer twice.
4. The results screen shows the correct answer for every wrong response.
5. AI explanations are displayed for every incorrectly answered question.
6. The History page shows an entry after completing a quiz, including the file format.
7. The Analytics page updates averages correctly after multiple quizzes across different formats.
8. The Settings page displays `.pptx .pdf .docx .txt` as supported file types.
