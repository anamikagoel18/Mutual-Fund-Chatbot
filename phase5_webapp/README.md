# Phase 5: Web Application Instructions

This phase contains the full-stack implementation of the Mutual Fund RAG Chatbot.

## 1. Backend (FastAPI)
The backend serves as the API for the RAG engine.

### Prerequisites
- Python 3.9+
- A valid `.env` file in the project root with `GOOGLE_API_KEY`.

### Steps to Run
1. Navigate to the backend directory:
   ```bash
   cd phase5_webapp/backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`.

## 2. Frontend (React Dashboard)
The frontend is a premium dark-themed dashboard built with React and Tailwind CSS.

### Project Structure
- `app.jsx`: Main React component.
- `styles.css`: Deep midnight theme and glassmorphic styles.

### How to Preview
For a quick preview, you can host the files using a local development server or integrate them into a Next.js/Vite project.

1. Ensure the backend is running.
2. Open the frontend in a browser (e.g., using VS Code Live Server extension on a generated `index.html`).

## 3. Key Features
- **Premium Aesthetics**: Midnight Navy palette with Lucide-style icons.
- **Real-time Interaction**: Direct chat with the RAG engine.
- **Factual citations**: Automatically links to official source URLs.
- **Guardrail Integration**: PII and advisory filtering are active at the API level.
