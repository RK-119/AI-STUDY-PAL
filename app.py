#                                                                   ☀️
# ==============================
# AI Study Pal - A Web App!
# ==============================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from flask import Flask, request, render_template, send_file, url_for
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# ==============================
# 1. DATA SETUP & CLEANING
# ==============================

def load_and_clean_data(file_path="educational_texts.csv"):
    """Load and clean educational texts dataset"""
    if not os.path.exists(file_path):
        raise RuntimeError(f"File {file_path} not found.")
    
    try:
        df = pd.read_csv(
            file_path,
            engine='python',
            quotechar='"',
            on_bad_lines='skip',
            encoding='utf-8'
        )
    except Exception as e:
        try:
            df = pd.read_csv(file_path, encoding='utf-8', on_error='skip')
        except:
            raise RuntimeError(f"Error reading CSV: {str(e)}")

    # Ensure required columns exist
    if 'text' not in df.columns or 'subject' not in df.columns:
        raise RuntimeError("CSV must contain 'text' and 'subject' columns.")

    # Normalize and drop empty texts
    df['text'] = df['text'].astype(str).str.strip()
    df = df[df['text'].str.len() > 0].copy()
    
    # Ensure difficulty column exists
    if 'difficulty' not in df.columns:
        df['difficulty'] = 'easy'
    
    if df.empty:
        raise RuntimeError("No valid text rows found after cleaning.")

    return df

