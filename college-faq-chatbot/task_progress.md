# Task Progress: College FAQ Chatbot - Use BVRITH_Knowledge_Base.md as RAG Source

- [x] Analyze existing project structure
- [x] Understand knowledge base format (JSON array in .md file)
- [ ] Update `.env` to point to `data/BVRITH_Knowledge_Base.md`
- [ ] Update `config.py` default document path to `.md` file
- [ ] Add `load_json_knowledge_base()` to `utils.py`
- [ ] Update `ingest.py` to handle structured JSON knowledge base
- [ ] Clear old ChromaDB for fresh re-ingestion
- [ ] Verify ingestion works end-to-end
- [ ] Run the app to confirm chatbot functionality