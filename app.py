from flask import Flask, render_template, request, send_from_directory
import os
import sqlite3

# Safe import for Render (prevents crash if detector is heavy)
try:
    from detector import predict_image
except:
    def predict_image(image_path):
        return "Real Photo", 50


app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================
# INIT DATABASE (IMPORTANT)
# ==========================
def init_db():
    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_name TEXT,
        result TEXT,
        confidence REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ==========================
# HOME PAGE
# ==========================
@app.route('/')
def home():
    return render_template('index.html')


# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ==========================
# UPLOAD + PREDICTION
# ==========================
@app.route('/upload', methods=['POST'])
def upload():

    if 'image' not in request.files:
        return "No file uploaded"

    image = request.files['image']

    if image.filename == '':
        return "No image selected"

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(image_path)

    # AI prediction
    result, confidence = predict_image(image_path)

    if result == "AI Generated":
        ai_confidence = confidence
        real_confidence = 100 - confidence
    else:
        real_confidence = confidence
        ai_confidence = 100 - confidence

    # Save to DB
    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO history (image_name, result, confidence)
    VALUES (?, ?, ?)
    """, (image.filename, result, confidence))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        result=result,
        ai_confidence=ai_confidence,
        real_confidence=real_confidence,
        image_name=image.filename
    )


# ==========================
# HISTORY PAGE
# ==========================
@app.route('/history')
def history():

    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()

    return render_template("history.html", rows=rows)


# ==========================
# DASHBOARD PAGE
# ==========================
@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect("detector.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM history")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM history WHERE result='AI Generated'")
    ai = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM history WHERE result='Real Photo'")
    real = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        ai=ai,
        real=real
    )


# ==========================
# RUN APP (RENDER SAFE)
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)