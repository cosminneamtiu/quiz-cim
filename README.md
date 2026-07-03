# CIM Quiz Lab

A browser quiz app for practicing the CIM question bank.

## Run the quiz

### Windows

Double-click `run.bat`.

That opens the quiz in your default browser. No installation is needed.

### Any platform

Open this file in a browser:

```text
quiz_site/index.html
```

You can also run a small local web server from the `quiz_site` folder:

```powershell
cd quiz_site
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

## Using the quiz

- Choose a question pool.
- Choose 10, 20, 40, or all questions.
- Start the quiz and answer each question.
- Progress is saved in the browser on that computer.

To reset saved progress, use the `Reset` button in the quiz.

## Project files

- `run.bat` opens the quiz on Windows.
- `quiz_site/index.html` is the quiz app.
- `quiz_site/quiz-data.js` is the bundled question data used by the app.

The repository intentionally contains only the files needed to run the quiz.
