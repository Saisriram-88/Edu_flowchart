from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import re
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

# Load environment variables
load_dotenv()
Model = "gemini-2.5-flash"
# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_explanation(topic, level):
    prompt = (
        f"Generate a step-by-step approach on the Topic {topic} "
        f"for a person at {level} level. It should be in numbered points "
        f"(1,2,3,...), only headings, no explanations. This is for a flowchart."
    )

    try:
        response = genai.GenerativeModel(Model).generate_content(prompt)
        if response and response.text:
            return clean_script(response.text)
        else:
            return "Error: No valid response from Gemini AI."
    except Exception as e:
        return f"API Error: {e}"


def generate_prep_plan(topic, level, steps, days):
    # Convert steps to list if it's a string
    if isinstance(steps, str):
        steps_list = steps.strip().split("\n")
    else:
        steps_list = steps

    num_steps = len(steps_list)

    prompt = (
        f"Create a {days}-day preparation plan for learning {topic} at {level} level. "
        f"The learning path has {num_steps} steps as follows: {steps_list}. "
        f"Distribute these steps across {days} days, showing which steps to focus on each day. "
        f"Format the response as 'Day X: Step Y' or 'Day X: Steps Y, Z' for each day. "
        f"Be practical about time allocation and ensure exact step numbers are used."
    )

    try:
        response = genai.GenerativeModel(Model).generate_content(prompt)
        if response and response.text:
            return clean_script(response.text)
        else:
            return "Error: No valid response from Gemini AI."
    except Exception as e:
        return f"API Error: {e}"


def clean_script(script):
    script = re.sub(r"[#*]", "", script)  # Remove markdown symbols
    script = re.sub(r"\n+", "\n", script).strip()  # Clean up newlines
    return script


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
    data = request.json
    topic = data.get("topic")
    level = data.get("level")

    if not topic or not level:
        return jsonify({"error": "Missing topic or level"}), 400

    steps = generate_explanation(topic, level)

    return jsonify({"steps": steps})


@app.route("/generate_prep_plan", methods=["POST"])
def generate_prep_plan_route():
    data = request.json
    topic = data.get("topic")
    level = data.get("level")
    steps = data.get("steps")
    days = data.get("days")

    if not all([topic, level, steps, days]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        days = int(days)
        if days <= 0:
            return jsonify({"error": "Days must be a positive number"}), 400
    except ValueError:
        return jsonify({"error": "Days must be a number"}), 400

    plan = generate_prep_plan(topic, level, steps, days)

    return jsonify({"plan": plan})


@app.route("/render_mermaid_svg", methods=["POST"])
def render_mermaid_svg():
    data = request.get_json()
    mermaid_code = data.get("code", "")
    topic = data.get("topic")
    level = data.get("level")
    # If not provided, fallback to empty string
    if not mermaid_code:
        return jsonify({"error": "No Mermaid code provided"}), 400

    # Validate Mermaid code
    if not is_valid_mermaid_code(mermaid_code):
        # Try to re-prompt Gemini if topic and level are provided
        if topic and level:
            steps = generate_explanation(topic, level)
            # Re-generate mermaid code from steps
            steps_list = steps.split("\n")
            mermaid_code = "graph TD\n"
            for i, step in enumerate(steps_list):
                clean_step = step.strip().replace(r"[^\w\s\-(),.]", "")
                mermaid_code += f'    step{i}["{clean_step}"]\n'
                if i < len(steps_list) - 1:
                    mermaid_code += f"    step{i}-->step{i + 1}\n"
            if not is_valid_mermaid_code(mermaid_code):
                return (
                    jsonify(
                        {
                            "error": "Gemini did not return valid Mermaid code. Please try again."
                        }
                    ),
                    400,
                )
        else:
            return (
                jsonify({"error": "Invalid Mermaid code syntax. Please try again."}),
                400,
            )

    html_content = f"""
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.3.0/mermaid.min.js"></script>
    </head>
    <body>
        <div class="mermaid" id="m">{mermaid_code}</div>
        <script>
            mermaid.initialize({{startOnLoad:true}});
        </script>
    </body>
    </html>
    """

    with open("temp_mermaid.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("file://" + os.path.abspath("temp_mermaid.html"))
    time.sleep(2)

    try:
        svg_elem = driver.find_element(By.TAG_NAME, "svg")
        svg = svg_elem.get_attribute("outerHTML")
        driver.quit()
        os.remove("temp_mermaid.html")
        return jsonify({"svg": svg})
    except Exception as e:
        driver.quit()
        os.remove("temp_mermaid.html")
        return jsonify({"error": f"Failed to render SVG: {str(e)}"}), 500


if __name__ == "__main__":
    # Get port from environment variable or default to 5000
    port = int(os.environ.get("PORT", 5000))
    # Run app with host set to '0.0.0.0' for deployment
    app.run(host="0.0.0.0", port=port, debug=False)
