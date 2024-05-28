import sqlite3

# Listen zum Speichern der Fragen und Antworten
questions = []
answers = []

# Fragen und Antworten aus den Dateien einlesen
with open("f.txt", "r", encoding="utf-8") as questions_file:
    with open("a.txt", "r", encoding="utf-8") as answers_file:
        questions_lines = questions_file.readlines()
        answers_lines = answers_file.readlines()
        assert len(answers_lines) == len(questions_lines), "Die Anzahl der Fragen und Antworten muss gleich sein."

        # Verarbeitung der Fragen und Antworten ohne Abhängigkeit von ". "
        for question_line in questions_lines:
            # Entferne die führende Nummerierung und den Punkt
            question = question_line.split(". ", 1)[1].strip()
            questions.append(question)

        for answer_line in answers_lines:
            # Entferne die führende Nummerierung und den Punkt
            answer = answer_line.split(". ", 1)[1].strip()
            answers.append(answer)

# Verbindung zur SQLite3-Datenbank herstellen
conn = sqlite3.connect('quiz.db')

# Einen Cursor erstellen
cursor = conn.cursor()

# SQL-Befehl zum Einfügen von Daten
insert_query = '''
INSERT INTO quiz (question, answer, category, type, points)
VALUES (?, ?, NULL, NULL, NULL);
'''

# Fragen und Antworten in die Datenbank einfügen
for question, answer in zip(questions, answers):
    cursor.execute(insert_query, (question, answer))

# Änderungen speichern
conn.commit()

# Verbindung schließen
conn.close()
