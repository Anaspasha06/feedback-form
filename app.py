from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io

app = Flask(__name__)

# Local SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    rating = db.Column(db.String(10))
    comments = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)


# Create database tables
with app.app_context():
    db.create_all()


# Home page → Feedback Form
@app.route('/')
def index():
    return render_template('index.html')


# Submit feedback
@app.route('/submit', methods=['POST'])
def submit():

    name = request.form.get('name')
    email = request.form.get('email')
    rating = request.form.get('rating')
    comments = request.form.get('comments')

    if not name or not email or not rating:
        return jsonify({"status": "error", "message": "Please fill all required fields."})

    feedback = Feedback(
        name=name,
        email=email,
        rating=rating,
        comments=comments
    )

    db.session.add(feedback)
    db.session.commit()

    return jsonify({"status": "success", "message": "🎉 Thank you! Your feedback has been submitted."})


# Admin dashboard
@app.route('/dashboard')
def dashboard():

    feedbacks = Feedback.query.order_by(Feedback.date.desc()).all()

    return render_template('dashboard.html', feedbacks=feedbacks)


# Fetch single feedback
@app.route('/feedback/<int:fid>')
def get_feedback(fid):

    feedback = Feedback.query.get_or_404(fid)

    data = {
        "id": feedback.id,
        "name": feedback.name,
        "email": feedback.email,
        "rating": feedback.rating,
        "comments": feedback.comments,
        "date": feedback.date.strftime("%d-%m-%Y"),
        "time": feedback.date.strftime("%I:%M %p")
    }

    return jsonify({"status": "success", "data": data})


# Delete feedback
@app.route('/feedback/<int:fid>/delete', methods=['POST'])
def delete_feedback(fid):

    feedback = Feedback.query.get_or_404(fid)

    db.session.delete(feedback)
    db.session.commit()

    return jsonify({"status": "success", "message": "Feedback deleted."})


# Export CSV
@app.route('/export')
def export_csv():

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["id", "name", "email", "rating", "comments", "date", "time"])

    feedbacks = Feedback.query.order_by(Feedback.date.desc()).all()

    for f in feedbacks:
        writer.writerow([
            f.id,
            f.name,
            f.email,
            f.rating,
            (f.comments or "").replace("\n", " "),
            f.date.strftime("%d-%m-%Y"),
            f.date.strftime("%I:%M %p")
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=feedback_export.csv"}
    )


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
