"""
StudyMate – Smart Study Assistant Chatbot
Beginner-Friendly NLP Project
Technique: Keyword-based Text Classification
Backend: Python Flask
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import re, os, json, sqlite3
from markupsafe import Markup

app = Flask(__name__)
# Change this secret (or set the SECRET_KEY environment variable) before deploying
app.secret_key = os.environ.get("SECRET_KEY", "studymate-dev-secret-change-me")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studymate.db")


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pw TEXT);
        CREATE TABLE IF NOT EXISTS progress(user_id INTEGER, subject TEXT, days TEXT, PRIMARY KEY(user_id, subject));
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER, sender TEXT, text TEXT);
        CREATE TABLE IF NOT EXISTS quiz_scores(id INTEGER PRIMARY KEY, user_id INTEGER, subject TEXT, score INTEGER, total INTEGER);
        """)


_ICON_CACHE = {}


@app.template_global()
def icon(name):
    """Inline a Lucide SVG icon from static/icons (works offline, takes the text colour)."""
    if name not in _ICON_CACHE:
        path = os.path.join(app.static_folder, "icons", name + ".svg")
        svg = open(path, encoding="utf8").read()
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
        _ICON_CACHE[name] = svg.replace("<svg", '<svg aria-hidden="true" focusable="false"', 1)
    return Markup(_ICON_CACHE[name])


def current_user():
    return session.get("uid")

# ============================================================
# 1. SUBJECT DATABASE (Topics + Tips + Plans)
# ============================================================

