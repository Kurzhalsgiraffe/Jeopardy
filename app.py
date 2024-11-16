import json
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, stream_with_context
import time
from datetime import datetime
from database_access import Dao
import question_selector

app = Flask(__name__)
dao = Dao("jeopardy.db")

buzzer_unlocked_semaphore = False
last_pressed_buzzer_id = None
last_buzzer_ping = None
selected_question_id = None
buzzer_stream_active = False
quizmaster_polling_interval_seconds = 1.5
buzzer_polling_interval_seconds = 1

session_id = dao.get_next_session_id()
round_number = 1
rounds_json_filepath = "rounds.json"
question_selector.check_integrity(dao, rounds_json_filepath)

def increase_round_number():
    with open(rounds_json_filepath, 'r') as file:
        rounds_data = json.load(file)
    total_rounds_count = len(rounds_data)

    global round_number
    if round_number < total_rounds_count:
        round_number += 1

def decrease_round_number():
    global round_number
    if round_number > 1:
        round_number -= 1

def activate_buzzer():
    global buzzer_unlocked_semaphore
    global last_pressed_buzzer_id
    last_pressed_buzzer_id = None
    buzzer_unlocked_semaphore = True

def deactivate_buzzer():
    global buzzer_unlocked_semaphore
    buzzer_unlocked_semaphore = False

@app.route('/')
def index():
    global selected_question_id
    selected_question_id = None
    teams = dao.get_teams()
    answered_questions = dao.get_answered_questions_of_round(session_id, round_number)
    answered_question_ids = [question_id for question_id, _ in answered_questions]
    question_matrix = question_selector.get_question_matrix_from_json_ids(dao, round_number, rounds_json_filepath)
    return render_template('index.html', question_matrix=question_matrix, answered_question_ids=answered_question_ids, teams=teams, round_number=round_number, last_buzzer_ping=last_buzzer_ping)

@app.route('/quizmaster')
def quizmaster():
    return render_template('quizmaster.html')

@app.route('/quizmaster_stream')
def quizmaster_stream():
    def event_stream():
        while True:
            question_object = dao.get_question_by_id(selected_question_id)
            question = question_object['question'] if question_object else None
            answer = question_object['answer'] if question_object else None
            data = {
                "question": question,
                "answer": answer
            }
            yield f"data: {json.dumps(data)}\n\n" # Yield the JSON object as a string
            time.sleep(quizmaster_polling_interval_seconds)
    return Response(stream_with_context(event_stream()), content_type='text/event-stream')

@app.route('/buzzer_event_stream')
def buzzer_event_stream():
    def event_stream():
        global buzzer_stream_active
        buzzer_stream_active = True
        while buzzer_stream_active:
            if last_pressed_buzzer_id:
                team_id = dao.get_team_id_for_buzzer_id(last_pressed_buzzer_id) if last_pressed_buzzer_id else None
                team_name = dao.get_team_name_by_id(team_id) if team_id else None
                buzzer_sound = dao.get_team_buzzer_sound_by_team_id(team_id)
                data = {
                    "buzzer_id": last_pressed_buzzer_id,
                    "buzzer_sound": buzzer_sound,
                    "team_id": team_id,
                    "team_name": team_name
                }
                yield f"data: {json.dumps(data)}\n\n"
                buzzer_stream_active = False
            time.sleep(buzzer_polling_interval_seconds)
    return Response(stream_with_context(event_stream()), content_type='text/event-stream')

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

@app.route('/previous_round', methods=['POST'])
def previous_round():
    decrease_round_number()
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
    global selected_question_id
    selected_question_id = question_id
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
    global buzzer_stream_active
    global selected_question_id
    buzzer_stream_active = False
    selected_question_id = None
    return jsonify({"success": True, "message": "Buzzer deactivated"})

@app.route('/answer_question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    deactivate_buzzer()
    global last_pressed_buzzer_id
    global selected_question_id
    team_id = dao.get_team_id_for_buzzer_id(last_pressed_buzzer_id)
    last_pressed_buzzer_id = None
    if team_id:
        question = dao.get_question_by_id(question_id)
        if request.form['is_answer_correct'] == "true":
            dao.add_answer_to_session(session_id, round_number, question_id, team_id, question["points"])
            new_score = dao.get_team_score_by_id(team_id) + question["points"]
            selected_question_id = None
        else:
            dao.add_answer_to_session(session_id, round_number, question_id, team_id, - question["points"])
            new_score = dao.get_team_score_by_id(team_id) - question["points"]
            activate_buzzer()
        dao.update_score(team_id, new_score)
        teams = dao.get_teams()
        return jsonify({"success": True, "message": "Processed Answer", "teams": [dict(row) for row in teams]})
    else:
        activate_buzzer()
        return jsonify({"success": False, "message": "No Team pressed the Buzzzer", "teams":[]})

@app.route('/skip_question/<int:question_id>', methods=['POST'])
def skip_question(question_id):
    dao.add_answer_to_session(session_id, round_number, question_id, None, 0)
    return jsonify({"success": True, "message": "Question skipped"})

@app.route('/is_buzzer_unlocked', methods=['GET'])
def is_buzzer_unlocked():
    global last_buzzer_ping
    last_buzzer_ping = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({"buzzer_unlocked_semaphore": buzzer_unlocked_semaphore})

@app.route('/push_buzzer', methods=['POST'])
def push_buzzer():
    global last_pressed_buzzer_id
    buzzer_id = request.args.get("buzzer_id")
    assigned_buzzer_ids = dao.get_assigned_buzzer_ids()
    if buzzer_id and assigned_buzzer_ids and int(buzzer_id) in assigned_buzzer_ids:
        if buzzer_unlocked_semaphore:
            last_pressed_buzzer_id = buzzer_id
            deactivate_buzzer()
            return jsonify({"success": True, "message": f"Buzzer {buzzer_id} was pressed"})
        return jsonify({"success": False, "message": f"Buzzers are locked"}), 500
    return jsonify({"success": False, "message": f"Buzzer {buzzer_id} not assigned"}), 500

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

@app.route('/update_team_buzzer_sound', methods=['POST'])
def update_team_buzzer_sound():
    team_id = request.form.get('team_id')
    buzzer_sound = request.form.get('buzzer_sound')

    if not team_id:
        return jsonify({"success": False, "message": "Team ID is required"})
    if buzzer_sound:
        dao.update_team_buzzer_sound(team_id, buzzer_sound)
    else:
        dao.update_team_buzzer_sound(team_id, None)
    teams = dao.get_teams()
    return jsonify({"success": True, "message": "Team Buzzer Sound successfully changed", "teams": [dict(row) for row in teams]})

@app.route('/get_buzzer_sounds', methods=['GET'])
def get_buzzer_sounds():
    sounds_directory = os.path.join(app.static_folder, 'sounds/team_sounds')
    try:
        sound_files = sorted([f for f in os.listdir(sounds_directory) if os.path.isfile(os.path.join(sounds_directory, f))])
        teams = dao.get_teams()
        return jsonify({"success": True, "sounds": sound_files, "teams": [dict(row) for row in teams]})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving sounds: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
