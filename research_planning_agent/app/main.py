import streamlit as st
import uuid
from langgraph.types import Command
from app.graph import build_graph
from app.reporting import save_report
from app.config import settings

st.set_page_config(page_title="Research & Planning Agent", page_icon="🔎", layout="wide")
st.title("🔎 General-Purpose Research & Planning Agent")
st.caption("LangGraph · parallel research · source-backed synthesis · reflection · optional human approval")

with st.sidebar:
    st.subheader("Configuration")
    st.write(f"**LLM:** `{settings.llm_provider}`")
    st.write(f"**Search:** `{settings.search_provider}`")
    st.write(f"**Reflection limit:** {settings.max_reflection_loops}")
    st.info("For best results, configure a real LLM and (optionally) a Tavily API key in .env. Mock mode is for setup/testing.")

question = st.text_area("What would you like to research or plan?", height=150,
    placeholder="Example: Compare cloud certifications for a beginner and create a 12-week study roadmap.")
approval = st.checkbox("Pause for my approval before starting web research", value=settings.require_human_approval)
if "agent_graph" not in st.session_state:
    st.session_state.agent_graph = build_graph()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if st.button("Start research", type="primary", disabled=not question.strip()):
    st.session_state.question = question.strip()
    st.session_state.pending = True
    initial = {"question": question.strip(), "findings": [], "iteration": 0,
               "max_iterations": settings.max_reflection_loops,
               "approval_required": approval, "approved": not approval}
    with st.spinner("Planning and researching..."):
        st.session_state.result = st.session_state.agent_graph.invoke(initial,
            config={"configurable": {"thread_id": st.session_state.thread_id}})

if st.session_state.get("pending"):
    state = st.session_state.agent_graph.get_state({"configurable": {"thread_id": st.session_state.thread_id}})
    if state and state.tasks and any(getattr(t, "interrupts", None) for t in state.tasks):
        st.subheader("Review research plan")
        current = state.values.get("plan", [])
        for i, step in enumerate(current, 1): st.write(f"{i}. **{step.get('title')}** — `{step.get('query')}`")
        c1, c2 = st.columns(2)
        if c1.button("Approve and continue", type="primary"):
            with st.spinner("Researching and writing report..."):
                st.session_state.result = st.session_state.agent_graph.invoke(Command(resume=True),
                    config={"configurable": {"thread_id": st.session_state.thread_id}})
            st.session_state.pending = False
            st.rerun()
        if c2.button("Cancel research"):
            st.session_state.result = st.session_state.agent_graph.invoke(Command(resume=False),
                config={"configurable": {"thread_id": st.session_state.thread_id}})
            st.session_state.pending = False
            st.rerun()
    else:
        st.session_state.pending = False

result = st.session_state.get("result")
if result:
    st.divider()
    if result.get("status") == "cancelled":
        st.warning("Research was cancelled at the approval step.")
    else:
        st.subheader("Research plan")
        for i, step in enumerate(result.get("plan", []), 1): st.write(f"{i}. **{step.get('title')}** — {step.get('query')}")
        st.subheader("Report")
        st.markdown(result.get("report", "No report was generated."))
        with st.expander("Research findings and source snippets"):
            for finding in result.get("findings", []):
                st.markdown(f"**{finding.get('step')}** · `{finding.get('query')}`")
                if finding.get("error"): st.warning(finding["error"])
                for item in finding.get("results", []):
                    st.markdown(f"- [{item.get('title','Source')}]({item.get('url','')}) — {item.get('content','')}")
        path = save_report(st.session_state.question, result.get("report", ""), result.get("findings", []))
        st.success(f"Saved report to `{path}`")
        st.download_button("Download Markdown report", path.read_bytes(), file_name=path.name, mime="text/markdown")
