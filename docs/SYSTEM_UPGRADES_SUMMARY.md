# 🚀 Comprehensive System Upgrades & Architecture Documentation

This document provides an exhaustive, end-to-end technical breakdown of all system enhancements, algorithmic upgrades, multi-stage retrieval optimizations, and evaluation benchmarks implemented in the **Agentic Hiring Workflow** platform.

---

## 📋 Table of Contents
1. [Executive Summary](#-executive-summary)
2. [1. Section-Level Resume Chunking & MaxSim Storage](#1-section-level-resume-chunking--maxsim-storage)
3. [2. Automated Vector Re-Indexing Utility](#2-automated-vector-re-indexing-utility)
4. [3. Multi-File Batch Resume Ingestion Fix](#3-multi-file-batch-resume-ingestion-fix)
5. [4. Hard Metadata Pre-Filtering Pipeline](#4-hard-metadata-pre-filtering-pipeline)
6. [5. 12-Layer Cross-Encoder Upgrade & Chunk-Aware Reranking](#5-12-layer-cross-encoder-upgrade--chunk-aware-reranking)
7. [6. Automated RAG Evaluation Suite (Precision@K, MRR & Faithfulness)](#6-automated-rag-evaluation-suite-precisionk-mrr--faithfulness)
8. [💻 CLI Commands Cheat Sheet](#-cli-commands-cheat-sheet)

---

## 🌟 Executive Summary

Through these upgrades, the platform transitioned from a basic 1-vector global resume retrieval pipeline to an enterprise-grade, **chunk-aware, multi-stage hybrid RAG hiring engine**.

Key achievements:
- **Retrieval Precision Boost**: Context dilution and 512-token truncation eliminated via section-level chunking.
- **Deeper Re-Ranking**: Upgraded to 12-layer Cross-Encoder (`ms-marco-MiniLM-L-12-v2`) with exact section chunk context injection.
- **Hard Constraints Enforcement**: Hard metadata filtering for Years of Experience and Minimum Education Degree tiers before vector scoring.
- **Automated Benchmarking**: Built a complete RAG evaluation suite evaluating `Precision@K`, `Hit Rate@K`, `MRR`, and LLM Faithfulness scores.

---

## 1. Section-Level Resume Chunking & MaxSim Storage

### Core Problem Solved
Previously, the entire resume was concatenated into a single long string and encoded into **1 single vector** per candidate. Because embedding models (such as `BAAI/bge-base-en-v1.5`) have a 512-token window limit, key project details or work experience buried deep in long resumes were truncated or diluted.

### Technical Implementation
- **`app/services/embedding_service.py`**:
  - Implemented `build_resume_chunks(profile)`: Automatically extracts discrete logical section chunks from candidate profiles:
    - **Summary**: Name & Professional Summary
    - **Skills**: Technical & Soft Skills
    - **Experience\_i**: 1 chunk per work experience entry (`Role: designation at company` + `responsibilities`)
    - **Project\_i**: 1 chunk per project entry (`Project Title`, `description`, `technologies`)
    - **Education**: Degrees, specializations, and institutes
    - **Certifications**: Certification names and issuers
  - Implemented `generate_resume_chunk_embeddings(profile)`: Encodes each section chunk into a 768-dimensional dense vector.

- **`app/services/vector_store.py`**:
  - Added `add_resume_chunks(resume_id, chunks)`: Stores multiple vectors per candidate in FAISS while recording metadata mapping in `resume_mapping.json`:
    ```json
    {
      "id": "resume_id",
      "resume_id": "resume_id",
      "chunk_type": "experience_1",
      "chunk_text": "Role: Senior AI Engineer at Fxis.ai..."
    }
    ```
  - Updated `search()` with **MaxSim (Maximum Chunk Similarity)**: Aggregates multiple chunk hits per candidate, retaining the highest matching section score, type, and text.
  - Updated `delete_resume()`: Purges all chunk vectors belonging to a candidate upon deletion.

---

## 2. Automated Vector Re-Indexing Utility

### Technical Implementation
- **`scripts/reindex_resumes.py`**:
  Created a standalone CLI utility script that:
  1. Clears existing FAISS index & mapping file (`vector_store.clear_index()`).
  2. Reads all candidate profiles stored in SQLite (`hiring.db`).
  3. Re-generates 768-dim section chunk vectors for every candidate.
  4. Re-populates FAISS and `resume_mapping.json` automatically without needing manual PDF re-upload.

---

## 3. Multi-File Batch Resume Ingestion Fix

### Core Problem Solved
When recruiters uploaded multiple resume files simultaneously in the Streamlit **Resume Pool** page, `st.rerun()` was being called inside the file processing loop after the first file finished, terminating the loop prematurely and skipping the remaining files.

### Technical Implementation
- **`streamlit_app.py`**:
  - Moved `st.rerun()` to execute **only after** all uploaded files in the batch complete.
  - Added a live batch progress bar `(1/N ... N/N)` and real-time status message.
  - Added toast notifications (`✅ Added file_name to pool`) per completed upload.

---

## 4. Hard Metadata Pre-Filtering Pipeline

### Core Problem Solved
Recruiters frequently have non-negotiable hard constraints (e.g. minimum 3 years of experience or a Master's degree). Pure semantic search could rank an entry-level candidate high due to keyword similarity despite failing hard job requirements.

### Technical Implementation
- **`app/schemas/candidate_profile.py`**:
  - Added `get_parsed_experience_years()`: Extracts numeric total experience years from parsed profiles.
  - Added `get_education_tier()`: Classifies candidate education level into standardized tiers:
    - **Tier 0**: None / Unknown
    - **Tier 1**: Diploma / High School
    - **Tier 2**: Bachelor's (B.Tech, BE, BS, BA, B.Sc)
    - **Tier 3**: Master's (M.Tech, ME, MS, MA, M.Sc, MBA)
    - **Tier 4**: Doctorate / PhD

- **`app/services/hybrid_search.py`**:
  - Pre-filters candidate pool against active hard constraints (`min_experience_years` and `required_degree`) *before* executing BM25 lexical tokenization and FAISS vector similarity search.

- **`app/graph/retrieval_state.py` & `app/api/routes/retrieval.py`**:
  - Restored `top_k: int = 5` and added `filters: Optional[dict] = None`.
  - Updated `POST /retrieval/{job_id}` endpoint to accept filter criteria in JSON payload.

- **`streamlit_app.py`**:
  - Added interactive **🎚️ Hard Constraint Filters** (Min Experience input & Min Education Level dropdown) on the **🎯 Candidate Fetch** page.

---

## 5. 12-Layer Cross-Encoder Upgrade & Chunk-Aware Reranking

### Technical Implementation
- **`app/services/reranker_service.py`**:
  - Upgraded model from `cross-encoder/ms-marco-MiniLM-L-6-v2` (6 layers) to **`cross-encoder/ms-marco-MiniLM-L-12-v2`** (12 transformer layers, 2x depth for superior cross-attention reasoning).
  - Updated `_build_resume_text()` to format candidate text with **Chunk-Aware Context**, passing the candidate's exact top-matching section chunk (`matched_chunk_text`) along with Summary & Skills:
    ```text
    Summary: Experienced AI Engineer...
    Technical Skills: Python, FastAPI, LangChain, FAISS
    Top Matching Candidate Section (Experience 1):
    Built automated hiring workflows using RAG and multi-agent graphs at Fxis.ai...
    ```

- **`app/graph/fetch_candidates.py`**:
  - Preserved `matched_chunk_type` and `matched_chunk_text` metadata through `FetchCandidatesNodes` into `state.candidate_profiles`.

- **`streamlit_app.py`**:
  - Added a dedicated **🎯 Top Matching Section** highlight box inside each candidate card's expander view.

---

## 6. Automated RAG Evaluation Suite (Precision@K, MRR & Faithfulness)

### Technical Implementation
- **`data/eval_dataset.json`**:
  - Created standardized benchmark test suite containing sample job requirements and expected candidate matches.

- **`app/evaluators/retrieval_evaluator.py`**:
  - Implemented `RetrievalEvaluator` class computing empirical metrics:
    - **Precision@K**: $\frac{\text{Relevant Candidates in Top K}}{K}$
    - **Hit Rate@K**: $1.0$ if $\ge 1$ relevant candidate in Top $K$, else $0.0$.
    - **Mean Reciprocal Rank (MRR)**: $\frac{1}{\text{rank of first relevant candidate}}$

- **`app/evaluators/generation_evaluator.py`**:
  - Implemented `GenerationEvaluator` class (LLM-as-a-Judge):
    - `evaluate_jd_faithfulness()`: Measures JD generation faithfulness against prompt requirements.
    - `evaluate_match_groundedness()`: Verifies section chunk match relevance.

- **`scripts/run_evaluations.py`**:
  - Created CLI benchmark runner executing evaluations across candidate pool and writing a formatted Markdown report to `data/eval_report.md`.

- **`app/api/routes/evaluations.py`**:
  - Created `GET /evaluations/report` REST API endpoint returning current evaluation benchmarks.

---

## 💻 CLI Commands Cheat Sheet

### 1. Re-Index Existing Resumes with Section Chunks
```powershell
python -m scripts.reindex_resumes
```

### 2. Pre-Download 12-Layer Cross-Encoder Model Weights
```powershell
python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')"
```

### 3. Run Automated RAG Evaluation Benchmark Suite
```powershell
python -m scripts.run_evaluations
```

### 4. Run Test Suite
```powershell
pytest tests/
```

### 5. Launch Application Services
```powershell
# Terminal 1 - FastAPI Backend Server
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Streamlit Frontend Dashboard
streamlit run streamlit_app.py
```
