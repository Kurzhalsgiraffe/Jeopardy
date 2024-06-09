# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_access import Dao

app = Flask(__name__)
dao = Dao("jeopardy.db")

session_id = 1

@app.route('/')
def index():
    questions = dao.get_questions_by_category(session_id, category="Kultur")
    teams = dao.get_teams()
    return render_template('index.html', questions=questions, teams=teams)

@app.route('/add_team', methods=['POST'])
def add_team():
    team_name = request.form['name']
    dao.add_team(team_name)
    return redirect(url_for('index'))

@app.route('/remove_team', methods=['POST'])
def remove_team():
    team_id = request.form['team_id']
    dao.remove_team(team_id)
    return redirect(url_for('index'))

@app.route('/select_question/<int:question_id>', methods=['POST'])
def select_question(question_id):
    question = dao.get_question_by_id(question_id)
    return jsonify({
        'question': question['question'],
        'points': question['points']
    })

@app.route('/answer_question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    is_answer_correct = request.form['is_answer_correct']
    team_id = 1 # TODO: REPLACE -- Kommt von Buzzern
    question = dao.get_question_by_id(question_id)
    points = question["points"]
    dao.mark_question_as_selected(session_id, question_id, team_id, points)
    return redirect(url_for('index'))

@app.route('/update_score', methods=['POST'])
def update_score():
    team_id = request.form['team_id']
    new_score = request.form['score']
    dao.update_score(team_id, new_score)
    return '', 204


if __name__ == "__main__":
    app.run(debug=True)
