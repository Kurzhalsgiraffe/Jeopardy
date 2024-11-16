import json
import random

def get_random_question_matrix(dao, categories):
    question_matrix = []
    for category in categories:
        questions_list = dao.get_questions_by_category(category=category)
        if questions_list:
            random.shuffle(questions_list)
            questions_of_category = []
            for points_value in [100, 200, 300, 400, 500]:
                questions_with_specific_points = [q["question_id"] for q in questions_list if q["points"] == points_value]
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
                if question_ids:
                    question_matrix.append(dao.get_multiple_questions_by_ids(question_ids))
    return question_matrix

def check_integrity(dao, json_filepath):
    with open(json_filepath, 'r') as file:
        parsed_data = json.load(file)
        for json_obj in parsed_data:
            round_number = json_obj.get("round_number")
            questions = json_obj.get("questions")
            if questions:
                for category in questions:
                    question_ids = questions[category]
                    if question_ids:
                        questions_of_category = dao.get_multiple_questions_by_ids(question_ids)
                        categories = {q["category"] for q in questions_of_category}
                        assert len(categories) == 1, f"Round {round_number}, Category {categories}: Found more than one Category"


# from database_access import Dao
# dao = Dao("jeopardy.db")
# rounds_json_filepath = "rounds.json"

# output = {
#     "round_number": 4,
#     "questions": {}
# }
# categories = ["Sport", "Geographie", "Allgemeinwissen", "Wörter", "Kultur"]
# for i, c in enumerate(get_random_question_matrix(dao, categories)):
#     output["questions"][categories[i]] = c
# formatted_output = json.dumps(output, indent=4)
# print(formatted_output)