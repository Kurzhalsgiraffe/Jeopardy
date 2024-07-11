from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_access import Dao
from hardware import Buzzer
from question_selector import get_random_question_matrix, get_question_matrix_from_json_ids

app = Flask(__name__)
dao = Dao("jeopardy.db")
buzzer = Buzzer()


session_id = dao.get_next_session_id()
round_number = 1
rounds_json_filepath = "rounds.json"

@app.route('/')
def index():
    teams = dao.get_teams()
    answered_questions = dao.get_answered_questions_of_round(session_id, round_number)
    answered_question_ids = [question_id for question_id, team_id in answered_questions]
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
    global round_number #TODO Logik für Overflows
    round_number += 1
    return redirect(url_for('index'))

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
    buzzer.start_buzzer_loop()
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

@app.route('/answer_question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    buzzer.stop_buzzer_loop()
    buzzer_id = buzzer.get_last_pressed_buzzer_id()
    team_id = dao.get_team_id_for_buzzer_id(buzzer_id)
    if team_id:
        question = dao.get_question_by_id(question_id)
        if request.form['is_answer_correct'] == "true":
            dao.add_answer_to_session(session_id, round_number, question_id, team_id, question["points"])
            new_score = dao.get_team_score_by_id(team_id) + question["points"]
        else:
            dao.add_answer_to_session(session_id, round_number, question_id, team_id, - question["points"])
            new_score = dao.get_team_score_by_id(team_id) - question["points"]
            buzzer.start_buzzer_loop()
        dao.update_score(team_id, new_score)
        teams = dao.get_teams()
        return jsonify({"success": True, "message": "", "teams": [dict(row) for row in teams]})
    else:
        buzzer.start_buzzer_loop()
        pass
        return jsonify({"success": False, "message": "No Team pressed the Buzzzer", "teams":[]})

@app.route('/get_last_buzzer_event', methods=['GET'])
def get_last_buzzer_event():
    buzzer_id = buzzer.get_last_pressed_buzzer_id()
    team_id = dao.get_team_id_for_buzzer_id(buzzer_id)
    team_name = dao.get_team_name_by_id(team_id)
    return jsonify({"buzzer_id":buzzer_id, "team_id": team_id, "team_name": team_name})

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
    is_active = request.form.get('active') == 'true'  # Convert string to boolean
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
