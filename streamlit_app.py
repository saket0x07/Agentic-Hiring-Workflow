import os
import json
import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Agentic Hiring Workflow",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
DEFAULT_API_URL = "http://127.0.0.1:8000"

def fetch_all_jobs(url: str):
    """Fetch list of all jobs from backend API, with fallback to DatabaseService."""
    for path in ["/jobs/", "/jobs"]:
        try:
            res = requests.get(f"{url}{path}", timeout=5, allow_redirects=True)
            if res.status_code == 200:
                jobs = res.json()
                if jobs:
                    return jobs
        except Exception:
            pass
    # Fallback to direct DB query if API endpoint is busy or reloaded
    try:
        from app.services.database_service import DatabaseService
        return DatabaseService().list_jobs()
    except Exception:
        pass
    return []


def format_job_display(job: dict) -> str:
    """Format job record for user-friendly dropdown display by Job Name/Title."""
    gen_jd = job.get("generated_jd") or {}
    title = gen_jd.get("job_title") if isinstance(gen_jd, dict) else None
    if not title:
        hr = job.get("hiring_request") or {}
        title = hr.get("role") if isinstance(hr, dict) else None
    title = title or "Untitled Job"
    status = job.get("status", "UNKNOWN")
    job_id_short = job.get("job_id", "")[:8]
    return f"📌 {title} [{status}] ({job_id_short}...)"


