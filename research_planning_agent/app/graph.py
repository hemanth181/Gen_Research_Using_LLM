from __future__ import annotations
import json, operator, sqlite3, uuid
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt
from langgraph.checkpoint.sqlite import SqliteSaver
from app.config import settings
from app.llm import get_chat_model, invoke_text
from app.search import search_web

class AgentState(TypedDict, total=False):
    question: str
    plan: list[dict]
    pending_steps: list[dict]
    findings: Annotated[list[dict], operator.add]
    report: str
    critique: str
    gaps: list[str]
    iteration: int
    max_iterations: int
    approval_required: bool
    approved: bool
    status: str


def _json_from_text(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"): text = text[4:]
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end+1])
    raise ValueError("Model did not return a JSON array")


def build_graph(checkpointer=None):
    model = get_chat_model()
    if checkpointer is None:
        connection = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        checkpointer = SqliteSaver(connection)
        checkpointer.setup()

    def plan_node(state: AgentState):
        prompt = ("You are a domain-independent research planner. Break the user's request into 3-5 "
                  "independent, searchable research steps. Return ONLY a JSON array of objects with "
                  "title and query string fields. Avoid duplicate queries.\nUSER REQUEST:\n" + state["question"])
        try:
            plan = _json_from_text(invoke_text(model, prompt))
        except Exception:
            plan = [{"title": "Background and context", "query": state["question"] + " overview"},
                    {"title": "Evidence and data", "query": state["question"] + " evidence data"},
                    {"title": "Options and recommendations", "query": state["question"] + " options recommendations"}]
        plan = [x for x in plan if isinstance(x, dict) and x.get("query")][:settings.max_research_steps]
        return {"plan": plan, "pending_steps": plan, "iteration": state.get("iteration", 0), "status": "plan_ready"}

    def approval_gate(state: AgentState):
        if not state.get("approval_required", False):
            return {"approved": True, "status": "researching"}
        decision = interrupt({"message": "Review the research plan before search begins.", "plan": state.get("plan", [])})
        return {"approved": bool(decision), "status": "researching" if decision else "cancelled"}

    def route_after_approval(state: AgentState):
        if not state.get("approved", False): return END
        return [Send("research_step", {"step": step, "question": state["question"]})
                for step in state.get("pending_steps", [])]

    def research_step(state: dict):
        step = state["step"]
        try:
            results = search_web(step["query"], max_results=5)
            error = None
        except Exception as exc:
            results, error = [], str(exc)
        return {"findings": [{"step": step.get("title", "Research"), "query": step["query"],
                              "results": results, "error": error}]}

    def synthesize(state: AgentState):
        evidence = json.dumps(state.get("findings", []), ensure_ascii=False, indent=2)
        prompt = ("Create a useful, structured research report for the user's request. Include an executive "
                  "summary, key findings, analysis, uncertainties/limitations, and a practical numbered action plan. "
                  "Use ONLY supported claims from the supplied research; cite sources inline as [n] and provide a "
                  "Sources list with title and URL. Explicitly flag missing evidence.\nREQUEST:\n" + state["question"] +
                  "\nRESEARCH EVIDENCE:\n" + evidence)
        report = invoke_text(model, prompt)
        return {"report": report, "status": "drafted"}

    def critique(state: AgentState):
        prompt = ("Review this research report for important unanswered questions or missing evidence. "
                  "Return ONLY JSON with keys needs_more_research (boolean) and gaps (array of short strings). "
                  "Only request more research when a meaningful gap can be searched.\nREPORT:\n" + state.get("report", ""))
        try:
            raw = invoke_text(model, prompt)
            data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        except Exception:
            data = {"needs_more_research": False, "gaps": []}
        more = bool(data.get("needs_more_research")) and state.get("iteration", 0) < state.get("max_iterations", 0)
        return {"critique": json.dumps(data), "gaps": data.get("gaps", []), "_needs_more": more,
                "status": "reflection" if more else "complete"}

    def route_after_critique(state: AgentState):
        return "revise_plan" if state.get("_needs_more", False) else END

    def revise_plan(state: AgentState):
        gaps = state.get("gaps", [])
        steps = [{"title": f"Follow-up: {g[:70]}", "query": g} for g in gaps[:settings.max_research_steps]]
        return {"pending_steps": steps, "iteration": state.get("iteration", 0) + 1}

    builder = StateGraph(AgentState)
    builder.add_node("plan", plan_node)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node("research_step", research_step)
    builder.add_node("synthesize", synthesize)
    builder.add_node("critique", critique)
    builder.add_node("revise_plan", revise_plan)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "approval_gate")
    builder.add_conditional_edges("approval_gate", route_after_approval)
    builder.add_edge("research_step", "synthesize")
    builder.add_edge("synthesize", "critique")
    builder.add_conditional_edges("critique", route_after_critique)
    builder.add_conditional_edges("revise_plan", lambda s: [Send("research_step", {"step": step, "question": s["question"]}) for step in s.get("pending_steps", [])])
    return builder.compile(checkpointer=checkpointer)


def run_research(question: str, approval_required: bool = False, approved: bool = True):
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial = {"question": question, "findings": [], "iteration": 0,
               "max_iterations": settings.max_reflection_loops,
               "approval_required": approval_required, "approved": approved}
    return graph.invoke(initial, config=config)
