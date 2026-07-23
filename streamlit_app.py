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
    # Inject Custom CSS for Google Fonts, Material Icons, Glassmorphism, and Agentic Gradients
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>

    <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
        }
        .pool-glass-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 4px 15px -2px rgba(11, 28, 48, 0.04);
            margin-bottom: 16px;
        }
        .pool-stat-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        .pool-avatar-badge {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: #e5eeff;
            color: #0525bb;
            font-weight: 800;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Fetch Resumes & Vector DB stats
    from app.services.resume_service import ResumeService
    from app.services.vector_store import VectorStore
    
    rs_service = ResumeService()
    vs_service = VectorStore()
    
    all_resumes = rs_service.list_resumes()
    total_pool_count = len(all_resumes)
    total_vectors_count = vs_service.total_vectors()

    # Hero Banner & Stats
    col_hero_text, col_hero_stats = st.columns([8, 4])
    with col_hero_text:
        st.markdown("""
        <div class="pool-glass-card" style="margin-bottom: 0px; padding: 18px 24px; min-height: 94px;">
            <div style="font-family: Inter; font-weight: 800; font-size: 24px; color: #0b1c30; letter-spacing: -0.02em;">
                Resume Pool Management
            </div>
            <div style="font-size: 13px; color: #444655; margin-top: 4px; line-height: 1.5;">
                Centralized repository for high-potential candidates. Manage ingestions, automated indexing, and AI-powered ranking across your talent ecosystem.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_hero_stats:
        c_st1, c_st2 = st.columns(2)
        with c_st1:
            st.markdown(f"""
            <div class="pool-stat-box" style="min-height: 94px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 10px; font-weight: 700; color: #757686; text-transform: uppercase;">Total Pool</div>
                <div style="font-family: Inter; font-weight: 800; font-size: 24px; color: #0525bb; margin-top: 2px;">{total_pool_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_st2:
            st.markdown(f"""
            <div class="pool-stat-box" style="min-height: 94px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 10px; font-weight: 700; color: #757686; text-transform: uppercase;">FAISS Vectors</div>
                <div style="font-family: Inter; font-weight: 800; font-size: 24px; color: #4648d4; margin-top: 2px;">{total_vectors_count}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Bento Grid: Upload Candidates & Vector Indexing Card
    col_upload, col_report = st.columns([7, 5])

    with col_upload:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px 24px; box-shadow: 0 4px 15px -2px rgba(11, 28, 48, 0.04);">
            <div style="display: flex; align-items: center; gap: 8px; font-family: Inter; font-weight: 800; font-size: 18px; color: #0b1c30;">
                <span class="material-symbols-outlined" style="color: #0525bb;">unarchive</span> Upload Candidates
            </div>
            <div style="font-size: 12px; color: #757686; margin-top: 4px; margin-bottom: 12px;">
                Drop files here to start the agentic parsing & vector indexing process.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose Resume Files (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="resume_pool_uploader"
        )
        
        if uploaded_files:
            if st.button("🚀 Process & Index Resumes into Pool", type="primary", use_container_width=True):
                for uploaded_file in uploaded_files:
                    with st.spinner(f"Parsing and embedding '{uploaded_file.name}'..."):
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            res = requests.post(f"{api_url}/resumes/upload", files=files)
                            if res.status_code in (200, 201):
                                data = res.json()
                                st.success(f"Successfully added `{uploaded_file.name}` to Resume Pool!")
                                st.rerun()
                            else:
                                st.error(f"Failed to process `{uploaded_file.name}`: {res.text}")
                        except Exception as e:
                            st.error(f"Error processing `{uploaded_file.name}`: {e}")

    with col_report:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px 24px; box-shadow: 0 4px 15px -2px rgba(11, 28, 48, 0.04); margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; font-weight: 800; color: #0525bb; font-size: 18px; margin-bottom: 8px;">
                <span class="material-symbols-outlined" style="color: #0525bb;">auto_awesome</span> Active Vector Indexing
            </div>
            <div style="font-size: 12px; color: #444655; margin-bottom: 16px; line-height: 1.5;">
                Resumes are parsed via LLM into structured profiles & embedded into 768-dim dense vectors using <b>BAAI/bge-base-en-v1.5</b>.
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="background: #f8f9ff; border: 1px solid #e2e8f0; padding: 12px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 10px; color: #757686; font-weight: 700; text-transform: uppercase;">Embedding Model</div>
                    <div style="font-size: 13px; font-weight: 800; color: #0b1c30; margin-top: 2px;">bge-base-en-v1.5</div>
                </div>
                <div style="background: #f8f9ff; border: 1px solid #e2e8f0; padding: 12px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 10px; color: #757686; font-weight: 700; text-transform: uppercase;">Dimensions</div>
                    <div style="font-size: 13px; font-weight: 800; color: #0525bb; margin-top: 2px;">768d Dense</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Recently Uploaded Resumes Table / Candidate Roster
    st.markdown("### 📋 Candidate Resume Pool")
    
    search_query = st.text_input("🔍 Search pool by Candidate Name or Skills", placeholder="e.g. Bharg, Python, Robotics...", key="search_resume_pool")

    # Filter resumes based on search query
    filtered_resumes = []
    if search_query.strip():
        q = search_query.strip().lower()
        for r in all_resumes:
            cname = str(r.get("candidate_name", "")).lower()
            raw = str(r.get("raw_text", "")).lower()
            if q in cname or q in raw:
                filtered_resumes.append(r)
    else:
        filtered_resumes = all_resumes

    if not filtered_resumes:
        st.info("No candidates found matching your criteria. Upload resumes above to populate the pool!")
    else:
        for idx, r in enumerate(filtered_resumes, 1):
            rid = r.get("resume_id", f"RES-{idx}")
            cname = r.get("candidate_name") or "Unknown Candidate"
            initials = "".join([part[0].upper() for part in cname.split() if part][:2]) or "CD"
            uploaded_at = r.get("uploaded_at", "N/A")
            if "T" in str(uploaded_at):
                uploaded_at = str(uploaded_at).split("T")[0]

            prof_raw = r.get("candidate_profile")
            prof_dict = json.loads(prof_raw) if isinstance(prof_raw, str) else (prof_raw or {})
            
            contact = prof_dict.get("contact") or {}
            email = contact.get("email") or r.get("email") or "N/A"
            phone = contact.get("phone") or r.get("phone") or "N/A"
            summary = prof_dict.get("professional_summary") or "No summary available."
            skills = prof_dict.get("technical_skills") or []

            # Candidate Card Row
            st.markdown(f"""
            <div class="pool-glass-card">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
                    <div style="display: flex; align-items: center; gap: 14px; min-width: 240px;">
                        <div class="pool-avatar-badge">{initials}</div>
                        <div>
                            <div style="font-family: Inter; font-weight: 700; font-size: 17px; color: #0b1c30;">
                                {cname}
                            </div>
                            <div style="font-size: 12px; color: #757686; margin-top: 2px;">
                                Email: <span style="color: #0525bb;">{email}</span> | Phone: {phone}
                            </div>
                        </div>
                    </div>
                    <div style="font-size: 12px; color: #757686;">
                        Uploaded: <b>{uploaded_at}</b>
                    </div>
                    <div>
                        <span class="status-badge-chip bg-online-chip">
                            <span class="material-symbols-outlined" style="font-size: 14px;">check_circle</span> Vector Indexed
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"🔍 View Extracted Profile & Data ({cname})"):
                st.markdown(f"**Candidate Summary:** {summary}")
                if skills:
                    skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
                    st.markdown(f"**Technical Skills:** `{skills_str}`")
                
                st.markdown("**Parsed JSON Profile:**")
                st.json(prof_dict)
                
                if st.button(f"🗑️ Delete Candidate ({cname})", key=f"btn_del_res_{rid}"):
                    rs_service.delete_resume(rid)
                    vs_service.delete_resume(rid)
                    st.success(f"Deleted candidate '{cname}' from database and vector index!")
                    st.rerun()

# ----------------------------------------------------
# 🎯 PAGE 3: Candidate Fetch
# ----------------------------------------------------
elif selected_page == "🎯 Candidate Fetch":
    # Inject Custom CSS for Google Fonts, Material Icons, Glassmorphism, and Agentic Gradients
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>

    <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
        }
        .glass-card-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px -2px rgba(11, 28, 48, 0.05);
            margin-bottom: 20px;
        }
        .agentic-gradient-banner {
            background: linear-gradient(135deg, #0525bb 0%, #4648d4 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 10px 25px -5px rgba(5, 37, 187, 0.25);
            margin-bottom: 24px;
        }
        .status-badge-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }
        .bg-online-chip { background-color: #dcfce7; color: #166534; }
        .bg-hybrid-chip { background-color: #dfe0ff; color: #000d60; }
        .bg-approved-chip { background-color: #e0e7ff; color: #3730a3; }
        .bg-pending-chip { background-color: #fef3c7; color: #92400e; }

        .avatar-initials-badge {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: #2e44d1;
            color: #ffffff;
            font-weight: 700;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(46, 68, 209, 0.3);
        }
        .score-mono-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 24px;
            font-weight: 700;
            color: #0525bb;
        }
        .rank-metric-box {
            background: #f8f9ff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Top Header & Status Chips Banner
    st.markdown("""
    <div class="agentic-gradient-banner">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-family: Inter; font-weight: 800; font-size: 26px; letter-spacing: -0.02em;">
                    Candidate Fetch & Reranking
                </div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">
                    Hybrid Search Engine: BM25 Keywords + 768-dim FAISS Vector + RRF Fusion + Cross-Encoder Reranker
                </div>
            </div>
            <div>
                <span class="status-badge-chip bg-online-chip">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #22c55e; display: inline-block;"></span>
                    FastAPI: Online
                </span>
                <span class="status-badge-chip bg-hybrid-chip">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #4648d4; display: inline-block;"></span>
                    BAAI/bge-base-en-v1.5 (768d)
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_jobs_tab3 = fetch_all_jobs(api_url)

    if not all_jobs_tab3:
        st.warning("⚠️ No Job Descriptions found in database. Create a Job Description in '📋 JD Generator' first!")
    else:
        job_map_tab3 = {format_job_display(j): j for j in all_jobs_tab3}

        # Controls & Action Button Section
        col_controls, col_trigger = st.columns([7, 5])

        with col_controls:
            st.markdown("#### 📄 Select Job & Retrieval Parameters")
            selected_jd_name = st.selectbox(
                "Approved Job Description",
                options=list(job_map_tab3.keys()),
                key="select_jd_candidate_fetch"
            )
            selected_job_obj = job_map_tab3[selected_jd_name]
            target_job_id = selected_job_obj.get("job_id")
            job_status = selected_job_obj.get("status", "PENDING_APPROVAL")

            top_k_val = st.slider("Top Candidates (K)", min_value=1, max_value=20, value=5, help="Number of top candidate matches to return")

            status_chip = "bg-approved-chip" if job_status == "APPROVED" else "bg-pending-chip"
            st.markdown(f"""
            <div style="font-size: 13px; color: #444655; margin-top: 6px;">
                Selected Job ID: <code>{target_job_id}</code> | Status: <span class="status-badge-chip {status_chip}">{job_status}</span>
            </div>
            """, unsafe_allow_html=True)

        with col_trigger:
            st.markdown("#### ⚡ Trigger Pipeline")
            st.markdown("""
            <div style="background: #f8f9ff; border: 1px solid #c5c5d7; border-radius: 12px; padding: 18px 20px; text-align: center; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px; font-weight: 700; color: #0525bb; font-size: 15px;">
                    <span class="material-symbols-outlined" style="font-size: 24px;">bolt</span> Execute Hybrid Search Pipeline
                </div>
                <div style="font-size: 12px; color: #757686; margin-top: 4px;">
                    BM25 Keywords + FAISS Vector + RRF + Cross-Encoder Reranker
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            btn_fetch = st.button("🚀 Fetch & Rerank Candidates Now", type="primary", use_container_width=True, key="btn_run_retrieval_tab3")

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Execute Retrieval when button is clicked
        if btn_fetch:
            if not target_job_id:
                st.error("Please select a valid Job Description!")
            else:
                with st.spinner(f"Executing Hybrid BM25 + FAISS Vector Search & Reranking for '{selected_jd_name}'..."):
                    try:
                        res = requests.post(f"{api_url}/retrieval/{target_job_id}?top_k={top_k_val}")
                        if res.status_code == 200:
                            retrieval_data = res.json()
                            st.session_state["active_retrieval_results"] = retrieval_data
                        else:
                            st.error(f"Candidate Fetch Error ({res.status_code}): {res.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to candidate retrieval endpoint: {e}")

        # Display Candidate Results Cards
        if "active_retrieval_results" in st.session_state and st.session_state["active_retrieval_results"]:
            retrieved_data = st.session_state["active_retrieval_results"]
            candidates = retrieved_data.get("candidates", [])
            total_cand = retrieved_data.get("total_candidates", 0)

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="font-family: Inter; font-weight: 800; color: #0b1c30; font-size: 22px; margin: 0;">
                    Ranked Candidates ({total_cand})
                </h3>
                <span class="status-badge-chip bg-online-chip">
                    <span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span> Search Complete
                </span>
            </div>
            """, unsafe_allow_html=True)

            if not candidates:
                st.info("No candidate matches found in vector index. Upload candidate resumes in '📂 Resume Pool' first!")
            else:
                for idx, cand in enumerate(candidates, 1):
                    sim_score = float(cand.get("similarity_score", 0.0))
                    rerank_score = float(cand.get("rerank_score", 0.0))
                    rrf_score = float(cand.get("rrf_score", 0.0))
                    bm25_rank = cand.get("bm25_rank", 0)
                    vector_rank = cand.get("vector_rank", 0)
                    profile = cand.get("profile") or {}
                    resume_id = cand.get("resume_id", "N/A")

                    name = profile.get("candidate_name", "Unknown Candidate")
                    initials = "".join([part[0].upper() for part in name.split() if part][:2]) or "CD"
                    
                    contact = profile.get("contact") or {}
                    email = contact.get("email", "N/A") if isinstance(contact, dict) else getattr(contact, "email", "N/A")
                    phone = contact.get("phone", "N/A") if isinstance(contact, dict) else getattr(contact, "phone", "N/A")
                    skills = profile.get("technical_skills", [])
                    summary = profile.get("professional_summary") or "No summary provided."

                    # Candidate Glassmorphic Card HTML
                    st.markdown(f"""
                    <div class="glass-card-container">
                        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
                            <div style="display: flex; align-items: center; gap: 16px; min-width: 220px;">
                                <div class="avatar-initials-badge">{initials}</div>
                                <div>
                                    <div style="font-family: Inter; font-weight: 800; font-size: 19px; color: #0b1c30;">
                                        #{idx}. {name}
                                    </div>
                                    <div style="font-size: 12px; color: #757686; margin-top: 2px;">
                                        ID: <code>{str(resume_id)[:8]}...</code> | Email: <span style="color: #0525bb;">{email}</span>
                                    </div>
                                </div>
                            </div>
                            <div style="text-align: center; min-width: 110px;">
                                <div class="score-mono-val">{rerank_score:.2f}</div>
                                <div style="font-size: 10px; font-weight: 700; color: #757686; text-transform: uppercase; letter-spacing: 0.05em;">
                                    Rerank Score
                                </div>
                            </div>
                            <div style="flex-grow: 1; max-width: 260px; min-width: 180px;">
                                <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: #444655; margin-bottom: 6px;">
                                    <span>Vector Similarity</span>
                                    <span style="color: #0525bb; font-weight: 700;">{sim_score:.1f}%</span>
                                </div>
                                <div style="height: 8px; width: 100%; background: #e5eeff; border-radius: 9999px; overflow: hidden;">
                                    <div style="height: 100%; width: {min(max(sim_score, 0), 100)}%; background: linear-gradient(90deg, #0525bb 0%, #4648d4 100%); border-radius: 9999px;"></div>
                                </div>
                            </div>
                            <div style="text-align: right; min-width: 110px;">
                                <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #4648d4; font-size: 15px;">
                                    RRF: {rrf_score:.4f}
                                </div>
                                <div style="font-size: 10px; font-weight: 700; color: #757686; text-transform: uppercase; letter-spacing: 0.05em;">
                                    Hybrid Rank
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Collapsible Candidate Details with Stats Grid and JSON view
                    with st.expander(f"🔍 View Full Candidate Details ({name})"):
                        st.markdown(f"**Candidate Summary:** {summary}")
                        if skills:
                            skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
                            st.markdown(f"**Technical Skills:** `{skills_str}`")

                        # 4-Metric Grid
                        st.markdown(f"""
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-top: 14px; margin-bottom: 14px;">
                            <div class="rank-metric-box">
                                <div style="font-size: 10px; color: #757686; font-weight: 700; text-transform: uppercase;">BM25 Keyword</div>
                                <div style="font-size: 18px; font-weight: 800; color: #0b1c30;">#{bm25_rank}</div>
                            </div>
                            <div class="rank-metric-box">
                                <div style="font-size: 10px; color: #757686; font-weight: 700; text-transform: uppercase;">FAISS Vector</div>
                                <div style="font-size: 18px; font-weight: 800; color: #0525bb;">#{vector_rank}</div>
                            </div>
                            <div class="rank-metric-box">
                                <div style="font-size: 10px; color: #757686; font-weight: 700; text-transform: uppercase;">Vector Match</div>
                                <div style="font-size: 18px; font-weight: 800; color: #0525bb;">{sim_score:.1f}%</div>
                            </div>
                            <div class="rank-metric-box">
                                <div style="font-size: 10px; color: #757686; font-weight: 700; text-transform: uppercase;">Contact Phone</div>
                                <div style="font-size: 13px; font-weight: 700; color: #0b1c30;">{phone}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("**Parsed Profile JSON Structure:**")
                        st.json(profile)

