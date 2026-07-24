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
    st.caption("Agentic Hiring Workflow")


# ----------------------------------------------------
# 📋 PAGE 1: JD Generator
# ----------------------------------------------------
if selected_page == "📋 JD Generator":
    # Inject Custom CSS for Google Fonts (Inter & JetBrains Mono), Material Icons, and Candidate Fetch Color Palette
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

        /* Snowy White Background Tokens matching Candidate Fetch */
        :root {
            --primary: #0525bb;
            --primary-container: #2e44d1;
            --secondary: #4648d4;
            --on-surface: #0b1c30;
            --on-surface-variant: #444655;
            --background: #ffffff;
            --surface: #ffffff;
            --surface-container-low: #f8f9ff;
            --surface-container-high: #e5eeff;
            --outline: #757686;
            --outline-variant: #e2e8f0;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main, .stApp {
            font-family: 'Inter', sans-serif !important;
            color: #0b1c30 !important;
            background-color: #ffffff !important;
            background: #ffffff !important;
        }

        /* Container Card styling - Crisp Pure White with Subtle Border */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            box-shadow: 0 2px 12px rgba(11, 28, 48, 0.03) !important;
        }

        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
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
            font-family: 'Inter', sans-serif !important;
            font-size: 12px !important;
            font-weight: 600 !important;
        }
        .bg-online-chip { background-color: #dcfce7 !important; color: #166534 !important; border: 1px solid #bbf7d0 !important; }
        .bg-hybrid-chip { background-color: #dfe0ff !important; color: #000d60 !important; border: 1px solid #bcc3ff !important; }
        .bg-approved-chip { background-color: #e0e7ff !important; color: #3730a3 !important; border: 1px solid #c0c1ff !important; }
        .bg-pending-chip { background-color: #fef3c7 !important; color: #92400e !important; border: 1px solid #fde68a !important; }

        .jd-skill-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 16px;
            background: #eff4ff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            width: 120px;
            text-align: center;
            font-family: 'Inter', sans-serif !important;
        }
        .jd-step-card {
            flex: 1;
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 12px 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
            font-family: 'Inter', sans-serif !important;
        }
        .ai-insight-box {
            background: rgba(46, 68, 209, 0.06) !important;
            border: 1px solid rgba(46, 68, 209, 0.2) !important;
            border-radius: 14px !important;
            padding: 18px;
            margin-bottom: 20px;
            font-family: 'Inter', sans-serif !important;
        }
        .active-job-card-item {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 14px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            font-family: 'Inter', sans-serif !important;
        }
        .active-job-card-item.selected-job {
            border-left: 4px solid #0525bb !important;
            background: #f8f9ff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    all_jobs = fetch_all_jobs(api_url)

    # Hero Banner (Matching Candidate Fetch Page)
    st.markdown("""
    <div class="agentic-gradient-banner">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div>
                <h2 style="font-family: Inter; font-weight: 800; font-size: 24px; color: #ffffff; margin: 0;">
                    JD Generator & AI Control
                </h2>
                <p style="font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 4px; margin-bottom: 0;">
                    Create high-impact job descriptions using agentic AI. Fill out the requirements below or select from your active pool.
                </p>
            </div>
            <div style="display: flex; gap: 8px;">
                <span class="status-badge-chip bg-online-chip">FastAPI: Online</span>
                <span class="status-badge-chip bg-hybrid-chip">LLM Agentic Engine</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Split-Pane Layout: New Request & Selection
    col_create, col_lookup = st.columns([7, 5])

    with col_create:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px;">
                <div style="font-family: Inter; font-weight: 800; font-size: 18px; color: #0b1c30; display: flex; align-items: center; gap: 8px;">
                    <span class="material-symbols-outlined" style="color: #0525bb;">add_circle</span> Create New Hiring Request
                </div>
                <span class="status-badge-chip bg-hybrid-chip">AI-Assisted</span>
            </div>
            """, unsafe_allow_html=True)

            with st.form("form_create_job"):
                c1, c2 = st.columns(2)
                with c1:
                    f_role = st.text_input("Job Title", value="Senior Frontend Engineer", key="p1_job_role")
                with c2:
                    f_dept = st.selectbox("Department", ["Engineering", "Product", "Design", "Marketing", "Sales", "Operations"], key="p1_job_dept")

                c3, c4 = st.columns(2)
                with c3:
                    f_exp = st.selectbox("Experience Level", ["Junior (1-3 years)", "Mid-level (3-5 years)", "Senior (5-8 years)", "Staff/Principal (8+ years)"], key="p1_job_exp")
                with c4:
                    f_loc = st.text_input("Location", value="Remote, New York, etc.", key="p1_job_loc")
                    
                c5, c6, c7 = st.columns(3)
                with c5:
                    f_emp = st.selectbox("Employment Type", ["full_time", "part_time", "contract", "intern"], key="p1_job_emp")
                with c6:
                    f_mode = st.selectbox("Work Mode", ["remote", "on_site", "hybrid"], key="p1_job_mode")
                with c7:
                    f_budget = st.text_input("Salary Budget", value="$120,000 - $150,000", key="p1_job_budget")

                f_req_skills = st.text_area("Core Skills & Tech Stack", value="List key technologies and competencies...", height=80, key="p1_req_skills")

                col_btn_l, col_btn_r = st.columns([6, 6])
                with col_btn_r:
                    btn_submit_jd = st.form_submit_button("🪄 Generate JD", type="primary", use_container_width=True)

            if btn_submit_jd:
                if not f_role.strip() or f_role == "e.g. Senior Frontend Engineer":
                    st.error("Please enter a valid Job Title!")
                else:
                    payload = {
                        "role": f_role.strip(),
                        "department": f_dept.strip(),
                        "experience": f_exp.strip(),
                        "location": f_loc.strip(),
                        "employment_type": f_emp,
                        "work_mode": f_mode,
                        "budget": f_budget.strip() if f_budget else None,
                        "required_skills": [s.strip() for s in f_req_skills.split(",") if s.strip() and s != "List key technologies and competencies..."],
                        "notes": "Generated from Agentic Hiring Workflow UI"
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
                                    st.rerun()
                            else:
                                st.error(f"Error {res.status_code}: {res.text}")
                        except Exception as e:
                            st.error(f"Failed to connect to JD generation service: {e}")

    with col_lookup:
        with st.container(border=True):
            st.markdown("""
            <div style="font-family: Inter; font-weight: 800; font-size: 18px; color: #0b1c30; display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px;">
                <span class="material-symbols-outlined" style="color: #757686;">history</span> Select Existing Job
            </div>
            """, unsafe_allow_html=True)
            
            if all_jobs:
                job_options = {format_job_display(j): j for j in all_jobs}
                selected_display = st.selectbox(
                    "Choose Job from Active Pool:",
                    options=list(job_options.keys()),
                    key="select_existing_job_p1"
                )
                
                selected_job_obj = job_options[selected_display]
                j_status = selected_job_obj.get("status", "PENDING")
                j_chip_cls = "bg-online-chip" if j_status == "APPROVED" else "bg-pending-chip"
                
                st.markdown(f"""
                <div class="active-job-card-item selected-job">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="font-weight: 800; font-size: 15px; color: #0b1c30;">{selected_job_obj.get('title', 'Job Position')}</div>
                        <span style="font-size: 11px; color: #757686;">Active</span>
                    </div>
                    <div style="font-size: 12px; color: #757686; margin-top: 2px;">
                        {selected_job_obj.get('department', 'Engineering')} • {selected_job_obj.get('location', 'Remote')}
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 10px;">
                        <span class="status-badge-chip {j_chip_cls}">{j_status}</span>
                        <span style="font-size: 11px; font-weight: 700; color: #757686;">ID: <code>{selected_job_obj.get('job_id')[:8]}</code></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("📄 Load Selected Job into Review Workspace", key="btn_load_job_p1", use_container_width=True, type="primary"):
                    st.session_state["current_job"] = selected_job_obj
                    st.success(f"Loaded '{selected_display}'!")
                    st.rerun()
            else:
                st.info("No jobs created yet. Fill out the hiring request form on the left to generate your first Job Description!")

    # Active Job Review & AI Control Workspace
    if "current_job" in st.session_state and st.session_state["current_job"]:
        job_data = st.session_state["current_job"]
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        
        gen_jd_data = job_data.get("generated_jd") or {}
        jd_title_display = gen_jd_data.get("job_title", job_data.get("title", "Job Description")) if isinstance(gen_jd_data, dict) else "Job Description"
        job_status = job_data.get("status", "PENDING_APPROVAL")
        status_chip_cls = "bg-online-chip" if job_status == "APPROVED" else "bg-pending-chip"
        
        # Section Header with Right Action Buttons
        col_hdr_left, col_hdr_right = st.columns([7, 5])
        with col_hdr_left:
            st.markdown(f"""
            <div style="font-family: Inter; font-weight: 800; font-size: 24px; color: #0b1c30;">
                Active Job Review
            </div>
            """, unsafe_allow_html=True)
        with col_hdr_right:
            c_act1, c_act2 = st.columns(2)
            with c_act1:
                pdf_path = job_data.get("pdf_path")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Export PDF",
                            data=f.read(),
                            file_name=f"Job_Description_{job_data.get('job_id')[:8]}.pdf",
                            mime="application/pdf",
                            key="btn_export_pdf_p1",
                            use_container_width=True
                        )
                else:
                    st.button("📥 Export PDF", key="btn_export_disabled", disabled=True, use_container_width=True)
            with c_act2:
                st.button("🔗 Copy Link", key="btn_copy_link_p1", use_container_width=True)

        col_jd_view, col_jd_actions = st.columns([7, 5])

        with col_jd_view:
            with st.container(border=True):
                if isinstance(gen_jd_data, dict):
                    dept = gen_jd_data.get("department", job_data.get("department", "Engineering"))
                    loc = gen_jd_data.get("location", job_data.get("location", "Remote"))
                    
                    st.markdown(f"""
                    <div style="position: relative; overflow: hidden; padding: 4px;">
                        <span class="material-symbols-outlined" style="font-size: 110px; color: rgba(5, 37, 187, 0.06); position: absolute; top: -10px; right: -10px; pointer-events: none;">description</span>
                        <div style="font-size: 11px; font-weight: 800; color: #0525bb; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 4px;">
                            {dept} / {loc}
                        </div>
                        <div style="font-family: Inter; font-weight: 800; font-size: 28px; color: #0b1c30; margin-bottom: 12px;">
                            {jd_title_display}
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
                            <span style="background: #e5eeff; color: #0525bb; font-weight: 700; font-size: 12px; padding: 4px 14px; border-radius: 8px; border: 1px solid rgba(5, 37, 187, 0.2);">Full-time</span>
                            <span style="background: #e5eeff; color: #0525bb; font-weight: 700; font-size: 12px; padding: 4px 14px; border-radius: 8px; border: 1px solid rgba(5, 37, 187, 0.2);">{job_data.get('budget') or '$160k - $210k'}</span>
                            <span class="status-badge-chip {status_chip_cls}">{job_status}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    summary_text = gen_jd_data.get("summary", "")
                    if summary_text:
                        st.markdown(f"<div style='font-size: 14px; color: #444655; line-height: 1.6; margin-bottom: 20px;'>{summary_text}</div>", unsafe_allow_html=True)
                    
                    # Key Responsibilities
                    if gen_jd_data.get("responsibilities"):
                        st.markdown("""
                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 800; color: #0525bb; font-size: 16px; margin-top: 16px; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
                            <span class="material-symbols-outlined" style="color: #0525bb;">rocket_launch</span> Key Responsibilities
                        </div>
                        """, unsafe_allow_html=True)
                        resps = gen_jd_data.get("responsibilities", [])
                        if isinstance(resps, list):
                            for r in resps:
                                st.markdown(f"- {r}")
                        else:
                            st.write(resps)

                    # Required Skills Cards Grid
                    skills = gen_jd_data.get("must_have_skills", [])
                    if skills:
                        st.markdown("""
                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 800; color: #0525bb; font-size: 16px; margin-top: 22px; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
                            <span class="material-symbols-outlined" style="color: #0525bb;">psychology</span> Required Skills & Tech Stack
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if isinstance(skills, list):
                            skills_html = "<div style='display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;'>"
                            icons = ["terminal", "hub", "database", "cloud", "code", "memory", "settings"]
                            for idx, s in enumerate(skills):
                                ic = icons[idx % len(icons)]
                                skills_html += f'<div class="jd-skill-card"><span class="material-symbols-outlined" style="font-size: 32px; color: #0525bb;">{ic}</span><span style="font-size: 12px; font-weight: 700; color: #0b1c30;">{s}</span></div>'
                            skills_html += "</div>"
                            st.markdown(skills_html, unsafe_allow_html=True)

                    # Interview Process Steps
                    if gen_jd_data.get("interview_rounds"):
                        st.markdown("""
                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 800; color: #0525bb; font-size: 16px; margin-top: 22px; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
                            <span class="material-symbols-outlined" style="color: #0525bb;">timeline</span> Interview Process
                        </div>
                        """, unsafe_allow_html=True)
                        rounds = gen_jd_data.get("interview_rounds", [])
                        if isinstance(rounds, list):
                            steps_html = "<div style='display: flex; flex-wrap: wrap; gap: 12px; padding-bottom: 8px;'>"
                            for i, rd in enumerate(rounds, 1):
                                steps_html += f'<div class="jd-step-card" style="min-width: 140px;"><span style="font-size: 10px; font-weight: 800; color: #0525bb; text-transform: uppercase;">Step {i}</span><div style="font-size: 13px; font-weight: 800; color: #0b1c30; margin-top: 2px;">{rd}</div></div>'
                            steps_html += "</div>"
                            st.markdown(steps_html, unsafe_allow_html=True)

        with col_jd_actions:
            # AI Content Insight Box
            st.markdown("""
            <div class="ai-insight-box">
                <div style="display: flex; align-items: center; gap: 8px; font-weight: 800; color: #0525bb; font-size: 15px; margin-bottom: 6px;">
                    <span class="material-symbols-outlined" style="color: #0525bb;">auto_awesome</span> AI Content Insight
                </div>
                <div style="font-size: 12px; color: #0b1c30; line-height: 1.5;">
                    The current salary range is 15% higher than the market average for "Python Lead" in Remote roles. This may attract a higher volume of top-tier talent but requires stricter initial screening.
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("""
                <div style="font-family: Inter; font-weight: 800; font-size: 17px; color: #0b1c30; margin-bottom: 4px;">
                    Provide Feedback
                </div>
                <div style="font-size: 12px; color: #757686; margin-bottom: 12px;">
                    Not quite right? Let the AI know what to change.
                </div>
                """, unsafe_allow_html=True)

                feedback_input = st.text_area(
                    "Feedback Notes",
                    placeholder="e.g. 'Make the responsibilities more focused on DevOps' or 'Adjust the salary range lower'...",
                    height=90,
                    key="p1_feedback_text",
                    label_visibility="collapsed"
                )

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    btn_reject = st.button("🔄 Reject & Regenerate", key="btn_reject_p1", use_container_width=True)

                with col_btn2:
                    btn_approve = st.button("✅ Approve JD", key="btn_approve_p1", type="primary", use_container_width=True)

                if btn_reject:
                    if not feedback_input.strip():
                        st.error("Please provide feedback text before clicking Reject & Regenerate!")
                    else:
                        with st.spinner("Regenerating Job Description based on feedback..."):
                            try:
                                res_rej = requests.post(
                                    f"{api_url}/jobs/{job_data.get('job_id')}/reject",
                                    json={"feedback": feedback_input.strip()}
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

                if btn_approve:
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

                st.markdown("""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 11px;">
                    <span style="color: #166534; font-weight: 700; display: flex; align-items: center; gap: 4px;">
                        <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; display: inline-block;"></span> Version Active
                    </span>
                    <span style="color: #0525bb; font-weight: 700; cursor: pointer;">View Revision History</span>
                </div>
                """, unsafe_allow_html=True)

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
        /* Style Streamlit File Uploader to match Embedding Model inner box (#f8f9ff with #e2e8f0 border) */
        div[data-testid="stFileUploader"] {
            background-color: #f8f9ff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 8px 12px !important;
            margin-top: 8px !important;
        }
        div[data-testid="stFileUploader"] section {
            background-color: #f8f9ff !important;
            border: none !important;
            padding: 4px !important;
        }
        div[data-testid="stFileUploader"] section button {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            color: #0b1c30 !important;
            font-weight: 600 !important;
        }
        /* Equalize height of Upload Candidates & Active Vector Indexing container cards */
        div[data-testid="stColumn"] div[data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 185px !important;
            height: 185px !important;
            box-sizing: border-box !important;
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

    # Hero Banner & Stats (Equalized Height)
    col_hero_text, col_hero_stats = st.columns([8, 4])
    with col_hero_text:
        st.markdown("""
        <div class="pool-glass-card" style="margin-bottom: 0px; padding: 16px 22px; height: 112px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-family: Inter; font-weight: 800; font-size: 22px; color: #0b1c30; letter-spacing: -0.02em; line-height: 1.2;">
                Resume Pool Management
            </div>
            <div style="font-size: 12px; color: #444655; margin-top: 4px; line-height: 1.4;">
                Centralized repository for high-potential candidates. Manage ingestions, automated indexing, and AI-powered ranking across your talent ecosystem.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_hero_stats:
        c_st1, c_st2 = st.columns(2)
        with c_st1:
            st.markdown(f"""
            <div class="pool-stat-box" style="height: 112px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div style="font-size: 10px; font-weight: 700; color: #757686; text-transform: uppercase;">Total Pool</div>
                <div style="font-family: Inter; font-weight: 800; font-size: 26px; color: #0525bb; margin-top: 2px;">{total_pool_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_st2:
            st.markdown(f"""
            <div class="pool-stat-box" style="height: 112px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div style="font-size: 10px; font-weight: 700; color: #757686; text-transform: uppercase;">FAISS Vectors</div>
                <div style="font-family: Inter; font-weight: 800; font-size: 26px; color: #4648d4; margin-top: 2px;">{total_vectors_count}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Bento Grid: Upload Candidates & Vector Indexing Card (Equalized Card Layout & Style)
    col_upload, col_report = st.columns([7, 5])

    with col_upload:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 8px; font-family: Inter; font-weight: 800; font-size: 18px; color: #0b1c30;">
                <span class="material-symbols-outlined" style="color: #0525bb;">unarchive</span> Upload Candidates
            </div>
            <div style="font-size: 12px; color: #757686; margin-top: 4px; margin-bottom: 8px;">
                Drop files here to start the agentic parsing & vector indexing process.
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "Choose Resume Files (PDF, DOCX, TXT)",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="resume_pool_uploader",
                label_visibility="collapsed"
            )
            
            if uploaded_files:
                if st.button("🚀 Process & Index Resumes into Pool", type="primary", use_container_width=True):
                    total_files = len(uploaded_files)
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0.0)
                    status_placeholder = st.empty()
                    
                    for idx, uploaded_file in enumerate(uploaded_files):
                        status_placeholder.info(f"⏳ Processing resume {idx + 1}/{total_files}: `{uploaded_file.name}`...")
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            res = requests.post(f"{api_url}/resumes/upload", files=files)
                            if res.status_code in (200, 201):
                                success_count += 1
                                st.toast(f"✅ Added `{uploaded_file.name}` to pool", icon="✅")
                            else:
                                error_count += 1
                                st.error(f"Failed to process `{uploaded_file.name}`: {res.text}")
                        except Exception as e:
                            error_count += 1
                            st.error(f"Error processing `{uploaded_file.name}`: {e}")
                        
                        progress_bar.progress((idx + 1) / total_files)
                    
                    status_placeholder.empty()
                    progress_bar.empty()
                    
                    if success_count > 0:
                        st.success(f"🎉 Successfully processed and indexed {success_count} of {total_files} resume(s) into Resume Pool!")
                        st.rerun()


    with col_report:
        with st.container(border=True):
            st.markdown("""
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
            raw_cname = r.get("candidate_name") if isinstance(r, dict) else None
            cname = str(raw_cname).strip() if raw_cname else "Unknown Candidate"
            if not cname or cname == "None":
                cname = "Unknown Candidate"
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

            # Candidate Card Row with 1-Click Delete Action Button
            c_info, c_action = st.columns([8.5, 1.5])
            with c_info:
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
            with c_action:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"btn_delete_main_{rid}", use_container_width=True, help=f"Delete '{cname}' from SQLite DB & Vector Index"):
                    with st.spinner(f"Deleting '{cname}' from DB & Vector Index..."):
                        rs_service.delete_resume(rid)
                        vs_service.delete_resume(rid)
                        st.success(f"Deleted candidate '{cname}'!")
                        st.rerun()

            with st.expander(f"🔍 View Extracted Profile & Data ({cname})"):
                st.markdown(f"**Candidate Summary:** {summary}")
                if skills:
                    skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
                    st.markdown(f"**Technical Skills:** `{skills_str}`")
                
                st.markdown("**Parsed JSON Profile:**")
                st.json(prof_dict)
                
                if st.button(f"🗑️ Purge Candidate Record ({cname})", key=f"btn_del_res_{rid}"):
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

                    raw_name = profile.get("candidate_name") if isinstance(profile, dict) else None
                    name = str(raw_name).strip() if raw_name else "Unknown Candidate"
                    if not name or name == "None":
                        name = "Unknown Candidate"
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