SUBJECTS = {
    "python": {
        "name": "Python Programming",
        "topics": [
            "Variables & Data Types",
            "Operators & Expressions",
            "If-Else & Conditional Statements",
            "Loops (for, while)",
            "Functions & Modules",
            "Lists, Tuples & Dictionaries",
            "File Handling Basics",
            "Simple Programs & Practice"
        ],
        "tips": [
            "Practice small programs every day (even 20–30 mins).",
            "Type code yourself instead of only reading.",
            "Understand errors – they teach you a lot.",
            "Start with simple problems, then increase difficulty.",
            "Use online compilers or VS Code for practice."
        ],
        "plan_1week": [
            "Day 1: Variables, Data Types & Operators",
            "Day 2: If-Else & Conditional Logic",
            "Day 3: Loops (for & while)",
            "Day 4: Functions",
            "Day 5: Lists & Dictionaries",
            "Day 6: Practice programs",
            "Day 7: Revision + Mini Project idea"
        ]
    },
    "mathematics": {
        "name": "Mathematics",
        "topics": [
            "Numbers & Operations",
            "Fractions, Decimals & Percentages",
            "Basic Algebra (Equations)",
            "Geometry (Shapes, Area, Perimeter)",
            "Simple Interest & Ratio",
            "Introduction to Graphs",
            "Word Problems Practice"
        ],
        "tips": [
            "Practice daily – consistency is more important than long hours.",
            "Understand the concept before memorizing formulas.",
            "Solve previous year / sample questions.",
            "Draw diagrams for geometry questions.",
            "Check calculations carefully to avoid silly mistakes."
        ],
        "plan_1week": [
            "Day 1-2: Numbers, Fractions & Percentages",
            "Day 3-4: Basic Algebra & Equations",
            "Day 5-6: Geometry (Area, Perimeter, Volume)",
            "Day 7: Revision + Practice questions"
        ]
    },
    "english": {
        "name": "English",
        "topics": [
            "Parts of Speech",
            "Tenses (Present, Past, Future)",
            "Sentence Structure",
            "Reading Comprehension",
            "Essay & Letter Writing",
            "Vocabulary Building",
            "Grammar Practice"
        ],
        "tips": [
            "Read something every day (story, article or newspaper).",
            "Practice writing short paragraphs regularly.",
            "Learn 5–10 new words daily with meanings.",
            "Focus on grammar rules with examples.",
            "Speak or think in English to improve fluency."
        ],
        "plan_1week": [
            "Day 1-2: Grammar (Parts of Speech + Tenses)",
            "Day 3-4: Reading Comprehension practice",
            "Day 5: Writing skills (Paragraph / Essay)",
            "Day 6-7: Vocabulary + Full revision"
        ]
    },
    "nlp": {
        "name": "Natural Language Processing (NLP)",
        "topics": [
            "What is NLP? Introduction & Applications",
            "Text Preprocessing (Lowercase, Cleaning, Tokenization)",
            "Stop Words & Stemming / Lemmatization",
            "Bag Classification (Keyword & Rule-based)",
            "Bag Frequency & Bag of Words",
            "Simple Chatbot Logic",
            "Sentiment Analysis Basics",
            "Real-world NLP Examples"
        ],
        "tips": [
            "Start with simple text cleaning before advanced techniques.",
            "Practice on small datasets (tweets, reviews, chat messages).",
            "Understand tokenization – it is the foundation of NLP.",
            "Build tiny projects like a keyword chatbot (like StudyMate!).",
            "Learn one concept at a time – preprocessing → classification → applications."
        ],
        "plan_1week": [
            "Day 1: Introduction to NLP + Applications",
            "Day 2: Text Preprocessing & Tokenization",
            "Day 3: Stop words, Stemming, Lemmatization",
            "Day 4: Text Classification (Keyword-based)",
            "Day 5: Bag of Words & Simple frequency analysis",
            "Day 6: Build a mini chatbot / classifier",
            "Day 7: Revision + Small project ideas"
        ]
    },
    "java": {
        "name": "Java Programming",
        "topics": [
            "Introduction to Java & Setup",
            "Variables, Data Types & Operators",
            "Control Statements (if, switch)",
            "Loops (for, while, do-while)",
            "Methods / Functions",
            "Arrays & Strings",
            "Object-Oriented Concepts (Class, Object)",
            "Basic Input / Output"
        ],
        "tips": [
            "Install JDK and practice in an IDE (IntelliJ / Eclipse / VS Code).",
            "Write and run small programs daily.",
            "Focus on understanding syntax and structure first.",
            "Practice OOP concepts with simple real-life examples.",
            "Debug errors carefully – reading error messages helps a lot."
        ],
        "plan_1week": [
            "Day 1: Java setup + Variables & Data Types",
            "Day 2: Operators & Control Statements",
            "Day 3: Loops",
            "Day 4: Methods",
            "Day 5: Arrays & Strings",
            "Day 6: Classes & Objects (OOP basics)",
            "Day 7: Practice programs + Revision"
        ]
    },
    "computer": {
        "name": "Computer Science",
        "topics": [
            "Introduction to Computers",
            "Hardware vs Software",
            "Number Systems (Binary, Decimal)",
            "Basic Programming Concepts",
            "Algorithms & Flowcharts",
            "Internet & Cyber Safety",
            "Operating System Basics",
            "Simple Data Structures Overview"
        ],
        "tips": [
            "Understand fundamentals before jumping into coding.",
            "Practice logic building with flowcharts and pseudocode.",
            "Learn keyboard shortcuts and basic computer operations.",
            "Stay updated with basic cyber safety rules.",
            "Relate theoretical concepts to real computer usage."
        ],
        "plan_1week": [
            "Day 1-2: Computer fundamentals + Hardware/Software",
            "Day 3: Number Systems & Logic basics",
            "Day 4: Algorithms & Flowcharts",
            "Day 5: Operating System + Internet Safety",
            "Day 6-7: Programming concepts practice + Revision"
        ]
    }
}