# Sidebar Configuration & LHS Menu Selection
with st.sidebar:
    st.title("⚙️ Workflow Config")
    api_url = st.text_input("FastAPI Service URL", value=DEFAULT_API_URL).rstrip("/")

    st.markdown("---")
    st.markdown("### 📌 Navigation")
    # Menu Selection on LHS Sidebar as requested by USER
    selected_page = st.radio(
        "Select Operation:",
        options=[
            "📋 JD Generator",
            "📂 Resume Pool",
            "🎯 Candidate Fetch"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### Service Health Check")
    if st.button("Check Backend Status"):
        try:
            res = requests.get(f"{api_url}/health", timeout=3)
            if res.status_code == 200:
                data = res.json()
                st.success(f"Backend Connected ({data.get('status', 'healthy')})")
            else:
                st.error(f"Backend returned HTTP {res.status_code}")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")

    st.markdown("---")
    st.caption("Agentic Hiring Workflow Dashboard v1.2")


st.title("🎯 Agentic Hiring Workflow")
st.markdown("Automated AI Job Description Generation, Resume Pool Management & Candidate Retrieval")


# ----------------------------------------------------
# 📋 PAGE 1: JD Generator
# ----------------------------------------------------
if selected_page == "📋 JD Generator":
    st.header("Job Description Generator & Review")

    col_create, col_lookup = st.columns([2, 1])

    all_jobs = fetch_all_jobs(api_url)

    with col_lookup:
        st.subheader("🔍 Select Existing Job")
        if all_jobs:
            job_options = {format_job_display(j): j for j in all_jobs}
            selected_display = st.selectbox(
                "Choose Job by Name/Title:",
                options=list(job_options.keys()),
                key="select_existing_job_tab1"
            )
            if st.button("Load Selected Job", key="btn_load_job_tab1"):
                st.session_state["current_job"] = job_options[selected_display]
                st.success(f"Loaded '{selected_display}'!")
        else:
            st.info("No jobs created yet. Fill the form on the left to generate your first JD!")

    with col_create:
        st.subheader("✨ Create New Hiring Request")
        with st.form("form_create_job"):
            f_role = st.text_input("Job Role / Title*", value="Senior Backend Engineer")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                f_dept = st.text_input("Department", value="Engineering")
            with c2:
                f_exp = st.text_input("Experience Level", value="3-5 years")
            with c3:
                f_loc = st.text_input("Location", value="Remote")
                
            c4, c5, c6 = st.columns(3)
            with c4:
                f_emp = st.selectbox("Employment Type", ["full_time", "part_time", "contract", "intern"])
            with c5:
                f_mode = st.selectbox("Work Mode", ["remote", "on_site", "hybrid"])
            with c6:
                f_budget = st.text_input("Salary Budget (Optional)", value="$120,000 - $150,000")

            f_req_skills = st.text_area("Required Skills (comma separated)*", value="Python, FastAPI, PostgreSQL, Docker")
            f_pref_skills = st.text_area("Preferred Skills (comma separated)", value="AWS, Redis, Kubernetes, CI/CD")
            f_notes = st.text_area("Additional Recruiter Notes (Optional)", value="Looking for someone with strong API design background.")

            btn_submit_jd = st.form_submit_button("🚀 Generate Job Description with AI", type="primary")

        if btn_submit_jd:
            if not f_role.strip():
                st.error("Job Title is required!")
            else:
                payload = {
                    "role": f_role.strip(),
                    "department": f_dept.strip(),
                    "experience": f_exp.strip(),
                    "location": f_loc.strip(),
                    "employment_type": f_emp,
                    "work_mode": f_mode,
                    "budget": f_budget.strip() if f_budget else None,
                    "required_skills": [s.strip() for s in f_req_skills.split(",") if s.strip()],
                    "preferred_skills": [s.strip() for s in f_pref_skills.split(",") if s.strip()],
                    "notes": f_notes.strip() if f_notes else None
                }
                with st.spinner("AI Agent is generating the Job Description..."):
                    try:
                        res = requests.post(f"{api_url}/jobs/create", json=payload, timeout=60)
                        if res.status_code in (200, 201):
                            data = res.json()
                            job_id = data.get("job_id")
                            st.success(f"Job Description Generated! Job ID: `{job_id}`")
                            
                            res_job = requests.get(f"{api_url}/jobs/{job_id}")
                            if res_job.status_code == 200:
                                st.session_state["current_job"] = res_job.json()
                        else:
                            st.error(f"Error {res.status_code}: {res.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to JD generation service: {e}")

    # Display Current Job Details & Review Actions
    if "current_job" in st.session_state and st.session_state["current_job"]:
        job_data = st.session_state["current_job"]
        st.markdown("---")
        
        gen_jd_data = job_data.get("generated_jd") or {}
        jd_title_display = gen_jd_data.get("job_title", "Job Description") if isinstance(gen_jd_data, dict) else "Job Description"
        
        st.subheader(f"📌 Active Job: {jd_title_display} (`{job_data.get('job_id')}`)")
        
        status_color = "🟢" if job_data.get("status") == "APPROVED" else "🟡"
        st.markdown(f"**Status:** {status_color} `{job_data.get('status')}` | **Retry Count:** `{job_data.get('retry_count', 0)}`")

        # Render Generated JD Preview
        with st.expander("📄 View Generated Job Description Details", expanded=True):
            if isinstance(gen_jd_data, dict):
                st.markdown(f"### {gen_jd_data.get('job_title', 'Job Description')}")
                st.write(gen_jd_data.get("summary", ""))
                
                c_req, c_pref = st.columns(2)
                with c_req:
                    st.markdown("**Required Skills:**")
                    skills = gen_jd_data.get("must_have_skills", [])
                    st.write(", ".join(skills) if isinstance(skills, list) else skills)
                with c_pref:
                    st.markdown("**Nice to Have Skills:**")
                    pref = gen_jd_data.get("nice_to_have_skills", [])
                    st.write(", ".join(pref) if isinstance(pref, list) else pref)

                if gen_jd_data.get("responsibilities"):
                    st.markdown("**Key Responsibilities:**")
                    resps = gen_jd_data.get("responsibilities", [])
                    if isinstance(resps, list):
                        for r in resps:
                            st.markdown(f"- {r}")
                    else:
                        st.write(resps)

                if gen_jd_data.get("interview_rounds"):
                    st.markdown("**Interview Process:**")
                    rounds = gen_jd_data.get("interview_rounds", [])
                    if isinstance(rounds, list):
                        for idx, rd in enumerate(rounds, 1):
                            st.markdown(f"{idx}. {rd}")
                    else:
                        st.write(rounds)
            else:
                st.write(gen_jd_data)

        # Actions: Approve or Reject
        col_app, col_rej = st.columns(2)

        with col_app:
            st.markdown("#### ✅ Approve Job Description")
            if job_data.get("status") == "APPROVED":
                st.info("This Job Description is already APPROVED.")
                pdf_path = job_data.get("pdf_path")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Approved Job Description PDF",
                            data=f.read(),
                            file_name=f"Job_Description_{job_data.get('job_id')[:8]}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
            else:
                if st.button("Approve & Generate PDF", key="btn_approve", type="primary"):
                    with st.spinner("Approving and generating PDF..."):
                        try:
                            res_app = requests.post(f"{api_url}/jobs/{job_data.get('job_id')}/approve")
                            if res_app.status_code == 200:
                                st.success("Job Description Approved!")
                                res_updated = requests.get(f"{api_url}/jobs/{job_data.get('job_id')}")
                                if res_updated.status_code == 200:
                                    st.session_state["current_job"] = res_updated.json()
                                    st.rerun()
                            else:
                                st.error(f"Approval error: {res_app.text}")
                        except Exception as e:
                            st.error(f"Approval failed: {e}")

        with col_rej:
            st.markdown("#### ❌ Reject & Regenerate with Feedback")
            with st.form("form_reject_jd"):
                feedback_text = st.text_area("Provide feedback for revision:", placeholder="e.g. Include more emphasis on AWS cloud architecture...")
                btn_reject = st.form_submit_button("Submit Feedback & Regenerate AI JD")

            if btn_reject:
                if not feedback_text.strip():
                    st.error("Please provide feedback for regeneration.")
                else:
                    with st.spinner("Regenerating Job Description based on feedback..."):
                        try:
                            res_rej = requests.post(
                                f"{api_url}/jobs/{job_data.get('job_id')}/reject",
                                json={"feedback": feedback_text.strip()}
                            )
                            if res_rej.status_code == 200:
                                st.success("Job Description revised and regenerated!")
                                res_updated = requests.get(f"{api_url}/jobs/{job_data.get('job_id')}")
                                if res_updated.status_code == 200:
                                    st.session_state["current_job"] = res_updated.json()
                                    st.rerun()
                            else:
                                st.error(f"Rejection error: {res_rej.text}")
                        except Exception as e:
                            st.error(f"Rejection failed: {e}")

# ----------------------------------------------------
# 📂 PAGE 2: Resume Pool
# ----------------------------------------------------
elif selected_page == "📂 Resume Pool":
    st.header("Resume Pool & Candidate Upload")
    st.markdown("Upload candidate resumes (PDF, DOCX, TXT) to extract profile data and store vector embeddings in the resume pool.")

    uploaded_files = st.file_uploader(
        "Choose Resume Files to add to Resume Pool",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("⚡ Process & Index Resumes into Pool", type="primary"):
            for uploaded_file in uploaded_files:
                with st.spinner(f"Parsing and embedding '{uploaded_file.name}'..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        res = requests.post(f"{api_url}/resumes/upload", files=files)
                        if res.status_code in (200, 201):
                            data = res.json()
                            st.success(f"Successfully added `{uploaded_file.name}` to Resume Pool! Resume ID: `{data.get('resume_id')}`")
                            with st.expander(f"View Extracted Candidate Profile ({uploaded_file.name})"):
                                st.json(data.get("parsed_profile", {}))
                        else:
                            st.error(f"Failed to process `{uploaded_file.name}`: {res.text}")
                    except Exception as e:
                        st.error(f"Error processing `{uploaded_file.name}`: {e}")

# ----------------------------------------------------
# 🎯 PAGE 3: Candidate Fetch
# ----------------------------------------------------
elif selected_page == "🎯 Candidate Fetch":
    st.header("Hybrid Candidate Fetch & Reranking (BM25 + FAISS Vector + Cross-Encoder)")
    col_hdr, col_ref = st.columns([4, 1])
    with col_hdr:
        st.markdown("Select a Job Description by Name to fetch and rerank top matching candidates using **BM25 Keyword Search**, **FAISS Vector Search**, **Reciprocal Rank Fusion (RRF)**, and **Cross-Encoder Reranking**.")
    with col_ref:
        if st.button("🔄 Refresh Jobs", key="btn_refresh_jobs_tab3"):
            st.rerun()

    all_jobs_tab3 = fetch_all_jobs(api_url)

    if not all_jobs_tab3:
        st.warning("⚠️ No Job Descriptions found in database. Create a Job Description in '📋 JD Generator' first!")
    else:
        job_map_tab3 = {format_job_display(j): j for j in all_jobs_tab3}

        col_select_jd, col_topk = st.columns([3, 1])

        with col_select_jd:
            selected_jd_name = st.selectbox(
                "Select Job Description by Name/Title*",
                options=list(job_map_tab3.keys()),
                key="select_jd_candidate_fetch"
            )
            selected_job_obj = job_map_tab3[selected_jd_name]
            target_job_id = selected_job_obj.get("job_id")

            job_status = selected_job_obj.get("status", "PENDING_APPROVAL")
            status_badge = "🟢 Approved" if job_status == "APPROVED" else "🟡 Pending Approval"
            st.caption(f"Selected Job ID: `{target_job_id}` | Status: **{status_badge}**")

        with col_topk:
            top_k_val = st.slider("Top Candidates (K)", min_value=1, max_value=20, value=5)

        if st.button("🎯 Fetch & Rerank Candidates for Selected Job", type="primary", key="btn_run_retrieval_tab3"):
            if not target_job_id:
                st.error("Please select a Job Description!")
            else:
                with st.spinner(f"Running Hybrid Search (BM25 + FAISS Vector + Cross-Encoder) for '{selected_jd_name}'..."):
                    try:
                        res = requests.post(f"{api_url}/retrieval/{target_job_id}?top_k={top_k_val}")
                        if res.status_code == 200:
                            retrieval_data = res.json()
                            candidates = retrieval_data.get("candidates", [])
                            total_cand = retrieval_data.get("total_candidates", 0)

                            st.success(f"Successfully fetched & reranked {total_cand} candidates using Hybrid BM25 + Vector Search!")

                            if not candidates:
                                st.info("No candidates found in vector index matching this job. Upload resumes in '📂 Resume Pool' first!")
                            else:
                                for idx, cand in enumerate(candidates, 1):
                                    sim_score = cand.get("similarity_score", 0.0)
                                    rerank_score = cand.get("rerank_score", 0.0)
                                    rrf_score = cand.get("rrf_score", 0.0)
                                    bm25_rank = cand.get("bm25_rank", 0)
                                    vector_rank = cand.get("vector_rank", 0)
                                    profile = cand.get("profile") or {}
                                    resume_id = cand.get("resume_id")

                                    name = profile.get("candidate_name", "Unknown Candidate")
                                    contact = profile.get("contact") or {}
                                    email = contact.get("email", "N/A") if isinstance(contact, dict) else getattr(contact, "email", "N/A")
                                    phone = contact.get("phone", "N/A") if isinstance(contact, dict) else getattr(contact, "phone", "N/A")
                                    skills = profile.get("technical_skills", [])
                                    summary = profile.get("professional_summary", "No summary provided.")

                                    with st.container():
                                        st.markdown(f"### #{idx}. {name} — Rerank Score: **{rerank_score:.2f}** | Hybrid RRF: **{rrf_score:.4f}**")
                                        st.progress(min(max(float(sim_score) / 100.0, 0.0), 1.0))

                                        c_m1, c_m2, c_m3 = st.columns(3)
                                        with c_m1:
                                            st.markdown(f"🔤 **BM25 Keyword Rank:** `#{bm25_rank}`")
                                        with c_m2:
                                            st.markdown(f"📐 **FAISS Vector Rank:** `#{vector_rank}`")
                                        with c_m3:
                                            st.markdown(f"⚡ **Vector Similarity:** `{sim_score:.1f}%`")

                                        st.markdown(f"**Resume ID:** `{resume_id}` | **Email:** `{email}` | **Phone:** `{phone}`")
                                        st.markdown(f"**Summary:** {summary}")
                                        if skills:
                                            st.markdown(f"**Skills:** {', '.join(skills) if isinstance(skills, list) else skills}")

                                        with st.expander("🔍 View Full Profile Details"):
                                            st.json(profile)

                                        st.markdown("---")
                        else:
                            st.error(f"Candidate Fetch Error ({res.status_code}): {res.text}")
                    except Exception as e:
                        st.error(f"Failed to fetch candidates: {e}")
