# Touch Grass 🌿

**Touch Grass** is an AI-powered outdoor adventure app designed to encourage people to step away from their phones and explore the world around them. It generates outdoor missions that encourage observation, curiosity, and real-world exploration.

## ✨ Features

- **AI-generated missions:** Create outdoor adventures with the help of a locally running AI model.
- **Progressive clues:** Receive clues that guide you through an exploration step by step.
- **Observation-based progression:** Clues encourage you to notice and examine details in your surroundings.
- **Phone-free exploration:** Designed to encourage users to focus on the outdoors instead of their screens.
- **Local AI:** Uses Ollama to run the Qwen3 4B model locally.

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| AI inference | Ollama, Qwen3 4B |
| Testing | Pytest |

## 📁 Project Structure

```text
touch-grass/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   ├── tests/
│   └── main.py
└── frontend/
    ├── src/
    ├── public/
    └── package.json
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or a compatible version
- Node.js and npm
- Ollama installed locally
- Git

### 1. Clone the repository

```bash
git clone https://github.com/anmolchaudhary617-ux/touch-grass.git
cd touch-grass
```

### 2. Set up the AI model

Install Ollama from [ollama.com](https://ollama.com/) and run:

```bash
ollama pull qwen3:4b
```

Ensure Ollama is running before using AI-powered features.

### 3. Start the backend

Open a terminal:

```bash
cd backend
python -m venv venv
```

Activate the environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend will typically run at `http://127.0.0.1:8000`. If your project uses a different application entry point, follow the configuration in the backend.

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in your terminal.

## 🧪 Run Tests

From the backend directory, with the Python environment activated:

```bash
python -m pytest -q
```

## 🎯 Vision

Touch Grass aims to make outdoor exploration more engaging by turning ordinary surroundings into opportunities for discovery. Instead of constantly looking at a screen, users are encouraged to observe, explore, and reconnect with the world around them.

## 👨‍💻 Author

**Anmol Chaudhary**

GitHub: [@anmolchaudhary617-ux](https://github.com/anmolchaudhary617-ux)

---

Built for the Hacktoberfest Open-Source AI Challenge.
