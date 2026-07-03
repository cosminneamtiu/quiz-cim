# CIM Quiz Lab

Open `index.html` directly in a browser, or run a small local server from this folder:

```powershell
python -m http.server 8080
```

Then visit `http://localhost:8080`.

The quiz data is bundled in `quiz-data.js`. Rebuild the main question bank with `python ..\build_quiz_json.py`, then regenerate this bundle from the project root if the source quiz JSON changes.
