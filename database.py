# database_setup.py
import sqlite3

def init_db():
    conn = sqlite3.connect('jeopardy.db')
    cursor = conn.cursor()

    # Create teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            score INTEGER DEFAULT 0
        )
    ''')

    # Create questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            type TEXT,
            points INTEGER
        )
    ''')

    # Create a table for tracking selected questions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selected_questions (
            question_id INTEGER,
            team_id INTEGER,
            FOREIGN KEY(question_id) REFERENCES questions(id),
            FOREIGN KEY(team_id) REFERENCES teams(id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
