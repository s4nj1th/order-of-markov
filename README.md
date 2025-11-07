<div align="center">
    <img src="frontend/public/favicon.png" width="150"/>
    <h1>Order of Markov</h1>
    <p>Order of Markov is a lovingly over‑engineered experiment that uses a LLM to solve basic questions that can be answered by thinking for a couple of minutes.</p>
</div>

## Why this exists

Because sometimes the most educational thing you can do is be a little ridiculous. This project is an experiment to see how far we can push large language models on tiny, well-defined tasks: can we get them to pick a single integer (1–5) that represents the "right" Markov order, and how many resources will that consume along the way? Expect inconsistent answers, amusing justifications, and wasted compute. The point is not efficiency, it's curiosity and a mild stress test of how easily LLMs can be shoehorned into trivial decision-making.

## What this does

- The frontend (Vite + React + TypeScript) sends a short problem description to the backend.
- The backend (FastAPI) asks an LLM which Markov order (1–5) best fits the problem and returns a tiny JSON answer: order, justification, confidence.

## Quickstart (dev)

### 1. Backend

- Ensure you have Python 3.10+ and a virtual environment. From the `backend/`folder:

  ```bash
  cd backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

- Create a `.env` (or export) with your OpenRouter API key:

  ```bash
  export OPENROUTER_API_KEY="sk-..."
  # optional: export OPENROUTER_API_BASE (defaults to https://openrouter.ai)
  ```

- Run the API locally:
  ```bash
  uvicorn main:app --reload
  ```

The backend will be available at http://localhost:8000 and exposes `/api/analyze`.

### 2. Frontend

- From the `frontend/` folder (Node 18+ recommended):

  ```bash
  cd frontend
  npm install
  npm run dev
  ```

- Open the app in the browser (Vite will print the URL). The UI is tiny, keyboard-friendly (Cmd/Ctrl+Enter to submit), and theme-aware.

## Testing the API directly

If you want to skip the UI and poke the backend directly, this curl will do it (replace the API key or set it in the environment):

```bash
curl -i -X POST http://localhost:8000/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"problem": "predicting the next word in a sentence"}'
```

## What to expect

- A successful response is JSON with keys: `order` (1–5), `justification` (short string), and `confidence` (0–1).
- If the backend cannot reach the LLM or the response is malformed, the server will return a verbose error that should help you debug (it prints URL, status, and response snippets).

## Troubleshooting

- If you see DNS or network errors from the backend, check `OPENROUTER_API_KEY` and whether the host running the backend can access the internet or needs proxy configuration.
- If Tailwind utilities in the frontend look unprocessed in your editor, restart the Vite dev server after `npm install` so PostCSS/Tailwind plugins are picked up.

That's it. Tinker, break, and then tell the LLM what you think it should have answered.

License: [MIT](./LICENSE)
