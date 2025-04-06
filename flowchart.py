from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import re

app = Flask(__name__)

# Configure API key (Replace with actual API Key)
genai.configure(api_key="AIzaSyCKe2NbapZ4R3Gj9w9IQN1XT1mBC1TDbbY")


def generate_explanation(topic, level):
    prompt = (
        f"Generate a step-by-step approach on the Topic {topic} "
        f"for a person at {level} level. It should be in numbered points "
        f"(1,2,3,...), only headings, no explanations. This is for a flowchart."
    )

    try:
        response = genai.GenerativeModel("gemini-1.5-pro-latest").generate_content(
            prompt
        )
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
        response = genai.GenerativeModel("gemini-1.5-pro-latest").generate_content(
            prompt
        )
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


if __name__ == "__main__":
    app.run(debug=True)
