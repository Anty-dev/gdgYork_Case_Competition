import os
import sys
import json
import time
from google import genai
from google.genai import types
from utils.report_formatter import build_report
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.environ.get("GEMINI_API_KEY", "your-key-here")
MODEL = "gemini-2.5-flash-lite"


SECURITY_PROMPT = """You are a security code review agent.
Find security vulnerabilities only: injections, hardcoded secrets, unsafe patterns,
path traversal, insecure deserialization, missing input validation, OWASP Top-10.

Severity: CRITICAL, HIGH, MEDIUM, LOW, INFO

Return ONLY this JSON:
{
  "agent": "security",
  "score": 5,
  "summary": "one sentence",
  "issues": [
    {"id": "SEC-001", "severity": "HIGH", "line": 12, "title": "...", "description": "...", "fix": "..."}
  ]
}"""

LOGIC_PROMPT = """You are a logic and correctness code review agent.
Find bugs only: off-by-one errors, null dereferences, division by zero,
unhandled edge cases, resource leaks, incorrect error handling.

Severity: CRITICAL, HIGH, MEDIUM, LOW, INFO

Return ONLY this JSON:
{
  "agent": "logic",
  "score": 7,
  "summary": "one sentence",
  "issues": [
    {"id": "LOG-001", "severity": "MEDIUM", "line": 34, "title": "...", "description": "...", "fix": "..."}
  ]
}"""

READABILITY_PROMPT = """You are a readability and maintainability code review agent.
Find clarity issues only: bad naming, missing docs, magic numbers,
long functions, deep nesting, code duplication.

Severity: HIGH, MEDIUM, LOW, INFO

Return ONLY this JSON:
{
  "agent": "readability",
  "score": 6,
  "summary": "one sentence",
  "issues": [
    {"id": "READ-001", "severity": "LOW", "line": 5, "title": "...", "description": "...", "fix": "..."}
  ],
  "positives": ["something done well"]
}"""

COORDINATOR_PROMPT = """You are a senior code review coordinator.
You receive findings from three specialized agents and synthesize them into a final report.

Your tasks:
- Deduplicate any overlapping issues across agents
- Rank the top 5 issues by severity and impact
- Compute overall_score = (security*0.45 + logic*0.32 + readability*0.23), rounded to 1 decimal
- Assign risk_level: CRITICAL (score<4 or any CRITICAL issue), HIGH (score<6 or any HIGH security),
  MEDIUM (score<7.5), LOW (otherwise)
- Recommend: APPROVE, REQUEST_CHANGES, or BLOCK

Return ONLY this JSON:
{
  "overall_score": 5.2,
  "risk_level": "HIGH",
  "recommendation": "REQUEST_CHANGES",
  "executive_summary": "3 sentence summary for a tech lead",
  "top_issues": [
    {"rank": 1, "agent": "security", "id": "SEC-001", "severity": "HIGH", "title": "...", "line": 12, "fix": "..."}
  ],
  "total_issues": 8,
  "issues_by_severity": {"CRITICAL": 0, "HIGH": 2, "MEDIUM": 3, "LOW": 3, "INFO": 0}
}"""


def call_agent(system_prompt: str, user_message: str) -> dict:
    """Send a prompt to Gemini and return parsed JSON."""
    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return json.loads(response.text)


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "sample_v.py"

    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    code_message = f"Review this code ({filepath}):\n\n```\n{code}\n```"

    print(f"\n Reviewing: {filepath}\n")

    print("Running Security Agent")
    security = call_agent(SECURITY_PROMPT, code_message)
    time.sleep(4)

    print("Running Logic Agent")
    logic = call_agent(LOGIC_PROMPT, code_message)
    time.sleep(4)

    print("Running Readability Agent")
    readability = call_agent(READABILITY_PROMPT, code_message)
    time.sleep(4)

    print("Running Coordinator Agent")
    coordinator_message = f"""Here are the findings from three agents reviewing {filepath}:

SECURITY AGENT:
{json.dumps(security, indent=2)}

LOGIC AGENT:
{json.dumps(logic, indent=2)}

READABILITY AGENT:
{json.dumps(readability, indent=2)}

Synthesize these into the final report."""

    final_report = call_agent(COORDINATOR_PROMPT, coordinator_message)

    # Attach per-agent details for the report formatter
    final_report["agents"] = {
        "security": security,
        "logic": logic,
        "readability": readability,
    }

    md = build_report(final_report, filepath)
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n Report saved to report.md")
    print(f" Score    : {final_report['overall_score']} / 10")
    print(f" Risk     : {final_report['risk_level']}")
    print(f" Decision : {final_report['recommendation']}")
    print(f" Issues   : {final_report['total_issues']}\n")