# ============================================================
# QUIZ QUESTIONS: (question, [options], index of correct option)
# ============================================================
QUIZ = {
    "python": [
        ("Which keyword defines a function in Python?", ["func", "def", "function", "define"], 1),
        ("What does len([1, 2, 3]) return?", ["2", "3", "4", "Error"], 1),
        ("Which of these is a mutable data type?", ["tuple", "string", "list", "int"], 2),
        ("Which loop runs while a condition stays true?", ["for", "while", "repeat", "loop"], 1),
    ],
    "mathematics": [
        ("What is 25% of 200?", ["25", "40", "50", "75"], 2),
        ("Solve: 2x + 6 = 14", ["x = 3", "x = 4", "x = 5", "x = 10"], 1),
        ("Area of a rectangle 5 by 3?", ["8", "15", "16", "30"], 1),
        ("Simple interest on 1000 at 10% for 2 years?", ["100", "200", "210", "1200"], 1),
    ],
    "english": [
        ("Which word is a noun?", ["quickly", "happiness", "run", "beautiful"], 1),
        ("Pick the correct sentence.", ["She go to school.", "She goes to school.", "She going school.", "She gone to school."], 1),
        ("Past tense of 'write' is:", ["writed", "wrote", "written", "writing"], 1),
        ("A word with the opposite meaning is called:", ["synonym", "antonym", "homonym", "acronym"], 1),
    ],
    "nlp": [
        ("Splitting text into words is called:", ["Stemming", "Tokenization", "Parsing", "Encoding"], 1),
        ("Stop words are:", ["Rare keywords", "Very common words often removed", "Punctuation only", "Names of people"], 1),
        ("Reducing 'running' to 'run' is:", ["Lemmatization/Stemming", "Tokenization", "Translation", "Tagging"], 0),
        ("StudyMate finds the subject using:", ["Deep learning", "Keyword matching", "Speech recognition", "Image search"], 1),
    ],
    "java": [
        ("Java programs are compiled into:", ["Machine code only", "Bytecode", "Python code", "HTML"], 1),
        ("Which is the entry point of a Java program?", ["start()", "run()", "main()", "init()"], 2),
        ("Which keyword creates an object?", ["create", "new", "make", "object"], 1),
        ("Which is NOT a primitive type?", ["int", "boolean", "String", "char"], 2),
    ],
    "computer": [
        ("Binary of decimal 5 is:", ["100", "101", "110", "111"], 1),
        ("The 'brain' of the computer is the:", ["RAM", "CPU", "Monitor", "Mouse"], 1),
        ("Which is system software?", ["MS Word", "Operating System", "Chrome", "Photoshop"], 1),
        ("A step-by-step solution to a problem is a(n):", ["Algorithm", "Browser", "Bug", "Compiler"], 0),
    ],
}

# Keyword mapping for subject classification
SUBJECT_KEYWORDS = {
    "python": ["python", "py", "programming in python", "learn python"],
    "mathematics": ["hisab", "math", "maths", "mathematics", "algebra", "geometry", "calculus", "arithmetic"],
    "english": ["angrezi", "english", "grammar", "vocabulary", "essay", "literature", "writing"],
    "nlp": ["nlp", "natural language", "natural language processing", "text classification", "chatbot", "sentiment"],
    "java": ["java", "jre", "jdk", "object oriented", "oop java"],
    "computer": ["computer science", "computer", "cs", "hardware", "software", "algorithm", "flowchart", "operating system"]
}


# ============================================================
# 2. NLP – TEXT CLASSIFICATION FUNCTIONS
# ============================================================

