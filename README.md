# 🎓 Learning Path Generator

[![Flask](https://img.shields.io/badge/Flask-3.0.0-blue.svg)](https://flask.palletsprojects.com/)
[![Google Generative AI](https://img.shields.io/badge/Google%20Generative%20AI-Latest-green.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful, AI-driven web application that generates personalized learning paths and study schedules using Google's Generative AI technology.

## ✨ Features

- 🔍 **Smart Learning Path Generation**: Creates step-by-step learning paths for any topic
- 📊 **Interactive Flowcharts**: Visualizes learning steps using Mermaid.js diagrams
- 📅 **Custom Study Plans**: Generates personalized daily study schedules
- 📈 **Visual Analytics**: Displays task distribution through interactive pie charts
- 🎯 **Multi-Level Support**: Adapts content for Beginner, Intermediate, and Expert levels

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
- **AI**: Google Generative AI (Gemini 1.5 Pro)
- **Frontend**: HTML, CSS, JavaScript
- **Visualization**: Mermaid.js
- **Styling**: Font Awesome, Custom CSS

## 🌟 Key Features Explained

### AI-Powered Learning Paths
- Generates detailed, step-by-step learning paths
- Adapts content based on user's expertise level
- Provides structured progression through topics

### Dynamic Study Planning
- Converts learning paths into daily schedules
- Optimizes task distribution based on available time
- Provides both visual and text-based plan views

### Interactive Visualization
- Flowchart representation of learning steps
- Pie chart visualization of daily task distribution
- Responsive and mobile-friendly design

## 🛠️ Technical Architecture

```
Learning-Path-Generator/
├── app.py              # Flask application & AI integration
├── templates/          # Frontend templates
│   └── index.html     # Main application interface
├── requirements.txt    # Project dependencies
└── .env               # Environment variables
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Generative AI for providing the AI capabilities
- Mermaid.js for flowchart visualizations
- Flask community for the excellent web framework