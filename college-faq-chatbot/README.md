# 🎓 BVRIT Hyderabad College FAQ Chatbot

A **production-ready RAG (Retrieval-Augmented Generation) chatbot** for BVRIT Hyderabad College of Engineering for Women. Built with LangChain, ChromaDB, OpenRouter, and Streamlit.

## 🚀 Features

- **💬 Intelligent Q&A**: Ask questions about admissions, programs, placements, campus life, and more
- **🔍 RAG Architecture**: Retrieval-Augmented Generation using vector search + LLM
- **📚 Knowledge Base**: Comprehensive college information indexed from official website
- **🎯 Accurate Responses**: Grounded answers with citations, no hallucinations
- **🖼️ Related Images**: Shows relevant images scraped from the official site for matching answers
- **📊 Evaluation Dashboard**: Run tests, view pass rates, RAGAS metrics, and performance charts
- **⚡ Fast & Scalable**: Persistent ChromaDB vector store with embedding caching
- **🌙 Dark/Light Mode**: Toggle between themes
- **📥 Export**: Download chat history and evaluation reports
- **🔗 OpenRouter**: Access GPT-4o-mini and text-embedding-3-small via API

## 🏗️ Project Structure

```
college-faq-chatbot/
├── app.py                  # Streamlit UI application
├── config.py               # Centralized configuration (pydantic-settings)
├── ingest.py               # Document ingestion pipeline
├── rag.py                  # RAG pipeline (retrieve + generate)
├── utils.py                # Utility functions
├── prompts.py              # Prompt management
├── evaluation.py           # Evaluation pipeline + LLM Judge
├── ragas_eval.py           # RAGAS metrics calculation
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── README.md               # This file
├── data/
│   └── college_knowledge.docx  # Knowledge base document
├── prompts/
│   ├── grounding_prompt.txt    # System prompt for RAG
│   ├── generator_prompt.txt    # Generator template
│   └── judge_prompt.txt        # LLM Judge template
├── chroma_db/                  # Persistent vector database
├── tests/
│   └── generated_testcases.json    # Generated evaluation test cases
└── reports/
    ├── evaluation_report.json  # Evaluation results (JSON)
    └── evaluation_report.csv   # Evaluation results (CSV)
```

## 📋 Prerequisites

- **Python 3.12+** (3.14 recommended)
- **OpenRouter API Key** ([Get one here](https://openrouter.ai/keys))
- Internet connection for API calls

## 🔧 Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd college-faq-chatbot
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your_api_key_here
```

### 5. Place the knowledge base document

Place your `college_knowledge.docx` file in the `data/` directory.
_The document is already included if you cloned with the knowledge base._

## 🚀 Running the Application

### Start the Streamlit app

```bash
streamlit run app.py
```

The application will:
1. **Auto-index** the document on first run (loads, chunks, embeds, stores in ChromaDB)
2. **Launch the UI** at `http://localhost:8501`
3. **Reuse the database** on subsequent runs (instant startup)

### Ingest documents manually

```bash
python ingest.py
```

## 💬 Usage

### Ask Questions

Type any question about BVRIT Hyderabad College:

- "What programs does BVRIT offer?"
- "What is the admission process?"
- "What are the placement statistics?"
- "Tell me about the CSE department"
- "How do I apply for hostel?"

### Chat Features

- **Citations**: Every answer cites its source sections
- **Source Viewer**: Expand to see retrieved chunks
- **Token Usage**: Track API consumption
- **Latency**: Response time metrics

## 📊 Evaluation

### Run Full Evaluation

1. Click **"Run Full Evaluation"** on the Evaluation Dashboard tab
2. The system generates 20 test cases across 8 dimensions
3. Each test case runs through the RAG pipeline
4. LLM Judge evaluates responses against expected answers
5. RAGAS metrics (Faithfulness, Relevancy, Precision, Recall) are calculated

### View Results

- Pass/fail rates per dimension
- RAGAS scores with progress bars
- Failed test cases with reasons
- Latency graphs
- Exportable reports (JSON + CSV)

## 🧠 Architecture

### RAG Pipeline

```
Question
    ↓
[Embedding: text-embedding-3-small]
    ↓
[Vector Search: ChromaDB (Top-K=5)]
    ↓
[Retrieved Chunks + Metadata]
    ↓
[Grounding Prompt + Context]
    ↓
[LLM: GPT-4o-mini via OpenRouter]
    ↓
[Answer + Citations]
```

### Chunking Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk Size | 800 | Balances semantic coherence & retrieval granularity |
| Chunk Overlap | 150 | ~19% overlap prevents information loss at boundaries |
| Separators | `\n##, \n###, \n\n, \n, ., , ` | Section-aware splitting |

### Why These Values?

- **800 chars**: Each chunk contains ~1-2 paragraphs of meaningful content, enough for the LLM to understand context without exceeding token limits
- **150 overlap**: Ensures continuity between chunks; key information near boundaries isn't lost
- **Section-aware**: Respects document structure, keeping related content together

## 🔑 Configuration

All configuration is in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | - | Your OpenRouter API key |
| `LLM_MODEL` | `gpt-4o-mini` | Model for answer generation |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Model for embeddings |
| `CHUNK_SIZE` | 800 | Characters per chunk |
| `CHUNK_OVERLAP` | 150 | Overlap between chunks |
| `TOP_K` | 5 | Number of chunks to retrieve |
| `CHROMA_DB_DIR` | `chroma_db` | Vector database directory |
| `IMAGE_INDEX_PATH` | `data/bvrit_image_index.json` | Scraped image index for related answer images |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | GPT-4o-mini (via OpenRouter) |
| **Embeddings** | text-embedding-3-small (via OpenRouter) |
| **Vector Store** | ChromaDB (persistent) |
| **Framework** | LangChain |
| **UI** | Streamlit |
| **Visualization** | Plotly |
| **Evaluation** | RAGAS, LLM Judge |

## 📈 RAGAS Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Faithfulness** | How factually accurate the answer is given the context | > 0.85 |
| **Answer Relevancy** | How relevant the answer is to the question | > 0.80 |
| **Context Precision** | How precise the retrieved context is | > 0.75 |
| **Context Recall** | How much relevant context was retrieved | > 0.70 |

## 📝 Future Improvements

- [ ] Multi-document support
- [ ] Conversational memory (chat history)
- [ ] Feedback loop for continuous improvement
- [ ] Admin dashboard for monitoring
- [ ] API endpoint for external integrations
- [ ] Support for additional file formats (PDF, HTML)
- [ ] Hybrid search (vector + keyword)
- [ ] User authentication

## 📄 License

This project is created for academic purposes at BVRIT Hyderabad College of Engineering for Women.

---

Built with ❤️ using LangChain, ChromaDB, OpenRouter & Streamlit