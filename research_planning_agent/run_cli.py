import argparse
from app.graph import run_research
from app.reporting import save_report

def main():
    parser = argparse.ArgumentParser(description="General-purpose LangGraph research and planning agent")
    parser.add_argument("question", nargs="+", help="Research question or planning goal")
    args = parser.parse_args()
    question = " ".join(args.question)
    result = run_research(question)
    print("\n" + result.get("report", "No report generated.") + "\n")
    print(f"Report saved: {save_report(question, result.get('report',''), result.get('findings', []))}")

if __name__ == "__main__": main()
