# database_setup.py
import sqlite3
import traceback

def error_handler(err,trace):
    """Print Errors that can occurr in the DB Methods"""
    print(f"SQLite error: {err.args}")
    print("Exception class is: ", err.__class__)
    print("SQLite traceback: ")
    print(trace)

class Dao:
    """Provides all the needed Methods to interact with the SQLite Database"""
    def __init__(self, dbfile:str) -> None:
        try:
            sqlite3.threadsafety = 1
            self.dbfile = dbfile
            self.create_tables()

        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_db_connection(self):
        """Get a connection to the database"""
        try:
            conn = sqlite3.connect(self.dbfile, check_same_thread=False)
            cursor = conn.cursor()
            cursor.row_factory = sqlite3.Row
            return conn, cursor

        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def vacuum(self) -> None:
        """Run a vacuum on the Database"""
        try:
            conn, cursor = self.get_db_connection()
            sql = """VACUUM"""
            cursor.execute(sql)
            conn.close()

        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def create_tables(self) -> None:
        """Create the database tables if they dont already exist"""
        try:
            conn, cursor = self.get_db_connection()

            sql = """CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER DEFAULT 0
                )"""
            cursor.execute(sql)

            sql = """CREATE TABLE IF NOT EXISTS questions (
                questions_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT,
                type TEXT,
                points INTEGER
                )"""
            cursor.execute(sql)

            sql = """CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER,
                question_id INTEGER,
                team_id INTEGER,
                points INTEGER,
                PRIMARY KEY (session_id, question_id, team_id),
                FOREIGN KEY(question_id) REFERENCES questions(id),
                FOREIGN KEY(team_id) REFERENCES teams(id)
                )"""
            cursor.execute(sql)
            conn.close()

        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_questions_by_category(self, session_id, category) -> list:
        try:
            conn, cursor = self.get_db_connection()
            sql = """SELECT q.*
                FROM questions q
                LEFT JOIN sessions sq
                ON q.id = sq.question_id AND sq.session_id = ?
                WHERE q.category = ?
                AND sq.question_id IS NULL"""

            questions =cursor.execute(sql, (session_id, category)).fetchall()
            conn.close()
            return questions
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_question_by_id(self, question_id) -> sqlite3.Row:
        try:
            conn, cursor = self.get_db_connection()
            question = cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
            conn.close()
            return question
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_teams(self) -> list:
        try:
            conn, cursor = self.get_db_connection()
            teams = cursor.execute('SELECT * FROM teams').fetchall()
            conn.close()
            return teams
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def add_team(self, team_name) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('INSERT INTO teams (name) VALUES (?)', (team_name,))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def remove_team(self, team_id) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('DELETE FROM teams WHERE id = ?', (team_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def update_score(self, team_id, new_score) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('UPDATE teams SET score = ? WHERE id = ?', (new_score, team_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def mark_question_as_played(self, session_id, question_id, team_id, points) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('INSERT INTO sessions (session_id, question_id, team_id, points) VALUES (?, ?, ?, ?)', (session_id, question_id, team_id, points))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())
