# 🎓 Learning Path Generator

[![Flask](https://img.shields.io/badge/Flask-3.0.0-blue.svg)](https://flask.palletsprojects.com/)
[![Google Generative AI](https://img.shields.io/badge/Google%20Generative%20AI-Latest-green.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful, AI-driven web application that generates personalized learning paths and study schedules using Google's Generative AI technology.

## ✨ Features

- 🔍 **Smart Learning Path Generation**: Creates step-by-step learning paths for any topic
- 📊 **Interactive Flowcharts**: Visualizes learning steps using Mermaid.js diagrams (smooth, single-pass rendering)
- 📅 **Custom Study Plans**: Generates personalized daily study schedules
- 📈 **Reliable Visual Analytics**: Pie chart of daily task distribution that **always renders** — driven by validated structured data, never fragile text parsing
- 🎯 **Multi-Level Support**: Adapts content for Beginner, Intermediate, and Expert levels
- 🖼️ **Branded UI**: Logo served from `/static`, responsive and clean across devices

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Learning-Path-Generator.git
cd Learning-Path-Generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
- Create a `.env` file in the root directory
- Add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python app.py
```

## 💻 Technologies Used

- **Backend**: Flask (Python)
- **AI**: Google Generative AI (Gemini 2.5 Flash)
- **Frontend**: HTML, CSS, JavaScript
- **Visualization**: Mermaid.js (flowchart + pie chart)
- **Styling**: Font Awesome, Custom CSS
- **Static assets**: Served from `static/` (logo, favicon)
- **Optional fallback**: Selenium + headless Chrome for server-side SVG (degraded mode only)

## 🌟 Key Features Explained

### AI-Powered Learning Paths
- Generates detailed, step-by-step learning paths
- Adapts content based on user's expertise level
- Provides structured progression through topics

### Dynamic Study Planning
- Converts learning paths into daily schedules
- Optimizes task distribution based on available time
- Provides both visual and text-based plan views
- **Buffer days**: when you allow more days than there are steps, extra days are shown as clearly labelled "Revision / Buffer" days — never dropped

### Interactive Visualization
- Flowchart representation of learning steps
- Pie chart visualization of daily task distribution
- Responsive and mobile-friendly design

## 🧱 Design Notes (Reliability)

The study plan is generated as **structured JSON** with a fixed schema and validated on the server before it reaches the browser:

```json
{
  "topic": "string",
  "total_steps": 0,
  "days": [
    { "day": 1, "title": "string", "steps": ["..."], "focus": "string" }
  ]
}
```

- **Deterministic rendering**: Both the pie chart and the text plan are built from this same validated object — not from regex-parsing free-form AI prose. This eliminates the intermittent "chart didn't render" failures.
- **Fallback**: If the AI response is missing or malformed, the backend builds an even step-per-day distribution in pure Python, so a plan **always** renders.
- **Smooth flowchart**: Mermaid runs with `startOnLoad: false` and is rendered manually with unique render ids, removing double-render flicker.
- **Security**: All AI-generated text is HTML-escaped before insertion into the DOM.

## 🛠️ Technical Architecture

```
Edu_Flowchart/
├── app.py              # Flask app, AI integration, JSON plan generation + validation
├── templates/
│   └── index.html      # Frontend (HTML + CSS + JS, Mermaid rendering)
├── static/             # Served at /static
│   ├── Edu_Flowchart_Logo.png
│   └── favicon.ico
├── requirements.txt    # Project dependencies
├── runtime.txt         # Python version (deploy)
├── Procfile            # Process definition (deploy)
└── .env                # Environment variables (GOOGLE_API_KEY, PORT)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Generative AI for providing the AI capabilities
- Mermaid.js for flowchart visualizations
- Flask community for the excellent web framework