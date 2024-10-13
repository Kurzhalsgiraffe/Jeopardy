# TODO: Buzzer connected status irgendwo auf der Website anzeigen?
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from database_access import Dao
from question_selector import get_question_matrix_from_json_ids
from api_secrets import SECRET_API_KEY

app = Flask(__name__)
dao = Dao("jeopardy.db")

buzzer_active_semaphore = False
last_pressed_buzzer_id = None

session_id = dao.get_next_session_id()
round_number = 1
rounds_json_filepath = "rounds.json"

def increase_round_number(rounds_json_filepath):
    with open(rounds_json_filepath, 'r') as file:
        rounds_data = json.load(file)
    total_rounds_count = len(rounds_data)

    global round_number
    if round_number < total_rounds_count:
        round_number += 1
    else:
        round_number = 1

def is_api_key_valid():
    api_key = request.headers.get("X-API-KEY")
    return api_key == SECRET_API_KEY

def activate_buzzer():
    global buzzer_active_semaphore
    global last_pressed_buzzer_id
    last_pressed_buzzer_id = None
    buzzer_active_semaphore = True

def deactivate_buzzer():
    global buzzer_active_semaphore
    buzzer_active_semaphore = False

@app.route('/')
def index():
    teams = dao.get_teams()
    answered_questions = dao.get_answered_questions_of_round(session_id, round_number)
    answered_question_ids = [question_id for question_id, _ in answered_questions]
    question_matrix = get_question_matrix_from_json_ids(dao, round_number, rounds_json_filepath)
    return render_template('index.html', question_matrix=question_matrix, answered_question_ids=answered_question_ids, teams=teams, round_number=round_number)

@app.route('/new_session', methods=['POST'])
def new_session():
    global session_id
    global round_number
    round_number = 1
    session_id = dao.get_next_session_id()
    return redirect(url_for('index'))

@app.route('/next_round', methods=['POST'])
def next_round():
    increase_round_number()
    return redirect(url_for('index'))

@app.route('/add_team', methods=['POST'])
def add_team():
    team_name = request.form['team-name-input']
    dao.add_team(team_name)
    return redirect(url_for('index'))

@app.route('/remove_team', methods=['POST'])
def remove_team():
    team_id = request.form['team_id']
    dao.remove_team(team_id)
    return redirect(url_for('index'))

@app.route('/select_question/<int:question_id>', methods=['POST'])
def select_question(question_id):
    activate_buzzer()
    question = dao.get_question_by_id(question_id)
    return jsonify({
        'question_id': question['question_id'],
        'question': question['question'],
        'answer': question['answer'],
        'category': question['category'],
        'type': question['type'],
        'points': question['points'],
        'answered_questions': [{i[0]:(dao.get_team_name_by_id(i[1]), dao.get_buzzer_id_for_team(i[1]))} for i in dao.get_answered_questions_of_round(session_id, round_number)]
    })

@app.route('/unselect_question', methods=['POST'])
def unselect_question():
    deactivate_buzzer()
    return jsonify({"success": True, "message": "Buzzer deactivated"})

@app.route('/answer_question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    deactivate_buzzer()
    global last_pressed_buzzer_id
    team_id = dao.get_team_id_for_buzzer_id(last_pressed_buzzer_id)
    if team_id:
        question = dao.get_question_by_id(question_id)
        if request.form['is_answer_correct'] == "true":
            dao.add_answer_to_session(session_id, round_number, question_id, team_id, question["points"])
            new_score = dao.get_team_score_by_id(team_id) + question["points"]
        else:
            dao.add_answer_to_session(session_id, round_number, question_id, team_id, - question["points"])
            new_score = dao.get_team_score_by_id(team_id) - question["points"]
            activate_buzzer()
        dao.update_score(team_id, new_score)
        teams = dao.get_teams()
        return jsonify({"success": True, "message": "", "teams": [dict(row) for row in teams]})
    else:
        activate_buzzer()
        pass
        return jsonify({"success": False, "message": "No Team pressed the Buzzzer", "teams":[]})

@app.route('/get_last_buzzer_event', methods=['GET'])
def get_last_buzzer_event():
    team_id = dao.get_team_id_for_buzzer_id(last_pressed_buzzer_id) if last_pressed_buzzer_id else None
    team_name = dao.get_team_name_by_id(team_id) if team_id else None
    return jsonify({"buzzer_id":last_pressed_buzzer_id, "team_id": team_id, "team_name": team_name})

@app.route('/is_buzzer_active', methods=['GET'])
def is_buzzer_active():
    if not is_api_key_valid():
        abort(403)
    return jsonify({"buzzer_active_semaphore": buzzer_active_semaphore})

@app.route('/push_buzzer', methods=['POST'])
def push_buzzer():
    global last_pressed_buzzer_id
    if not is_api_key_valid():
        abort(403)
    buzzer_id = request.args.get("buzzer_id")
    assigned_buzzer_ids = dao.get_assigned_buzzer_ids()
    if int(buzzer_id) in assigned_buzzer_ids:
        if buzzer_active_semaphore:
            last_pressed_buzzer_id = buzzer_id
            deactivate_buzzer()
            return jsonify({"success": True, "message": f"Buzzer {buzzer_id} was pressed"})
        return jsonify({"success": False, "message": f"Buzzers not active"})
    return jsonify({"success": False, "message": f"Buzzer {buzzer_id} not assigned"})

@app.route('/update_score', methods=['POST'])
def update_score():
    team_id = request.form['team_id']
    score_delta = request.form['score_delta']
    old_score = dao.get_team_score_by_id(team_id)
    dao.update_score(team_id, old_score+int(score_delta))
    teams = dao.get_teams()
    return jsonify([dict(row) for row in teams])

@app.route('/toggle_team_activation', methods=['POST'])
def toggle_team_activation():
    team_id = request.form['team_id']
    is_active = request.form.get('active') == 'true'
    dao.toggle_team_activation(team_id, is_active)
    teams = dao.get_teams()
    return jsonify([dict(row) for row in teams])

@app.route('/update_buzzer_id', methods=['POST'])
def update_buzzer_id():
    team_id = request.form.get('team_id')
    buzzer_id = request.form.get('buzzer_id')

    if not team_id:
        return jsonify({"success": False, "message": "Team ID is required"})
    if buzzer_id:
        current_team_with_buzzer_id = dao.get_team_id_for_buzzer_id(buzzer_id)
        if current_team_with_buzzer_id:
            dao.update_buzzer_id(current_team_with_buzzer_id, None)
        dao.update_buzzer_id(team_id, buzzer_id)
    else:
        dao.update_buzzer_id(team_id, None)
    teams = dao.get_teams()
    return jsonify({"success": True, "message": "Team ID successfully changed", "teams": [dict(row) for row in teams]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
