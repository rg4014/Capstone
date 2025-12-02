import json
from typing import Dict, Any, List


# ============================================================
# 1. Load prompts from prompt.md
# ============================================================

def load_prompts(path: str = "prompt.md") -> Dict[str, str]:
    """
    Load prompts from a markdown file.
    Expects sections marked with ### TITLE.
    """
    sections = {}
    current_key = None
    buffer = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("###"):
                # save previous section
                if current_key:
                    sections[current_key] = "".join(buffer).strip()
                    buffer = []
                current_key = line.replace("###", "").strip()
            else:
                buffer.append(line)
        # save last one
        if current_key:
            sections[current_key] = "".join(buffer).strip()

    return sections


PROMPTS = load_prompts()


# ============================================================
# 2. Build user prompts with variable substitution
# ============================================================

def fill_template(template: str, **kwargs) -> str:
    """Simple format replacement for prompt templates."""
    return template.format(**kwargs)


def build_baseline_prompt(resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, str]:
    user_prompt = fill_template(
        PROMPTS["BASELINE_USER_PROMPT"],
        job_title=job.get("title", ""),
        job_company=job.get("company", ""),
        job_description=job.get("description", ""),
        degree_level=resume.get("degree_level", ""),
        major=resume.get("major", ""),
        school_tier=resume.get("school_tier", ""),
        gpa=resume.get("gpa", ""),
        years_experience=resume.get("years_experience", ""),
        skills_list=", ".join(resume.get("skills", [])),
    )

    return {
        "system": PROMPTS["BASELINE_SYSTEM_PROMPT"],
        "user": user_prompt
    }


def build_fair_prompt(resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, str]:
    user_prompt = fill_template(
        PROMPTS["FAIR_USER_PROMPT"],
        job_title=job.get("title", ""),
        job_company=job.get("company", ""),
        job_description=job.get("description", ""),
        name=resume.get("name", ""),
        contact=resume.get("contact", ""),
        education_block=resume.get("education_block", ""),
        work_experience_block=resume.get("work_experience", ""),
        skills_block=", ".join(resume.get("skills", [])),
        projects_block=resume.get("projects", ""),
        extracurriculars_block=resume.get("extracurriculars", ""),
    )

    return {
        "system": PROMPTS["FAIR_SYSTEM_PROMPT"],
        "user": user_prompt
    }


# ============================================================
# 3. LLM Call Wrapper (You plug your API here)
# ============================================================

def call_llm(system_msg: str, user_msg: str) -> str:
    """
    Replace this with your actual LLM API call.
    Example below is OpenAI format, you can replace with other vendors.
    """

    # ❗ Replace this with your API
    raise NotImplementedError("Plug your OpenAI/Anthropic/other API here.")

    """
    Example (for OpenAI):
    
    from openai import OpenAI
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
    )
    return response.choices[0].message["content"]
    """


# ============================================================
# 4. JSON Parsing (LLM output → dict)
# ============================================================

def parse_score(raw: str) -> Dict[str, Any]:
    """Extract JSON safely from model output."""
    txt = raw.strip()

    # handle ```json ... ```
    if txt.startswith("```"):
        txt = txt.strip("`")
        txt = txt.replace("json", "", 1).strip()

    try:
        data = json.loads(txt)
        return {
            "score": int(data.get("score", 0)),
            "decision": data.get("decision", ""),
            "reasoning": data.get("reasoning", "")
        }
    except Exception:
        print("⚠️ JSON parse error. Raw output shown below:")
        print(raw)
        return {
            "score": None,
            "decision": "",
            "reasoning": raw[:200]
        }


# ============================================================
# 5. Scoring Functions
# ============================================================

def score_baseline(resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    prompts = build_baseline_prompt(resume, job)
    raw = call_llm(prompts["system"], prompts["user"])
    return parse_score(raw)


def score_fair(resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    prompts = build_fair_prompt(resume, job)
    raw = call_llm(prompts["system"], prompts["user"])
    return parse_score(raw)


# ============================================================
# 6. Running Experiments (loop over many resumes)
# ============================================================

def run_experiment(resumes: List[Dict[str, Any]], job: Dict[str, Any]):
    results = []
    for r in resumes:
        baseline = score_baseline(r, job)
        fair = score_fair(r, job)
        pa = r.get("protected_attributes", {})

        results.append({
            "id": r.get("id"),
            "baseline_score": baseline["score"],
            "fair_score": fair["score"],
            "baseline_decision": baseline["decision"],
            "fair_decision": fair["decision"],
            "gender": pa.get("gender"),
            "race": pa.get("race"),
        })

    return results


# ============================================================
# 7. Example usage (safe to delete)
# ============================================================

if __name__ == "__main__":
    print("model_runner.py loaded. Ready to screen resumes.")
