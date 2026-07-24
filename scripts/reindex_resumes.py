import json
import logging
from app.services.vector_store import VectorStore
from app.services.resume_service import ResumeService
from app.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reindex_resumes")


def reindex_all_resumes():
    """
    Clears old FAISS vector store index and re-indexes all existing resumes
    stored in SQLite into new chunk-level vectors.
    """
    vector_store = VectorStore()
    resume_service = ResumeService()
    embedding_service = EmbeddingService()

    logger.info("Clearing old FAISS vector store index...")
    vector_store.clear_index()

    resumes = resume_service.list_resumes()
    if not resumes:
        logger.info("No resumes found in SQLite database to re-index.")
        return

    logger.info(f"Found {len(resumes)} resume(s) in SQLite database. Starting re-indexing...")

    indexed_count = 0
    total_chunks_indexed = 0

    for r in resumes:
        resume_id = r["resume_id"]
        candidate_name = r.get("candidate_name") or "Unknown"
        prof_raw = r.get("candidate_profile")
        
        profile_data = None
        if prof_raw:
            try:
                profile_data = json.loads(prof_raw) if isinstance(prof_raw, str) else prof_raw
            except Exception as e:
                logger.warning(f"Could not parse candidate profile JSON for resume {resume_id}: {e}")
                profile_data = None
        
        if not profile_data and r.get("raw_text"):
            profile_data = {"candidate_name": candidate_name, "raw_text": r["raw_text"]}

        if not profile_data:
            logger.warning(f"Skipping resume {resume_id} - no candidate profile or raw text found.")
            continue

        # Generate chunk embeddings
        chunks = embedding_service.generate_resume_chunk_embeddings(profile_data)
        if chunks:
            vector_store.add_resume_chunks(resume_id=resume_id, chunks=chunks)
            indexed_count += 1
            total_chunks_indexed += len(chunks)
            logger.info(f"Indexed resume {resume_id} ({candidate_name}) -> {len(chunks)} chunks.")
        else:
            logger.warning(f"No chunks generated for resume {resume_id}.")

    logger.info(f"Re-indexing complete! Successfully indexed {indexed_count} resume(s) with total {total_chunks_indexed} section chunks into FAISS.")


if __name__ == "__main__":
    reindex_all_resumes()
