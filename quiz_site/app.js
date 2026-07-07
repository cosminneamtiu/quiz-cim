(function () {
  const STORAGE_KEY = "cimQuizProgress.v1";
  const SESSION_KEY = "cimQuizSession.v1";
  const data = window.QUIZ_DATA || { questions: [] };
  const allQuestions = data.questions || [];

  const state = {
    selectedPool: "all",
    count: "10",
    questions: [],
    currentIndex: 0,
    score: 0,
    answered: [],
    selectedMissed: [],
  };

  const els = {
    bankSummary: document.getElementById("bankSummary"),
    metricTotal: document.getElementById("metricTotal"),
    metricScore: document.getElementById("metricScore"),
    metricProgress: document.getElementById("metricProgress"),
    poolSelect: document.getElementById("poolSelect"),
    countButtons: document.getElementById("countButtons"),
    shuffleToggle: document.getElementById("shuffleToggle"),
    startButton: document.getElementById("startButton"),
    questionView: document.getElementById("questionView"),
    resultsView: document.getElementById("resultsView"),
    questionCounter: document.getElementById("questionCounter"),
    progressFill: document.getElementById("progressFill"),
    questionSource: document.getElementById("questionSource"),
    questionText: document.getElementById("questionText"),
    optionsList: document.getElementById("optionsList"),
    feedbackPanel: document.getElementById("feedbackPanel"),
    submitButton: document.getElementById("submitButton"),
    nextButton: document.getElementById("nextButton"),
    finalScore: document.getElementById("finalScore"),
    finalSummary: document.getElementById("finalSummary"),
    missedReview: document.getElementById("missedReview"),
    retryMissedButton: document.getElementById("retryMissedButton"),
    newQuizButton: document.getElementById("newQuizButton"),
    progressAttempted: document.getElementById("progressAttempted"),
    progressMissed: document.getElementById("progressMissed"),
    progressAccuracy: document.getElementById("progressAccuracy"),
    progressSaved: document.getElementById("progressSaved"),
    reviewMissedButton: document.getElementById("reviewMissedButton"),
    clearProgressButton: document.getElementById("clearProgressButton"),
  };

  function emptyProgress() {
    return {
      version: 1,
      updatedAt: null,
      questions: {},
    };
  }

  function loadProgress() {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (!stored) return emptyProgress();
      const parsed = JSON.parse(stored);
      if (!parsed || parsed.version !== 1 || typeof parsed.questions !== "object") return emptyProgress();
      return parsed;
    } catch (error) {
      return emptyProgress();
    }
  }

  let progress = loadProgress();

  function saveProgress() {
    progress.updatedAt = new Date().toISOString();
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    } catch (error) {
      // Progress remains available for this tab even if browser storage is unavailable.
    }
  }

  function loadSession() {
    try {
      const stored = window.localStorage.getItem(SESSION_KEY);
      if (!stored) return null;
      const parsed = JSON.parse(stored);
      if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.questionKeys)) return null;
      return parsed;
    } catch (error) {
      return null;
    }
  }

  function clearSession() {
    try {
      window.localStorage.removeItem(SESSION_KEY);
    } catch (error) {
      // Ignore storage failures; the in-memory state is still authoritative.
    }
  }

  function normalize(text) {
    return String(text || "")
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function displayText(text) {
    return String(text || "").trim();
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function sourceLabel(question) {
    const pieces = [];
    if (question.course) pieces.push(question.course);
    if (question.quiz) pieces.push(question.quiz);
    if (question.source_file) pieces.push(question.source_file);
    return pieces.filter(Boolean).join(" | ") || "Quiz bank";
  }

  function sourceMeta(question) {
    const details = [question.source_file];
    if (question.source_page) details.push(`page ${question.source_page}`);
    if (question.source_line) details.push(`line ${question.source_line}`);
    return details.filter(Boolean).join(", ");
  }

  function sourceFile(question) {
    return String(question.source_file || "").replace(/\\/g, "/");
  }

  function isCourseQuestion(question) {
    return sourceFile(question).startsWith("cim courses/");
  }

  function isExamDumpQuestion(question) {
    return sourceFile(question).startsWith("exam questions dumps/");
  }

  function questionKey(question) {
    return String(question.id || normalize(question.question));
  }

  function findQuestionByKey(key) {
    return allQuestions.find((question) => questionKey(question) === key) || null;
  }

  function progressRecord(question) {
    return progress.questions[questionKey(question)] || null;
  }

  function isAttempted(question) {
    const record = progressRecord(question);
    return Boolean(record && record.attempts > 0);
  }

  function isMissed(question) {
    const record = progressRecord(question);
    return Boolean(record && record.missed);
  }

  function persistentMissedQuestions() {
    return allQuestions.filter(isMissed);
  }

  function unseenQuestions() {
    return allQuestions.filter((question) => !isAttempted(question));
  }

  function progressSummary() {
    return allQuestions.reduce(
      (summary, question) => {
        const record = progressRecord(question);
        if (!record || !record.attempts) return summary;
        summary.attempted += 1;
        summary.totalAttempts += record.attempts;
        summary.correctAttempts += record.correct || 0;
        if (record.missed) summary.missed += 1;
        return summary;
      },
      { attempted: 0, missed: 0, totalAttempts: 0, correctAttempts: 0 }
    );
  }

  function updateProgressPanel() {
    const summary = progressSummary();
    const accuracy = summary.totalAttempts
      ? Math.round((summary.correctAttempts / summary.totalAttempts) * 100)
      : 0;

    els.progressAttempted.textContent = String(summary.attempted);
    els.progressMissed.textContent = String(summary.missed);
    els.progressAccuracy.textContent = `${accuracy}%`;
    els.reviewMissedButton.disabled = summary.missed === 0;
    els.progressSaved.textContent = progress.updatedAt
      ? `Saved ${new Date(progress.updatedAt).toLocaleString()}`
      : "No progress saved yet";
  }

  function recordAttempt(result) {
    const key = questionKey(result.question);
    const previous = progress.questions[key] || {
      attempts: 0,
      correct: 0,
      wrong: 0,
      missed: false,
      lastCorrect: false,
      lastAnsweredAt: null,
      lastSelected: [],
      lastCorrectAnswers: [],
    };

    previous.attempts += 1;
    previous.correct += result.correct ? 1 : 0;
    previous.wrong += result.correct ? 0 : 1;
    previous.missed = !result.correct;
    previous.lastCorrect = result.correct;
    previous.lastAnsweredAt = new Date().toISOString();
    previous.lastSelected = result.selected.slice();
    previous.lastCorrectAnswers = result.correctOptions.slice();
    progress.questions[key] = previous;

    saveProgress();
    updateProgressPanel();
  }

  function resultSnapshot(result) {
    return {
      questionKey: questionKey(result.question),
      selected: result.selected.slice(),
      correctOptions: result.correctOptions.slice(),
      correct: result.correct,
    };
  }

  function hydrateResult(snapshot) {
    const question = findQuestionByKey(snapshot.questionKey);
    if (!question) return null;
    const result = {
      question,
      selected: Array.isArray(snapshot.selected) ? snapshot.selected : [],
      correctOptions: Array.isArray(snapshot.correctOptions)
        ? snapshot.correctOptions
        : getCorrectOptions(question),
      correct: Boolean(snapshot.correct),
      explanation: "",
    };
    result.explanation = buildExplanation(question, result);
    return result;
  }

  function saveSession() {
    if (!state.questions.length) {
      clearSession();
      return;
    }

    const payload = {
      version: 1,
      updatedAt: new Date().toISOString(),
      selectedPool: els.poolSelect.value,
      count: state.count,
      currentIndex: state.currentIndex,
      score: state.score,
      questionKeys: state.questions.map(questionKey),
      answered: state.answered.map(resultSnapshot),
    };

    try {
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(payload));
    } catch (error) {
      // If storage is full or unavailable, the current in-memory quiz still works.
    }
  }

  function restoreSession() {
    const session = loadSession();
    if (!session) return false;

    const questions = session.questionKeys.map(findQuestionByKey).filter(Boolean);
    if (!questions.length) {
      clearSession();
      return false;
    }

    state.questions = questions;
    state.currentIndex = Math.min(Math.max(Number(session.currentIndex) || 0, 0), questions.length - 1);
    state.score = Number(session.score) || 0;
    state.answered = (session.answered || []).map(hydrateResult).filter(Boolean);
    state.selectedMissed = [];
    state.count = session.count || state.count;

    const hasSavedPool = Array.from(els.poolSelect.options).some((option) => option.value === session.selectedPool);
    if (session.selectedPool && hasSavedPool) {
      els.poolSelect.value = session.selectedPool;
      state.selectedPool = session.selectedPool;
    }

    setActiveCountButton();
    els.resultsView.hidden = true;
    els.questionView.hidden = false;
    els.nextButton.hidden = true;
    els.submitButton.hidden = false;
    renderQuestion();
    updateMetrics();
    return true;
  }

  function optionMatchesAnswer(option, answer) {
    const opt = normalize(option);
    const ans = normalize(answer);
    if (!opt || !ans) return false;
    return answersEquivalent(option, answer) || ans.startsWith(`${opt} `) || opt.startsWith(`${ans} `);
  }

  function parseNumericAnswer(text) {
    const value = String(text || "")
      .trim()
      .replace(",", ".")
      .replace(/%$/, "");
    if (!/^-?\d+(?:\.\d+)?$/.test(value)) return null;
    return Number(value);
  }

  function answersEquivalent(left, right) {
    if (normalize(left) === normalize(right)) return true;
    const a = parseNumericAnswer(left);
    const b = parseNumericAnswer(right);
    return a !== null && b !== null && Math.abs(a - b) < 0.000001;
  }

  function getCorrectOptions(question) {
    const matches = question.options.filter((option) =>
      question.correct_answers.some((answer) => optionMatchesAnswer(option, answer))
    );
    return matches.length ? matches : question.correct_answers.slice();
  }

  function sameSet(left, right) {
    if (left.length !== right.length) return false;
    const used = new Set();
    return left.every((item) => {
      const index = right.findIndex((candidate, candidateIndex) => {
        return !used.has(candidateIndex) && answersEquivalent(item, candidate);
      });
      if (index === -1) return false;
      used.add(index);
      return true;
    });
  }

  function shuffle(list) {
    const copy = list.slice();
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function uniqueSorted(values) {
    return Array.from(new Set(values.filter(Boolean))).sort((a, b) =>
      a.localeCompare(b, undefined, { numeric: true })
    );
  }

  function makeOption(value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    return option;
  }

  function makeGroup(label, options) {
    const group = document.createElement("optgroup");
    group.label = label;
    options.forEach((item) => group.appendChild(makeOption(item.value, item.label)));
    return group;
  }

  function buildPoolSelect() {
    els.poolSelect.innerHTML = "";
    els.poolSelect.appendChild(makeOption("all", "All questions"));
    els.poolSelect.appendChild(makeOption("group:exam-dumps", "Exam dump parts 1-12"));
    els.poolSelect.appendChild(makeOption("group:courses", "Course self-assessments"));
    els.poolSelect.appendChild(makeOption("group:original", "Original quiz files"));
    els.poolSelect.appendChild(makeOption("progress:missed", "Missed questions"));
    els.poolSelect.appendChild(makeOption("progress:unseen", "Unseen questions"));

    const courses = uniqueSorted(allQuestions.map((q) => q.course)).map((course) => ({
      value: `course:${course}`,
      label: `${course} self-assessment`,
    }));
    if (courses.length) els.poolSelect.appendChild(makeGroup("Courses", courses));

    const quizzes = uniqueSorted(allQuestions.map((q) => q.quiz)).map((quiz) => ({
      value: `quiz:${quiz}`,
      label: quiz,
    }));
    if (quizzes.length) els.poolSelect.appendChild(makeGroup("Quiz Sets", quizzes));

    const files = uniqueSorted(allQuestions.map((q) => q.source_file)).map((file) => ({
      value: `source:${file}`,
      label: file,
    }));
    if (files.length) els.poolSelect.appendChild(makeGroup("Source Files", files));
  }

  function getPool() {
    const value = els.poolSelect.value;
    if (value === "group:courses") return allQuestions.filter(isCourseQuestion);
    if (value === "group:original") return allQuestions.filter((q) => !isCourseQuestion(q) && !isExamDumpQuestion(q));
    if (value === "group:exam-dumps") return allQuestions.filter(isExamDumpQuestion);
    if (value === "progress:missed") return persistentMissedQuestions();
    if (value === "progress:unseen") return unseenQuestions();
    if (value.startsWith("course:")) return allQuestions.filter((q) => q.course === value.slice(7));
    if (value.startsWith("quiz:")) return allQuestions.filter((q) => q.quiz === value.slice(5));
    if (value.startsWith("source:")) return allQuestions.filter((q) => q.source_file === value.slice(7));
    return allQuestions.slice();
  }

  function updateMetrics() {
    const total = state.questions.length;
    const answered = state.answered.length;
    const progress = total ? Math.round((answered / total) * 100) : 0;
    els.metricTotal.textContent = String(total || allQuestions.length);
    els.metricScore.textContent = String(state.score);
    els.metricProgress.textContent = `${progress}%`;
  }

  function setActiveCountButton() {
    els.countButtons.querySelectorAll("button").forEach((button) => {
      button.classList.toggle("active", button.dataset.count === state.count);
    });
  }

  function startQuiz(customQuestions) {
    const pool = customQuestions || getPool();
    const randomized = els.shuffleToggle.checked ? shuffle(pool) : pool.slice();
    const desiredCount = customQuestions || state.count === "all"
      ? randomized.length
      : Number(state.count);
    state.questions = randomized.slice(0, Math.min(desiredCount, randomized.length));
    state.currentIndex = 0;
    state.score = 0;
    state.answered = [];
    state.selectedMissed = [];

    els.resultsView.hidden = true;
    els.questionView.hidden = false;
    els.nextButton.hidden = true;
    els.submitButton.hidden = false;
    renderQuestion();
    updateMetrics();
    saveSession();
  }

  function selectedOptions() {
    const textAnswer = els.optionsList.querySelector("[data-text-answer]");
    if (textAnswer) {
      const value = displayText(textAnswer.value);
      return value ? [value] : [];
    }
    return Array.from(els.optionsList.querySelectorAll("input:checked")).map((input) => input.value);
  }

  function resultForCurrentQuestion() {
    const question = state.questions[state.currentIndex];
    if (!question) return null;
    const key = questionKey(question);
    return state.answered.find((result) => questionKey(result.question) === key) || null;
  }

  function showSubmittedState(result) {
    const textAnswer = els.optionsList.querySelector("[data-text-answer]");
    if (textAnswer) {
      textAnswer.value = result.selected[0] || "";
    } else {
      const selected = result.selected;
      els.optionsList.querySelectorAll("input").forEach((input) => {
        input.checked = selected.some((answer) => answersEquivalent(input.value, answer));
      });
    }

    lockOptions(result);
    renderFeedback(result);
    els.submitButton.hidden = true;
    els.nextButton.hidden = false;
    els.nextButton.textContent = state.currentIndex === state.questions.length - 1 ? "Show Results" : "Next Question";
  }

  function renderQuestion() {
    const question = state.questions[state.currentIndex];
    els.feedbackPanel.hidden = true;
    els.feedbackPanel.className = "feedback-panel";
    els.feedbackPanel.innerHTML = "";
    els.nextButton.hidden = true;
    els.submitButton.hidden = false;
    els.submitButton.disabled = true;

    if (!question) {
      els.questionCounter.textContent = "Question 0 of 0";
      els.progressFill.style.width = "0%";
      els.questionSource.textContent = "Quiz bank";
      els.questionText.textContent = "No questions found.";
      els.optionsList.innerHTML = "";
      return;
    }

    const correctOptions = getCorrectOptions(question);
    const isMulti = correctOptions.length > 1;
    const options = question.options.length && els.shuffleToggle.checked ? shuffle(question.options) : question.options.slice();
    const submittedResult = resultForCurrentQuestion();

    els.questionCounter.textContent = `Question ${state.currentIndex + 1} of ${state.questions.length}`;
    els.progressFill.style.width = `${Math.round((state.currentIndex / state.questions.length) * 100)}%`;
    els.questionSource.textContent = sourceLabel(question);
    els.questionText.textContent = question.question;

    els.optionsList.innerHTML = "";
    if (!options.length) {
      const input = document.createElement("input");
      input.type = "text";
      input.className = "text-answer";
      input.dataset.textAnswer = "true";
      input.placeholder = "Type your answer";
      input.autocomplete = "off";
      els.optionsList.appendChild(input);
      if (submittedResult) {
        showSubmittedState(submittedResult);
      } else {
        input.focus();
      }
      return;
    }

    options.forEach((option, index) => {
      const id = `option_${state.currentIndex}_${index}`;
      const label = document.createElement("label");
      label.className = "option-row";
      label.setAttribute("for", id);

      const input = document.createElement("input");
      input.type = isMulti ? "checkbox" : "radio";
      input.name = "answer";
      input.id = id;
      input.value = option;

      const span = document.createElement("span");
      span.textContent = option;

      label.appendChild(input);
      label.appendChild(span);
      els.optionsList.appendChild(label);
    });

    if (submittedResult) showSubmittedState(submittedResult);
  }

  function lockOptions(result) {
    const textAnswer = els.optionsList.querySelector("[data-text-answer]");
    if (textAnswer) textAnswer.disabled = true;

    const correctNorms = result.correctOptions.map(normalize);
    els.optionsList.querySelectorAll(".option-row").forEach((row) => {
      const input = row.querySelector("input");
      input.disabled = true;
      const optionNorm = normalize(input.value);
      const isCorrect = correctNorms.includes(optionNorm);
      const isSelected = result.selected.map(normalize).includes(optionNorm);
      row.classList.toggle("correct", isCorrect);
      row.classList.toggle("incorrect", isSelected && !isCorrect);
    });
  }

  function sentenceList(items) {
    if (!items.length) return "nothing selected";
    return items.map((item) => `"${item}"`).join(", ");
  }

  function storedExplanation(question) {
    return displayText(question.answer_explanation || question.explanation);
  }

  function explanationReviewNote(question) {
    return "";
  }

  function buildExplanation(question, result) {
    const savedExplanation = storedExplanation(question);
    if (savedExplanation) return savedExplanation;

    const correct = sentenceList(result.correctOptions);
    const selected = sentenceList(result.selected);
    if (question.options.length === 2 && question.options.every((o) => ["true", "false"].includes(normalize(o)))) {
      return `The statement is ${result.correctOptions[0]} according to the quiz source. Your answer was ${selected}; the accepted answer is ${correct}.`;
    }
    if (result.correctOptions.length > 1) {
      return `This is a multi-answer question. The accepted set is ${correct}. Your submitted set was ${selected}, so every correct option has to be selected and no extra option can be included.`;
    }
    return `The accepted answer is ${correct}. Your submitted answer was ${selected}, which does not match the answer key for this question.`;
  }

  function buildBreakdown(result) {
    const correctNorms = result.correctOptions.map(normalize);
    const selectedNorms = result.selected.map(normalize);
    const rows = [];

    result.question.options.forEach((option) => {
      const optNorm = normalize(option);
      const isCorrect = correctNorms.includes(optNorm);
      const isSelected = selectedNorms.includes(optNorm);
      if (isSelected && isCorrect) {
        rows.push({ className: "hit", title: option, note: "Selected and correct." });
      } else if (!isSelected && isCorrect) {
        rows.push({ className: "miss", title: option, note: "Correct option that was not selected." });
      } else if (isSelected && !isCorrect) {
        rows.push({ className: "bad", title: option, note: "Selected option that is not in the accepted answer set." });
      }
    });

    return rows;
  }

  function renderFeedback(result) {
    els.feedbackPanel.hidden = false;
    els.feedbackPanel.className = `feedback-panel ${result.correct ? "correct" : "wrong"}`;
    const meta = sourceMeta(result.question);
    const breakdown = buildBreakdown(result);
    const reviewNote = !result.correct ? explanationReviewNote(result.question) : "";

    els.feedbackPanel.innerHTML = `
      <h3>${result.correct ? "Correct" : "Not quite"}</h3>
      <p class="feedback-explanation">${escapeHtml(
        result.correct ? `Accepted answer: ${sentenceList(result.correctOptions)}.` : buildExplanation(result.question, result)
      )}</p>
      ${
        !result.correct && breakdown.length
          ? `<ul class="answer-breakdown">${breakdown
              .map(
                (item) =>
                  `<li class="${item.className}"><strong>${escapeHtml(item.title)}</strong>${escapeHtml(item.note)}</li>`
              )
              .join("")}</ul>`
          : ""
      }
      ${reviewNote ? `<p class="meta-line">${escapeHtml(reviewNote)}</p>` : ""}
      ${meta ? `<p class="meta-line">${escapeHtml(meta)}</p>` : ""}
    `;
  }

  function submitAnswer() {
    const question = state.questions[state.currentIndex];
    if (!question) return;

    const selected = selectedOptions();
    if (!selected.length) {
      els.submitButton.disabled = true;
      return;
    }

    const correctOptions = getCorrectOptions(question);
    const correct = sameSet(selected, correctOptions);

    const result = {
      question,
      selected,
      correctOptions,
      correct,
      explanation: "",
    };
    result.explanation = buildExplanation(question, result);

    state.answered.push(result);
    if (correct) state.score += 1;
    recordAttempt(result);

    lockOptions(result);
    renderFeedback(result);
    els.submitButton.hidden = true;
    els.nextButton.hidden = false;
    els.nextButton.textContent = state.currentIndex === state.questions.length - 1 ? "Show Results" : "Next Question";
    updateMetrics();
    saveSession();
  }

  function nextQuestion() {
    if (state.currentIndex >= state.questions.length - 1) {
      showResults();
      return;
    }
    state.currentIndex += 1;
    renderQuestion();
    updateMetrics();
    saveSession();
  }

  function showResults() {
    const total = state.questions.length;
    const percent = total ? Math.round((state.score / total) * 100) : 0;
    const missed = state.answered.filter((item) => !item.correct);
    const persistentMissed = persistentMissedQuestions();
    state.selectedMissed = missed.length ? missed.map((item) => item.question) : persistentMissed;
    clearSession();

    els.questionView.hidden = true;
    els.resultsView.hidden = false;
    els.finalScore.textContent = `${percent}%`;
    els.finalSummary.textContent = `${state.score} correct of ${total}`;
    els.progressFill.style.width = "100%";
    els.metricProgress.textContent = "100%";
    els.retryMissedButton.disabled = state.selectedMissed.length === 0;

    els.missedReview.innerHTML = missed.length
      ? missed
          .map(
            (item) => `
              <article class="review-item">
                <h3>${escapeHtml(item.question.question)}</h3>
                <p><strong>Your answer:</strong> ${escapeHtml(sentenceList(item.selected))}</p>
                <p><strong>Correct answer:</strong> ${escapeHtml(sentenceList(item.correctOptions))}</p>
                <p>${escapeHtml(item.explanation)}</p>
                ${explanationReviewNote(item.question) ? `<p class="meta-line">${escapeHtml(explanationReviewNote(item.question))}</p>` : ""}
                <p class="meta-line">${escapeHtml(sourceMeta(item.question))}</p>
              </article>
            `
          )
          .join("")
      : `<article class="review-item"><h3>Clean run</h3><p>No missed questions in this session.</p></article>`;
  }

  function wireEvents() {
    els.poolSelect.addEventListener("change", () => {
      state.selectedPool = els.poolSelect.value;
      const pool = getPool();
      els.metricTotal.textContent = String(pool.length);
    });

    els.countButtons.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-count]");
      if (!button) return;
      state.count = button.dataset.count;
      setActiveCountButton();
    });

    els.optionsList.addEventListener("change", () => {
      els.submitButton.disabled = selectedOptions().length === 0;
    });
    els.optionsList.addEventListener("input", () => {
      els.submitButton.disabled = selectedOptions().length === 0;
    });

    els.startButton.addEventListener("click", () => startQuiz());
    els.submitButton.addEventListener("click", submitAnswer);
    els.nextButton.addEventListener("click", nextQuestion);
    els.newQuizButton.addEventListener("click", () => {
      els.resultsView.hidden = true;
      els.questionView.hidden = false;
      startQuiz();
    });
    els.retryMissedButton.addEventListener("click", () => {
      if (!state.selectedMissed.length) return;
      els.resultsView.hidden = true;
      els.questionView.hidden = false;
      startQuiz(state.selectedMissed);
    });
    els.reviewMissedButton.addEventListener("click", () => {
      const missed = persistentMissedQuestions();
      if (!missed.length) return;
      els.poolSelect.value = "progress:missed";
      els.resultsView.hidden = true;
      els.questionView.hidden = false;
      startQuiz(missed);
    });
    els.clearProgressButton.addEventListener("click", () => {
      if (!window.confirm("Reset saved quiz progress on this device?")) return;
      progress = emptyProgress();
      clearSession();
      try {
        window.localStorage.removeItem(STORAGE_KEY);
      } catch (error) {
        // Nothing else to do; in-memory progress has already been reset.
      }
      updateProgressPanel();
      if (els.poolSelect.value.startsWith("progress:")) {
        els.metricTotal.textContent = String(getPool().length);
      }
    });
  }

  function init() {
    buildPoolSelect();
    setActiveCountButton();
    els.bankSummary.textContent = `${allQuestions.length} questions loaded`;
    els.metricTotal.textContent = String(allQuestions.length);
    updateProgressPanel();
    wireEvents();
    if (!restoreSession()) startQuiz();
  }

  init();
})();
