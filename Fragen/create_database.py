import sqlite3

# Verbindung zur SQLite3-Datenbank herstellen (oder Datenbank erstellen, falls sie nicht existiert)
conn = sqlite3.connect('quiz.db')

# Einen Cursor erstellen
cursor = conn.cursor()

# SQL-Befehl zum Erstellen der Tabelle
create_table_query = '''
CREATE TABLE IF NOT EXISTS quiz (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,
    type TEXT,
    points INTEGER
);
'''

# SQL-Befehl ausführen
cursor.execute(create_table_query)

# Änderungen speichern
conn.commit()

# Verbindung schließen
conn.close()