def has(text: str, phrase: str) -> bool:
    """Whole-word match, so 'hi' does not fire inside 'this' or 'py' inside 'happy'."""
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def preprocess(text: str) -> str:
    """Convert to lowercase and remove extra spaces / special chars."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def classify_subject(message: str) -> str | None:
    """
    Keyword-based Text Classification.
    Returns the subject key if found, else None.
    """
    text = preprocess(message)
    scores = {}

    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if has(text, kw):
                score += 1
        if score > 0:
            scores[subject] = score

    if not scores:
        return None
    return max(scores, key=scores.get)


def classify_intent(message: str) -> str:
    """
    Classify user intent:
    - greeting
    - topics
    - tips
    - plan
    - help
    - goodbye
    - subject_query (when only subject is mentioned)
    - unknown
    """
    text = preprocess(message)

    if any(has(text, w) for w in ["bye", "goodbye", "exit", "quit", "see you", "khuda hafiz", "allah hafiz"]):
        return "goodbye"

    if any(has(text, w) for w in ["hi", "hello", "hey", "salam", "assalam o alaikum", "namaste", "good morning", "good evening"]):
        return "greeting"

    if any(has(text, w) for w in ["tip", "tips", "advice", "suggestion", "how to study", "study tip", "mashwara", "tarika"]):
        return "tips"

    if any(has(text, w) for w in ["topic", "topics", "chapter", "chapters", "what to study", "syllabus", "recommend"]):
        return "topics"

    if any(has(text, w) for w in ["plan", "schedule", "timetable", "routine", "study plan"]):
        return "plan"

    if any(has(text, w) for w in ["quiz", "mcq", "mcqs", "test me", "practice questions"]):
        return "quiz"

    # If a subject is detected, treat as subject query ("I need help with Python")
    if classify_subject(text):
        return "subject_query"

    if any(has(text, w) for w in ["help", "command", "what can you do", "features"]):
        return "help"

    return "unknown"


# ============================================================
# 3. RESPONSE GENERATOR
# ============================================================

def chips_for(subject_key):
    """Suggested next messages shown as buttons under the bot reply."""
    if not subject_key:
        return ["Python", "Mathematics", "English", "NLP", "Java", "Computer Science"]
    n = SUBJECTS[subject_key]["name"]
    return [f"{n} topics", f"{n} tips", f"{n} study plan", f"{n} quiz"]


def generate_response(message: str, current_subject: str | None = None) -> dict:
    """
    Main chatbot logic.
    Returns a dictionary with reply text and optional structured data.
    """
    intent = classify_intent(message)
    detected = classify_subject(message)

    # Update current subject if a new one is detected
    if detected:
        current_subject = detected

    subject_data = SUBJECTS.get(current_subject) if current_subject else None

    # ----- Greeting -----
    if intent == "greeting":
        return {
            "reply": "Hello! Welcome to <b>StudyMate</b> – Your Personal Study Assistant.<br><br>"
                     "What subject do you want help with today?<br>"
                     "You can say things like:<br>"
                     "• <i>I need help with Python</i><br>"
                     "• <i>NLP topics</i><br>"
                     "• <i>Java study plan</i><br>"
                     "• <i>Maths tips</i>",
            "subject": current_subject,
            "type": "greeting"
        }

    # ----- Goodbye -----
    if intent == "goodbye":
        return {
            "reply": "Goodbye! Keep studying and all the best for your exams. <br>Come back anytime!",
            "subject": current_subject,
            "type": "goodbye"
        }

    # ----- Help -----
    if intent == "help":
        return {
            "reply": "Here's what I can do for you:<br><br>"
                     "<b>Subject Detection</b> – Just tell me the subject<br>"
                     "<b>Topic Suggestions</b> – Ask for topics<br>"
                     "<b>Study Tips</b> – Ask for tips<br>"
                     "<b>Study Plan</b> – Ask for a 7-day plan<br>"
                     "<b>Quiz</b> – Say <i>Python quiz</i> to test yourself<br><br>"
                     "Examples:<br>"
                     "• Python topics<br>"
                     "• NLP tips<br>"
                     "• Java study plan<br>"
                     "• Maths tips",
            "subject": current_subject,
            "type": "help"
        }

    # ----- No subject yet -----
    if not subject_data:
        return {
            "reply": "Please tell me which subject you want help with.<br><br>"
                     "Supported subjects: <b>Python, Mathematics, English, NLP, Java, Computer Science</b>",
            "subject": None,
            "type": "ask_subject"
        }

    name = subject_data["name"]

    # ----- Quiz -----
    if intent == "quiz":
        return {
            "reply": f"Ready to test yourself on <b>{name}</b>? It is {len(QUIZ.get(current_subject, []))} quick questions.<br><br>"
                     f"<a class='chat-link' href='/quiz?subject={current_subject}'>Start {name} quiz</a>",
            "subject": current_subject,
            "type": "quiz"
        }

    # ----- Topics -----
    if intent == "topics":
        topics_html = "<br>".join([f"{i+1}. {t}" for i, t in enumerate(subject_data["topics"])])
        return {
            "reply": f"<b>Recommended Topics for {name}:</b><br><br>{topics_html}",
            "subject": current_subject,
            "type": "topics",
            "topics": subject_data["topics"]
        }

    # ----- Tips -----
    if intent == "tips":
        tips_html = "<br>".join([f"• {t}" for t in subject_data["tips"]])
        return {
            "reply": f"<b>Study Tips for {name}:</b><br><br>{tips_html}",
            "subject": current_subject,
            "type": "tips",
            "tips": subject_data["tips"]
        }

    # ----- Plan -----
    if intent == "plan":
        plan_html = "<br>".join([f"• {p}" for p in subject_data["plan_1week"]])
        return {
            "reply": f"<b>Simple 7-Day Study Plan for {name}:</b><br><br>{plan_html}<br><br>"
                     "You can adjust the days according to your free time!",
            "subject": current_subject,
            "type": "plan",
            "plan": subject_data["plan_1week"]
        }

    # ----- Subject Query (full response) -----
    if intent == "subject_query" or intent == "unknown":
        topics_html = "<br>".join([f"{i+1}. {t}" for i, t in enumerate(subject_data["topics"][:5])])
        tip = subject_data["tips"][0]
        return {
            "reply": f"Great! Let's study <b>{name}</b>. <br><br>"
                     f"<b>Recommended topics:</b><br>{topics_html}<br><br>"
                     f"<b>Study Tip:</b> {tip}<br><br>"
                     "You can also ask for:<br>"
                     "• full topics list<br>"
                     "• more tips<br>"
                     "• a study plan<br>"
                     "• a quick quiz",
            "subject": current_subject,
            "type": "subject_intro",
            "topics": subject_data["topics"],
            "tips": subject_data["tips"]
        }

    return {
        "reply": "I didn't quite understand that. Try asking for topics, tips or a study plan!",
        "subject": current_subject,
        "type": "unknown"
    }


# ============================================================
# 4. FLASK ROUTES
# ============================================================

@app.route("/")
def home():
    """Home / Dashboard page"""
    return render_template("index.html", subjects=SUBJECTS)


@app.route("/chat")
def chat_page():
    """Chatbot interface page"""
    subject = request.args.get("subject", "")
    return render_template("chat.html", initial_subject=subject, name=session.get("name"))


@app.route("/api/chat", methods=["POST"])
def api_chat():  # adds "chips" to every reply
    """
    API endpoint for chatbot messages.
    Expects JSON: { "message": "...", "subject": "python" (optional) }
    """
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    current_subject = data.get("subject") or None

    if not message:
        return jsonify({"reply": "Please type a message.", "subject": current_subject})

    result = generate_response(message, current_subject)
    result["chips"] = chips_for(result.get("subject"))
    uid = current_user()
    if uid:
        with db() as con:
            con.execute("INSERT INTO messages(user_id, sender, text) VALUES(?,?,?)", (uid, "user", message))
            con.execute("INSERT INTO messages(user_id, sender, text) VALUES(?,?,?)", (uid, "bot", result["reply"]))
    return jsonify(result)


@app.route("/plan")
def plan_page():
    """Simple Study Plan page"""
    subject_key = request.args.get("subject", "python")
    subject_data = SUBJECTS.get(subject_key, SUBJECTS["python"])
    return render_template("plan.html", subject=subject_data, subject_key=subject_key)



# ============================================================
# 5. ACCOUNTS, HISTORY, PROGRESS, QUIZ, DASHBOARD
# ============================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        if not name or "@" not in email or len(pw) < 6:
            return render_template("auth.html", mode="signup", error="Enter your name, a valid email and a password of 6+ characters.")
        try:
            with db() as con:
                cur = con.execute("INSERT INTO users(name, email, pw) VALUES(?,?,?)", (name, email, generate_password_hash(pw)))
            session.update(uid=cur.lastrowid, name=name)
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            return render_template("auth.html", mode="signup", error="That email is already registered. Try logging in.")
    return render_template("auth.html", mode="signup")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with db() as con:
            u = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if u and check_password_hash(u["pw"], request.form.get("password", "")):
            session.update(uid=u["id"], name=u["name"])
            return redirect(url_for("dashboard"))
        return render_template("auth.html", mode="login", error="Wrong email or password.")
    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    uid = current_user()
    if not uid:
        return jsonify({"messages": []})
    with db() as con:
        if request.method == "DELETE":
            con.execute("DELETE FROM messages WHERE user_id=?", (uid,))
            return jsonify({"ok": True})
        rows = con.execute("SELECT sender, text FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 40", (uid,)).fetchall()
    return jsonify({"messages": [dict(r) for r in reversed(rows)]})


@app.route("/api/progress/<subject>", methods=["GET", "POST"])
def api_progress(subject):
    uid = current_user()
    if not uid or subject not in SUBJECTS:
        return jsonify({"days": []})
    with db() as con:
        if request.method == "POST":
            days = [bool(d) for d in (request.get_json(silent=True) or {}).get("days", [])][:14]
            con.execute("INSERT OR REPLACE INTO progress VALUES(?,?,?)", (uid, subject, json.dumps(days)))
            return jsonify({"ok": True})
        row = con.execute("SELECT days FROM progress WHERE user_id=? AND subject=?", (uid, subject)).fetchone()
    return jsonify({"days": json.loads(row["days"]) if row else []})


@app.route("/quiz")
def quiz_page():
    return render_template("quiz.html", subjects=SUBJECTS)


@app.route("/api/quiz/<subject>")
def api_quiz(subject):
    items = QUIZ.get(subject, [])
    return jsonify([{"q": q, "options": o, "answer": a} for q, o, a in items])


@app.route("/api/quiz/<subject>/score", methods=["POST"])
def api_quiz_score(subject):
    uid = current_user()
    d = request.get_json(silent=True) or {}
    if uid and subject in QUIZ:
        total = len(QUIZ[subject])
        score = max(0, min(int(d.get("score", 0)), total))
        with db() as con:
            con.execute("INSERT INTO quiz_scores(user_id, subject, score, total) VALUES(?,?,?,?)", (uid, subject, score, total))
    return jsonify({"saved": bool(uid)})


@app.route("/dashboard")
def dashboard():
    uid = current_user()
    if not uid:
        return redirect(url_for("login"))
    rows = []
    with db() as con:
        for key, data in SUBJECTS.items():
            p = con.execute("SELECT days FROM progress WHERE user_id=? AND subject=?", (uid, key)).fetchone()
            done = sum(json.loads(p["days"])) if p else 0
            q = con.execute("SELECT COUNT(*) n, MAX(score) best, MAX(total) total FROM quiz_scores WHERE user_id=? AND subject=?", (uid, key)).fetchone()
            rows.append({"key": key, "name": data["name"], "done": done, "days": len(data["plan_1week"]),
                         "attempts": q["n"], "best": q["best"], "total": q["total"],
                         "started": done > 0 or q["n"] > 0})
    stats = {"started": sum(r["started"] for r in rows), "subjects": len(rows),
             "done": sum(r["done"] for r in rows), "days": sum(r["days"] for r in rows),
             "quizzes": sum(r["attempts"] for r in rows)}
    return render_template("dashboard.html", rows=rows, stats=stats, name=session.get("name"))


# ============================================================
# 6. RUN
# ============================================================

init_db()

if __name__ == "__main__":
    print("=" * 50)
    print("  StudyMate – Smart Study Assistant")
    print("  Open: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