def visualize_subjects(df):
    """Generate pie chart of subject distribution"""
    plt.figure(figsize=(8, 6))
    subject_counts = df['subject'].value_counts()
    plt.pie(subject_counts, labels=subject_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title("Subject Distribution in Dataset")
    plt.tight_layout()
    plt.savefig('static/subject_distribution.png')
    plt.close()
    return 'static/subject_distribution.png'

# ==============================
# 2. MACHINE LEARNING
# ==============================

def train_subject_classifier(df):
    """Train classifier to predict subject from text"""
    vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
    X = vectorizer.fit_transform(df['text'])
    y = df['subject']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression(max_iter=300, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    print(f"Subject Classifier - Accuracy: {accuracy:.2%}")
    
    return model, vectorizer

def train_difficulty_classifier(df):
    """Train classifier for quiz difficulty prediction"""
    vectorizer = CountVectorizer(max_features=300, stop_words='english')
    X = vectorizer.fit_transform(df['text'])
    y = df['difficulty']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression(max_iter=300, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    print(f"Difficulty Classifier - Accuracy: {accuracy:.2%}")
    
    return model, vectorizer

def classify_subject(text, clf_model, clf_vectorizer):
    """Classify text to predict subject"""
    X = clf_vectorizer.transform([text])
    subject = clf_model.predict(X)[0]
    confidence = max(clf_model.predict_proba(X)[0]) * 100
    return subject, confidence

def generate_contextual_plan(subject, hours, difficulty):
    """Generate context-aware study plan"""
    days = 5
    hours_per_day = hours // days
    
    study_phases = {
        'Math': ['Understand concepts', 'Practice problems', 'Solve complex examples', 'Review fundamentals', 'Final practice'],
        'Science': ['Read overview', 'Study mechanisms', 'Understand applications', 'Practice questions', 'Review key concepts'],
        'Computer Science': ['Learn syntax', 'Code simple programs', 'Build projects', 'Debug issues', 'Optimize code'],
        'History': ['Read timeline', 'Study key events', 'Understand context', 'Analyze impacts', 'Synthesize learning'],
        'Machine Learning/NLP': ['Understand theory', 'Study algorithms', 'Hands-on coding', 'Analyze results', 'Optimize model'],
    }
    
    phase_list = study_phases.get(subject, ['Learn basics', 'Practice concepts', 'Apply knowledge', 'Review material', 'Final drill'])
    
    plan = []
    for day, phase in enumerate(phase_list[:days], 1):
        difficulty_note = "(Focus on fundamentals)" if difficulty == "easy" else "(Work on advanced concepts)"
        plan.append(f"Day {day}: {phase} - {hours_per_day}h {difficulty_note}")
    
    return plan

def generate_quiz(df, subject, num_questions=5):
    """Generate quiz with proper questions and options"""
    subject_texts = df[df['subject'].str.contains(subject, case=False, na=False)]
    
    if len(subject_texts) < num_questions:
        subject_texts = df.sample(min(num_questions, len(df)), random_state=42)
    else:
        subject_texts = subject_texts.sample(num_questions, random_state=42)
    
    quiz = []
    question_templates = [
        "Which of the following best describes: {text}?",
        "What is the main concept of: {text}?",
        "According to the material: {text}. Which is true?",
        "Based on {text}, which statement is correct?",
        "The passage explains that {text}. What does this mean?"
    ]
    
    option_sets = [
        ["Correct answer", "Plausible wrong answer", "Common misconception", "Unrelated concept"],
        ["True statement", "False assumption", "Partial truth", "Opposite concept"],
        ["Precise definition", "Vague description", "Related but different", "Common confusion"]
    ]
    
    for i, row in subject_texts.iterrows():
        text_snippet = row['text'][:80] + "..." if len(row['text']) > 80 else row['text']
        q_template = question_templates[i % len(question_templates)]
        question = q_template.format(text=text_snippet)
        
        difficulty = row.get('difficulty', 'easy')
        options = option_sets[i % len(option_sets)]
        
        quiz.append({
            'question': question,
            'options': options,
            'difficulty': difficulty,
            'source_text': row['text'][:100]
        })
    
    return quiz

def suggest_resources(df, subject):
    """Suggest learning resources based on subject clustering"""
    subject_resources = {
        'Math': [
            'Khan Academy (Math Section) - https://www.khanacademy.org/math',
            'Wolfram Alpha - https://www.wolframalpha.com',
            'Desmos Graphing - https://www.desmos.com'
        ],
        'Science': [
            'NCBI PubMed - https://pubmed.ncbi.nlm.nih.gov',
            'Science Direct - https://www.sciencedirect.com',
            'Khan Academy (Science) - https://www.khanacademy.org/science'
        ],
        'Computer Science': [
            'GitHub - https://github.com',
            'Stack Overflow - https://stackoverflow.com',
            'Codecademy - https://www.codecademy.com',
            'W3Schools - https://www.w3schools.com'
        ],
        'History': [
            'History.com - https://www.history.com',
            'Britannica - https://www.britannica.com',
            'Google Scholar - https://scholar.google.com'
        ],
        'Machine Learning/NLP': [
            'Kaggle - https://www.kaggle.com',
            'TensorFlow Hub - https://www.tensorflow.org',
            'ArXiv - https://arxiv.org',
            'Papers with Code - https://paperswithcode.com'
        ]
    }
    
    return subject_resources.get(subject, [
        'Google Scholar - https://scholar.google.com',
        'Wikipedia - https://www.wikipedia.org',
        'Coursera - https://www.coursera.org'
    ])

# ==============================
# 3. NATURAL LANGUAGE PROCESSING
# ==============================

def extract_keywords(text, num_keywords=5):
    """Extract keywords from text using tokenization"""
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
    return keywords[:num_keywords]

def generate_study_tips(text, subject):
    """Generate context-aware study tips based on text and subject"""
    keywords = extract_keywords(text, num_keywords=3)
    
    general_tips = [
        "Review key terms daily to build long-term memory",
        "Create summary notes for better understanding",
        "Practice with examples related to the topic",
        "Teach concepts to others to reinforce learning",
        "Take breaks every 25-30 minutes (Pomodoro technique)"
    ]
    
    subject_tips = {
        'Math': [
            f"Master the fundamentals of {keywords[0] if keywords else 'core concepts'}",
            "Work through problems step-by-step",
            "Verify solutions using multiple methods",
            "Create a formula reference sheet"
        ],
        'Science': [
            f"Understand the mechanism behind {keywords[0] if keywords else 'processes'}",
            "Relate concepts to real-world examples",
            "Draw diagrams to visualize processes",
            "Understand cause-and-effect relationships"
        ],
        'Computer Science': [
            f"Code yourself using {keywords[0] if keywords else 'concepts'} covered",
            "Debug code to understand error messages",
            "Read and understand existing code",
            "Practice algorithmic thinking"
        ],
        'History': [
            f"Understand the context of {keywords[0] if keywords else 'events'} studied",
            "Create timelines of important events",
            "Analyze multiple perspectives on events",
            "Connect historical events to modern world"
        ],
        'Machine Learning/NLP': [
            f"Implement {keywords[0] if keywords else 'algorithms'} from scratch",
            "Experiment with datasets on Kaggle",
            "Understand mathematical foundations",
            "Reproduce research paper results"
        ]
    }
    
    tips = subject_tips.get(subject, general_tips)
    return tips[:4]

# ==============================
# 4. DEEP LEARNING & SUMMARIZATION
# ==============================

def summarize_text(text, max_sentences=3):
    """Text summarization using sentence extraction"""
    try:
        sentences = sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring based on word frequency
        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        word_freq = {}
        
        for word in words:
            if word.isalnum() and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sent_scores = {}
        for i, sent in enumerate(sentences):
            for word in word_tokenize(sent.lower()):
                if word in word_freq:
                    sent_scores[i] = sent_scores.get(i, 0) + word_freq[word]
        
        top_sentences = sorted(sent_scores, key=sent_scores.get, reverse=True)[:max_sentences]
        top_sentences = sorted(top_sentences)
        
        summary = " ".join([sentences[i] for i in top_sentences])
        return summary
    except:
        return text[:200] + "..." if len(text) > 200 else text

def generate_motivational_feedback(subject, performance='good'):
    """Generate personalized motivational feedback"""
    feedbacks = {
        'Math': {
            'good': "Excellent work on Math! Your problem-solving skills are improving. Keep practicing!",
            'average': "You're making progress in Math. Practice more challenging problems!",
            'needs_work': "Math takes practice. Review fundamentals and try again. You'll get better!"
        },
        'Science': {
            'good': "Great effort in Science! Your understanding of concepts is solid. Keep exploring!",
            'average': "Good start in Science! Dig deeper into the mechanisms and applications.",
            'needs_work': "Science requires patience. Review core concepts and relate them to real-world examples."
        },
        'Computer Science': {
            'good': "Fantastic coding progress! You're thinking like a programmer. Keep building projects!",
            'average': "Your coding is improving! Practice more everyday. Consistency is key.",
            'needs_work': "Programming takes time to learn. Break problems into smaller steps. You're on the right track!"
        },
        'History': {
            'good': "Impressive understanding of historical events! Excellent grasp of context and connections.",
            'average': "Good historical knowledge! Make more connections between events.",
            'needs_work': "History is about patterns. Review timelines and try to see the bigger picture."
        },
        'Machine Learning/NLP': {
            'good': "Outstanding ML learning! You're grasping complex concepts. Keep experimenting!",
            'average': "Strong foundation in ML! Code more and experiment with datasets.",
            'needs_work': "ML/NLP is complex. Start with simple models and gradually increase complexity."
        }
    }
    
    subject_feed = feedbacks.get(subject, {})
    return subject_feed.get(performance, "Great effort! Keep learning and practicing. You're progressing well!")

# ==============================
# 5. FLASK WEB APPLICATION
# ==============================

app = Flask(__name__)

# Global models (initialized on startup)
subject_clf = None
subject_vectorizer = None
difficulty_clf = None
difficulty_vectorizer = None
df_data = None

@app.route("/", methods=["GET", "POST"])
def index():
    """Home page with subject and hours input"""
    return render_template("index.html")

@app.route("/classify", methods=["POST"])
def classify():
    """Classify text and generate personalized study plan"""
    try:
        text = request.form.get("text", "").strip()
        hours = int(request.form.get("hours", 10))
        
        if not text:
            return render_template("index.html", error="Please enter study text.")
        
        if hours < 1 or hours > 100:
            hours = 10
        
        # Predict subject
        subject, confidence = classify_subject(text, subject_clf, subject_vectorizer)
        
        # Predict difficulty
        X_diff = difficulty_vectorizer.transform([text])
        difficulty = difficulty_clf.predict(X_diff)[0]
        
        # Generate study materials
        plan = generate_contextual_plan(subject, hours, difficulty)
        quiz = generate_quiz(df_data, subject, num_questions=5)
        summary = summarize_text(text, max_sentences=3)
        tips = generate_study_tips(text, subject)
        resources = suggest_resources(df_data, subject)
        feedback = generate_motivational_feedback(subject, performance='good')
        
        # Create and save schedule
        schedule_data = {
            'Day': [day for day in range(1, 6)],
            'Activity': plan,
            'Subject': subject,
            'Duration': [f"{hours//5}h" for _ in range(5)]
        }
        schedule_df = pd.DataFrame(schedule_data)
        schedule_df.to_csv("schedule.csv", index=False)
        
        return render_template(
            "output.html",
            plan=plan,
            quiz=quiz,
            summary=summary,
            tips=tips,
            resources=resources,
            feedback=feedback,
            subject=subject,
            confidence=f"{confidence:.1f}%",
            original_text=text[:200],
            difficulty=difficulty
        )
    
    except Exception as e:
        return render_template("index.html", error=f"Error: {str(e)}")

@app.route("/download")
def download():
    """Download study schedule as CSV"""
    try:
        return send_file("schedule.csv", as_attachment=True, download_name="study_schedule.csv")
    except:
        return "Schedule not found. Generate a study plan first!"

@app.route("/stats")
def stats():
    """Display dataset statistics"""
    try:
        if df_data is None:
            return "No data available"
        
        stats_html = f"""
        <h2>Dataset Statistics</h2>
        <p>Total entries: {len(df_data)}</p>
        <p>Unique subjects: {df_data['subject'].nunique()}</p>
        <p>Subjects: {', '.join(df_data['subject'].unique())}</p>
        <img src="{url_for('static', filename='subject_distribution.png')}" style="max-width: 500px;">
        """
        return stats_html
    except:
        return "Error generating statistics"

# ==============================
# INITIALIZATION
# ==============================

if __name__ == "__main__":
    print("Starting AI Study Pal...")
    
    # Load and prepare data
    print("Loading educational texts...")
    df_data = load_and_clean_data("educational_texts.csv")
    print(f"Loaded {len(df_data)} educational texts")
    
    # Train classifiers
    print("Training subject classifier...")
    subject_clf, subject_vectorizer = train_subject_classifier(df_data)
    
    print("Training difficulty classifier...")
    difficulty_clf, difficulty_vectorizer = train_difficulty_classifier(df_data)
    
    # Generate visualizations
    print("Generating visualizations...")
    visualize_subjects(df_data)
    
    print("AI Study Pal is ready!")
    print("Visit http://127.0.0.1:5000/ in your browser")
    
    app.run(debug=True, host='127.0.0.1', port=5000)

# End of app.py
# By ☀️
