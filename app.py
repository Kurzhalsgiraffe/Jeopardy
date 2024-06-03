# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('jeopardy.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions').fetchall()
    teams = conn.execute('SELECT * FROM teams').fetchall()
    conn.close()
    return render_template('index.html', questions=questions, teams=teams)

@app.route('/add_team', methods=['POST'])
def add_team():
    team_name = request.form['name']
    conn = get_db_connection()
    conn.execute('INSERT INTO teams (name) VALUES (?)', (team_name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/select_question/<int:question_id>', methods=['POST'])
def select_question(question_id):
    team_id = request.form['team_id']
    conn = get_db_connection()
    question = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
    conn.execute('INSERT INTO selected_questions (question_id, team_id) VALUES (?, ?)', (question_id, team_id))
    conn.commit()
    conn.close()
    return jsonify({
        'question': question['question'],
        'points': question['points']
    })

@app.route('/answer_question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    team_id = request.form['team_id']
    given_answer = request.form['answer']
    conn = get_db_connection()
    question = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
    team = conn.execute('SELECT * FROM teams WHERE id = ?', (team_id,)).fetchone()
    if given_answer.lower() == question['answer'].lower():
        new_score = team['score'] + question['points']
    else:
        new_score = team['score'] - question['points']
    conn.execute('UPDATE teams SET score = ? WHERE id = ?', (new_score, team_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_score', methods=['POST'])
def update_score():
    team_id = request.form['team_id']
    new_score = request.form['score']
    conn = get_db_connection()
    conn.execute('UPDATE teams SET score = ? WHERE id = ?', (new_score, team_id))
    conn.commit()
    conn.close()
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)
