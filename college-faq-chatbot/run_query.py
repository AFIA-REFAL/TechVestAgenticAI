"""
Run a quick query against the ingested knowledge base and print top-k retrieved chunks.
"""
from ingest import run_ingestion
from utils import get_llm_client
from config import settings
from simple_vectorstore import SimpleVectorStore


def pretty_print_docs(docs):
    for i, d in enumerate(docs, 1):
        meta = d.metadata if hasattr(d, 'metadata') else {}
        text = d.page_content if hasattr(d, 'page_content') else meta.get('text','')
        print(f"--- Result {i} ---")
        print(f"Score/metadata keys: {list(meta.keys())}")
        print(text[:800].strip())
        print()


if __name__ == '__main__':
    ingestor = run_ingestion()
    retriever = ingestor.get_retriever()

    queries = [
        "What are the admission criteria for BVRIT Hyderabad?",
        "How can I contact the college administration?",
        "List the undergraduate programs offered at BVRIT Hyderabad.",
    ]

    for q in queries:
        print('\n' + '='*60)
        print('Query:', q)
        print('='*60)

        vs = ingestor.vector_store
        docs = []

        # If using our SimpleVectorStore
        if isinstance(vs, SimpleVectorStore):
            results = vs.similarity_search(q, embedding_client=ingestor.embeddings, k=settings.top_k)
            # Map to LangchainDocument-like objects
            from langchain_core.documents import Document as LangchainDocument
            for r in results:
                md = r.get('metadata', {})
                text = md.get('text', '')
                docs.append(LangchainDocument(page_content=text, metadata=md))
        # If using a Chroma/VectorStore instance with similarity_search
        elif hasattr(vs, 'similarity_search'):
            try:
                docs = vs.similarity_search(q, k=settings.top_k)
            except TypeError:
                # Some versions accept different params
                docs = vs.similarity_search(q, k=settings.top_k)

        if not docs:
            print('No documents retrieved for this query.')
            continue

        pretty_print_docs(docs)

    print('Done')
