from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import re
import json
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from typing import cast

# static_folder/static_url_path expose files in ./static at /static/<file>.
# The logo and favicon live there so the browser can fetch them over HTTP
# (Flask handles caching/304s automatically).
app = Flask(__name__, static_folder="static", static_url_path="/static")

# Load environment variables
load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=API_KEY)

# Create model once
model = genai.GenerativeModel(MODEL_NAME)


# LEGACY: clean_script strips markdown (# and *) and collapses blank lines.
# It is still used for FLOWCHART step parsing only (generate_explanation),
# where we want plain numbered headings. It must NOT be used on the prep plan
# anymore — the plan is now structured JSON. Remove this helper once the
# JSON-based plan system has been stable in production.
def clean_script(script):
    script = re.sub(r"[#*]", "", script)
    script = re.sub(r"\n+", "\n", script).strip()
    return script


def generate_explanation(topic, level):
    prompt = (
        f"Generate a step-by-step approach on the topic '{topic}' "
        f"for a person at '{level}' level. "
        f"Return only numbered headings (1,2,3,...) without explanations. "
        f"This output will be used to create a flowchart."
    )

    try:
        response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text:
            return clean_script(response.text)

        return "Error: No valid response from Gemini."

    except Exception as e:
        return f"API Error: {str(e)}"


def _normalize_steps(steps):
    """Coerce the incoming steps (string or list) into a clean list of
    non-empty step strings."""
    if isinstance(steps, str):
        return [s.strip() for s in steps.split("\n") if s.strip()]
    return [str(s).strip() for s in (steps or []) if str(s).strip()]


def build_even_distribution(topic, steps_list, days):
    """Deterministic fallback: split steps as evenly as possible across N days.

    Always produces exactly `days` day-entries. Days that receive no steps are
    NOT dropped — they become "Revision / Buffer" days so the pie chart and
    text plan always show every day and stay consistent.

    Returns the canonical plan structure (topic, total_steps, days[]).
    """
    days = max(1, int(days))
    num_steps = len(steps_list)

    # Contiguous near-even chunks: the first (num_steps % days) days get one
    # extra step. Keeps step order intact (better than round-robin for reading).
    base, extra = divmod(num_steps, days) if days else (0, 0)

    day_entries = []
    cursor = 0
    for d in range(1, days + 1):
        take = base + (1 if d <= extra else 0)
        chunk = steps_list[cursor:cursor + take]
        cursor += take

        if chunk:
            day_entries.append({
                "day": d,
                "title": f"Day {d}",
                "steps": chunk,
                "focus": "Learn and practice the listed steps.",
            })
        else:
            # No steps left for this day — keep it as a buffer day.
            day_entries.append({
                "day": d,
                "title": f"Day {d} — Revision / Buffer",
                "steps": [],
                "focus": "Revision / Buffer",
            })

    return {
        "topic": topic,
        "total_steps": num_steps,
        "days": day_entries,
    }


def _extract_json(text):
    """Pull a JSON object out of an LLM response that may be wrapped in
    ```json fences or surrounded by prose. Returns a dict or None."""
    if not text:
        return None

    candidate = text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()

    # Fall back to the first {...} block.
    if not candidate.startswith("{"):
        brace = re.search(r"\{.*\}", candidate, re.DOTALL)
        if brace:
            candidate = brace.group(0)

    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, TypeError):
        return None


def _validate_plan(plan, topic, steps_list, days):
    """Validate that an AI-produced plan matches the canonical schema and is
    internally consistent. Returns a normalized plan dict on success, else None.
    """
    if not isinstance(plan, dict):
        return None

    day_items = plan.get("days")
    if not isinstance(day_items, list) or len(day_items) != int(days):
        return None

    # Normalized lookup of valid source steps for membership checks.
    valid_steps = {s.strip().lower() for s in steps_list}

    normalized_days = []
    for idx, item in enumerate(day_items, start=1):
        if not isinstance(item, dict):
            return None

        # Day index must be present and sequential (1..N).
        if int(item.get("day", idx)) != idx:
            return None

        raw_steps = item.get("steps", [])
        if not isinstance(raw_steps, list):
            return None

        # Every referenced step must exist in the source steps (normalized).
        clean_day_steps = [str(s).strip() for s in raw_steps if str(s).strip()]
        for s in clean_day_steps:
            if s.lower() not in valid_steps:
                return None

        title = str(item.get("title") or f"Day {idx}").strip()
        focus = str(item.get("focus") or "").strip()

        # Keep zero-step days as buffer days (never drop them).
        if not clean_day_steps:
            title = title or f"Day {idx} — Revision / Buffer"
            focus = focus or "Revision / Buffer"

        normalized_days.append({
            "day": idx,
            "title": title,
            "steps": clean_day_steps,
            "focus": focus,
        })

    return {
        "topic": topic,
        "total_steps": len(steps_list),
        "days": normalized_days,
    }


