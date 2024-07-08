import json
import random

def get_random_question_matrix(dao, session_id):
    question_matrix = []
    for category in ["Filme", "Geographie", "Kultur", "Politik", "Sport"]:
        questions_list = dao.get_questions_by_category(session_id, category=category)
        if questions_list:
            random.shuffle(questions_list)
            questions_of_category = []
            for points_value in [100, 200, 300, 400, 500]:
                questions_with_specific_points = [q for q in questions_list if q["points"] == points_value]
                if questions_with_specific_points:
                    questions_of_category.append(random.choice(questions_with_specific_points))
            question_matrix.append(questions_of_category)
    return question_matrix

def get_question_matrix_from_json_ids(dao, round_number, json_filepath):
    question_matrix = []
    with open(json_filepath, 'r') as file:
        parsed_data = json.load(file)
        json_obj = next((item for item in parsed_data if item["round_number"] == round_number), None)
        questions = json_obj.get("questions")
        if questions:
            for category in questions:
                question_ids = questions[category]
                print(question_ids)
                if question_ids:
                    question_matrix.append(dao.get_multiple_questions_by_ids(question_ids))
    return question_matrix
