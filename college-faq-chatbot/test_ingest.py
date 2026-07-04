import sys
sys.path.insert(0, '.')
try:
    from ingest import run_ingestion
    print('Starting ingestion test...')
    ingestor = run_ingestion()
    print('Ingestion OK, collection stats:')
    print(ingestor.get_collection_stats())
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))
    import traceback
    traceback.print_exc()
