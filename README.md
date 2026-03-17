# Mutual Fund Chatbot Setup

This document provides instructions for setting up the `GEMINI_API_KEY` in different environments.

## API Key Configuration

The application requires a `GEMINI_API_KEY` to function. It uses a hybrid loading strategy:
1. It first tries to read from **Streamlit Secrets**.
2. If not found, it falls back to **System Environment Variables**.

### 1. Local Development Support

For local runs using `streamlit run streamlit_app.py`:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="AIzaSyD0gaVkCIp1EfqbkKM_9BclqKaczXgiiEA"
streamlit run streamlit_app.py
```

**MacOS / Linux:**
```bash
export GEMINI_API_KEY="AIzaSyD0gaVkCIp1EfqbkKM_9BclqKaczXgiiEA"
streamlit run streamlit_app.py
```

### 2. Streamlit Cloud Deployment

When deploying to [Streamlit Cloud](https://streamlit.io/cloud):

1. Go to your **App Dashboard**.
2. Click on **Settings** > **Secrets**.
3. Add the following entry:
```toml
GEMINI_API_KEY = "AIzaSyD0gaVkCIp1EfqbkKM_9BclqKaczXgiiEA"
```

### 3. Safety Check

If the API key is not set, the application will raise a clear error message:
`"GEMINI_API_KEY is not set. Please configure it using environment variables or Streamlit Secrets."`
