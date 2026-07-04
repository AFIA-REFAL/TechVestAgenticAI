# Task: Fix Conversation History / Coreference Resolution

- [x] Analyze current codebase (app.py, rag.py, prompts)
- [ ] Fix `rag.py`: Remove truncation of chat_history (change from last 4 to full history)
- [ ] Update `grounding_prompt.txt`: Add explicit instructions about prior conversation context
- [ ] Create test script to run the 5-turn test
- [ ] Run the 5-turn test and record responses
- [ ] Verify all pass criteria met