def generate_prep_plan(topic, level, steps, days):
    """Produce a deterministic, structured study plan.

    Returns the canonical schema:
        {"topic", "total_steps", "days": [{day, title, steps[], focus}], "source"}

    Strategy: ask Gemini for strict JSON and validate it. If the response is
    missing, malformed, or fails validation, fall back to a pure-Python even
    distribution so the plan ALWAYS renders.
    """
    steps_list = _normalize_steps(steps)
    num_steps = len(steps_list)
    days = int(days)

    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps_list))

    prompt = (
        f"You are creating a {days}-day study plan for learning '{topic}' "
        f"at '{level}' level.\n\n"
        f"Distribute these {num_steps} learning steps across exactly {days} "
        f"days:\n{numbered}\n\n"
        f"Return ONLY valid JSON (no prose, no markdown) with this exact shape:\n"
        f'{{\n'
        f'  "topic": "{topic}",\n'
        f'  "total_steps": {num_steps},\n'
        f'  "days": [\n'
        f'    {{"day": 1, "title": "short title", '
        f'"steps": ["exact step text", ...], "focus": "one-line focus"}}\n'
        f'  ]\n'
        f'}}\n\n'
        f"Rules:\n"
        f"- Produce exactly {days} day objects, numbered 1 to {days}.\n"
        f"- Use the EXACT step text from the list above inside \"steps\".\n"
        f"- If there are more days than steps, leave the extra days' \"steps\" "
        f"empty and set their focus to \"Revision / Buffer\".\n"
        f"- Distribute steps in order, as evenly as possible."
    )

    # Prefer strict JSON output where the SDK supports it.
    generation_config = None
    try:
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
    except Exception:
        generation_config = None

    try:
        if generation_config is not None:
            response = model.generate_content(
                prompt, generation_config=generation_config
            )
        else:
            response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text:
            parsed = _extract_json(response.text)
            validated = _validate_plan(parsed, topic, steps_list, days)
            if validated is not None:
                validated["source"] = "ai"
                return validated

    except Exception:
        # Any API/parse error falls through to the deterministic fallback.
        pass

    fallback = build_even_distribution(topic, steps_list, days)
    fallback["source"] = "fallback"
    return fallback


VALID_MERMAID_TYPES = [
    "graph TD",
    "graph LR",
    "graph BT",
    "graph RL",
    "graph TB",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "journey",
    "gantt",
    "pie",
]


def is_valid_mermaid_code(code):
    return any(code.strip().startswith(t) for t in VALID_MERMAID_TYPES)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate_flowchart", methods=["POST"])
def generate_flowchart():
    data = request.get_json() or {}

    topic = data.get("topic")
    level = data.get("level")

    if not topic or not level:
        return jsonify({"error": "Missing topic or level"}), 400

    steps = generate_explanation(topic, level)

    return jsonify({"steps": steps})


@app.route("/generate_prep_plan", methods=["POST"])
def generate_prep_plan_route():
    data = request.get_json() or {}

    topic = data.get("topic")
    level = data.get("level")
    steps = data.get("steps")
    days = data.get("days")

    if not all([topic, level, steps, days]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        days = int(days)

        if days <= 0:
            return jsonify({"error": "Days must be positive"}), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Days must be a number"}), 400

    plan = generate_prep_plan(topic, level, steps, days)

    return jsonify({"plan": plan})


# DEGRADED-MODE FALLBACK ONLY. This route renders Mermaid to SVG server-side
# via headless Chrome (Selenium). It is heavy and slow and must NOT be part of
# the normal rendering flow — the client renders Mermaid directly. The frontend
# only calls this as a last resort if client-side mermaid.render() throws
# completely. Kept intact for safety/degraded environments.
@app.route("/render_mermaid_svg", methods=["POST"])
def render_mermaid_svg():
    data = request.get_json() or {}

    mermaid_code = data.get("code", "")
    topic = data.get("topic")
    level = data.get("level")

    if not mermaid_code:
        return jsonify({"error": "No Mermaid code provided"}), 400

    if not is_valid_mermaid_code(mermaid_code):
        if topic and level:
            steps = generate_explanation(topic, level)

            steps_list = [
                step.strip()
                for step in steps.split("\n")
                if step.strip()
            ]

            mermaid_code = "graph TD\n"

            for i, step in enumerate(steps_list):
                clean_step = re.sub(
                    r"[^\w\s\-(),.]",
                    "",
                    step.strip()
                )

                mermaid_code += f'    step{i}["{clean_step}"]\n'

                if i < len(steps_list) - 1:
                    mermaid_code += f"    step{i} --> step{i + 1}\n"

            if not is_valid_mermaid_code(mermaid_code):
                return jsonify({
                    "error": "Failed to generate valid Mermaid code."
                }), 400

        else:
            return jsonify({
                "error": "Invalid Mermaid syntax."
            }), 400

    html_content = f"""
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.3.0/mermaid.min.js"></script>
    </head>
    <body>
        <div class="mermaid" id="m">
        {mermaid_code}
        </div>

        <script>
            mermaid.initialize({{ startOnLoad: true }});
        </script>
    </body>
    </html>
    """

    temp_file = "temp_mermaid.html"

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)

        driver.get("file://" + os.path.abspath(temp_file))

        time.sleep(2)

        svg_elem = driver.find_element(By.TAG_NAME, "svg")
        svg = svg_elem.get_attribute("outerHTML")

        return jsonify({"svg": svg})

    except Exception as e:
        return jsonify({
            "error": f"Failed to render SVG: {str(e)}"
        }), 500

    finally:
        try:
            driver.quit()
        except:
            pass

        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )