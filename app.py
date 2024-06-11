# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_access import Dao
import random

app = Flask(__name__)
dao = Dao("jeopardy.db")

session_id = dao.get_next_session_id()
categorized_questions = None
answered_question_ids = set()

@app.route('/')
def index():
    global categorized_questions
    if not categorized_questions:
        categorized_questions = get_random_question_dict()
    teams = dao.get_teams()
    return render_template('index.html', categorized_questions=categorized_questions, teams=teams, answered_question_ids=answered_question_ids)

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
        'answer': question['answer'],
        'category': question['category'],
        'type': question['type'],
        'points': question['points']
    })

@app.route('/answer_question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    team_id = 1 # TODO: REPLACE -- Kommt von Buzzern
    question = dao.get_question_by_id(question_id)
    points = question["points"]
    is_answer_correct = request.form['is_answer_correct']
    if is_answer_correct == "true":
        dao.add_answer_to_session(session_id, question_id, team_id, points)
        new_score = dao.get_team_score_by_id(team_id) + points
        answered_question_ids.add(question_id)
    else:
        dao.add_answer_to_session(session_id, question_id, team_id, -points)
        new_score = dao.get_team_score_by_id(team_id) - points
    dao.update_score(team_id, new_score)
    teams = dao.get_teams()
    return jsonify([dict(row) for row in teams])

@app.route('/update_score', methods=['POST'])
def update_score():
    team_id = request.form['team_id']
    score_delta = request.form['score_delta']
    old_score = dao.get_team_score_by_id(team_id)
    dao.update_score(team_id, old_score+int(score_delta))
    teams = dao.get_teams()
    return jsonify([dict(row) for row in teams])


def get_random_question_dict():
    categorized_questions = dict()
    for category in ["Filme", "Geographie", "Kultur", "Politik", "Sport"]:
        questions_list = dao.get_questions_by_category(session_id, category=category)
        if questions_list:
            random.shuffle(questions_list)
            categorized_questions[category] = dict()
            for points_value in [100, 200, 300, 400, 500]:
                questions_with_specific_points = [q for q in questions_list if q["points"] == points_value]
                if questions_with_specific_points:
                    categorized_questions[category][points_value] = random.choice(questions_with_specific_points)
    return categorized_questions


if __name__ == "__main__":
    app.run(debug=True)
