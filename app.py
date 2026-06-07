
from flask import Flask, render_template, request, send_from_directory
import os
import sqlite3

# IMPORTANT: import your AI model
from detector import predict_image

print("Database Path:", os.path.abspath("detector.db"))

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Home Page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

# Upload Image + AI Detection
@app.route('/upload', methods=['POST'])
def upload():

    image = request.files['image']

    if image.filename == '':
        return "No Image Selected"

    # Save image
    image_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        image.filename
    )

    image.save(image_path)

    # ==========================
    # REAL AI DETECTION (NO RANDOM)
    # ==========================
    result, confidence = predict_image(image_path)

    if result == "AI Generated":
        ai_confidence = confidence
        real_confidence = 100 - confidence
    else:
        real_confidence = confidence
        ai_confidence = 100 - confidence

    # Save to Database
    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO history
    (image_name, result, confidence)
    VALUES (?, ?, ?)
    """,
    (
        image.filename,
        result,
        confidence
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        result=result,
        ai_confidence=ai_confidence,
        real_confidence=real_confidence,
        image_name=image.filename
    )


# History Page
@app.route('/history')
def history():

    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM history
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        rows=rows
    )


# Dashboard Page
@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM history")
    total = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM history
    WHERE result='AI Generated'
    """)
    ai = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM history
    WHERE result='Real Photo'
    """)
    real = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        ai=ai,
        real=real
    )


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )

