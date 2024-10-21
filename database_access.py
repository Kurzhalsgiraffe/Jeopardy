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

    def get_db_connection(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
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
                score INTEGER DEFAULT 0,
                buzzer_id INTEGER,
                is_active INTEGER,
                buzzer_sound TEXT
                )"""
            cursor.execute(sql)

            sql = """CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT,
                type TEXT,
                points INTEGER
                )"""
            cursor.execute(sql)

            sql = """CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER,
                round_number INTEGER,
                question_id INTEGER,
                team_id INTEGER,
                points INTEGER,
                attempt_time DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
                PRIMARY KEY (session_id, round_number, question_id, team_id, attempt_time),
                FOREIGN KEY(question_id) REFERENCES questions(question_id),
                FOREIGN KEY(team_id) REFERENCES teams(team_id)
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
                ON q.question_id = sq.question_id AND sq.session_id = ?
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
            question = cursor.execute('SELECT * FROM questions WHERE question_id = ?', (question_id,)).fetchone()
            conn.close()
            return question
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_multiple_questions_by_ids(self, question_ids):
        try:
            conn, cursor = self.get_db_connection()

            # Create a placeholder for each question ID
            placeholders = ','.join('?' for _ in question_ids)
            query = f'SELECT * FROM questions WHERE question_id IN ({placeholders}) ORDER BY points ASC'

            questions = cursor.execute(query, question_ids).fetchall()
            conn.close()
            return questions
        except sqlite3.Error as err:
            error_handler(err, traceback.format_exc())

    def get_teams(self) -> list:
        try:
            conn, cursor = self.get_db_connection()
            teams = cursor.execute('SELECT * FROM teams').fetchall()
            conn.close()
            return teams
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_team_score_by_id(self, team_id) -> int:
        try:
            conn, cursor = self.get_db_connection()
            score_row = cursor.execute('SELECT score FROM teams WHERE team_id = ?', (team_id,)).fetchone()
            conn.close()
            if score_row is None:
                return None
            return score_row['score']
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
            cursor.execute('DELETE FROM teams WHERE team_id = ?', (team_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def toggle_team_activation(self, team_id, is_active) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('UPDATE teams SET is_active = ? WHERE team_id = ?', (is_active, team_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def update_buzzer_id(self, team_id, buzzer_id) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('UPDATE teams SET buzzer_id = ? WHERE team_id = ?', (buzzer_id, team_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_buzzer_id_for_team(self, team_id):
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT buzzer_id FROM teams WHERE team_id = ?', (team_id,)).fetchone()
            conn.close()
            if result:
                return result[0]
            return None
        except sqlite3.Error as err:
            error_handler(err, traceback.format_exc())
            return None

    def get_assigned_buzzer_ids(self):
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT buzzer_id FROM teams').fetchall()
            conn.close()
            if result:
                return [r["buzzer_id"] for r in result]
            return None
        except sqlite3.Error as err:
            error_handler(err, traceback.format_exc())
            return None

    def get_team_id_for_buzzer_id(self, buzzer_id):
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT team_id FROM teams WHERE buzzer_id = ?', (buzzer_id,)).fetchone()
            conn.close()
            if result:
                return result[0]
            return None
        except sqlite3.Error as err:
            error_handler(err, traceback.format_exc())
            return None

    def get_team_name_by_id(self, team_id):
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT name FROM teams WHERE team_id = ?', (team_id,)).fetchone()
            conn.close()
            if result:
                return result[0]
            return None
        except sqlite3.Error as err:
            error_handler(err, traceback.format_exc())
            return None

    def update_team_buzzer_sound(self, team_id, buzzer_sound):
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('UPDATE teams SET buzzer_sound = ? WHERE team_id = ?', (buzzer_sound, team_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_team_buzzer_sound_by_team_id(self, team_id):
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT buzzer_sound FROM teams WHERE team_id = ?', (team_id,)).fetchone()
            conn.close()
            if result:
                return result[0]
            return None
        except sqlite3.Error as err:
            error_handler(err, traceback.format_exc())
            return None

    def update_score(self, team_id, new_score) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('UPDATE teams SET score = ? WHERE team_id = ?', (new_score, team_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def add_answer_to_session(self, session_id, round_number, question_id, team_id, points) -> None:
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute('INSERT INTO sessions (session_id, round_number, question_id, team_id, points) VALUES (?, ?, ?, ?, ?)', (session_id, round_number, question_id, team_id, points))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            error_handler(err,traceback.format_exc())

    def get_answered_questions_of_round(self, session_id, round_number) -> list:
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT question_id, team_id FROM sessions WHERE session_id = ? AND round_number = ? AND points >= 0', (session_id, round_number)).fetchall()
            conn.close()
            return [(r["question_id"], r["team_id"]) for r in result]
        except sqlite3.Error as err:
            self.error_handler(err, traceback.format_exc())
            return None

    def get_next_session_id(self) -> int:
        try:
            conn, cursor = self.get_db_connection()
            result = cursor.execute('SELECT MAX(session_id) FROM sessions').fetchone()
            conn.close()
            if result[0] is None:
                return 1
            else:
                return result[0] + 1
        except sqlite3.Error as err:
            self.error_handler(err, traceback.format_exc())
            return None
