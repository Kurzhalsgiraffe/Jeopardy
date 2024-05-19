import sqlite3

# Listen zum Speichern der Fragen und Antworten
questions = []
answers = []

# Fragen und Antworten aus den Dateien einlesen
with open("f.txt", "r", encoding="utf-8") as fragen:
    with open("a.txt", "r", encoding="utf-8") as antworten:
        f = fragen.readlines()
        a = antworten.readlines()
        assert len(a) == len(f), "Die Anzahl der Fragen und Antworten muss gleich sein."
        for i in range(len(f)):
            fr = f[i]
            an = a[i]
            questions.append(fr.split(". ")[1].strip())
            answers.append(an.split(". ")[1].strip())

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
