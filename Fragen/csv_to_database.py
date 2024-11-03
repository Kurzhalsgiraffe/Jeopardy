import sqlite3
import csv

def import_from_csv(db_path, table_name, csv_path):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # CSV-Datei lesen
    with open(csv_path, 'r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')

        # Spaltennamen aus der ersten Zeile der CSV-Datei abrufen
        try:
            column_names = [col.strip().replace('"', '') for col in next(csv_reader)]  # Clean up column names
            print(f"Column names: {column_names}")  # Debugging line
            if len(column_names) != 6:
                raise ValueError(f"CSV does not contain exactly 6 columns: {column_names}")
        except StopIteration:
            raise ValueError("CSV file is empty")

        # Tabelle erstellen, wenn sie nicht existiert
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {column_names[0]} INTEGER PRIMARY KEY,
                {column_names[1]} TEXT,
                {column_names[2]} TEXT,
                {column_names[3]} TEXT,
                {column_names[4]} TEXT,
                {column_names[5]} INTEGER
            )
        """)

        # Daten in die Tabelle einfügen
        for row in csv_reader:
            print(f"Row data: {row}")  # Debugging line
            if len(row) != 6:
                raise ValueError(f"Row does not contain exactly 6 values: {row}")

            # Convert the points to an integer
            row[5] = int(row[5])  # Ensure points are stored as integer
            
            cursor.execute(f"""
                INSERT INTO {table_name} ({', '.join(column_names)})
                VALUES ({', '.join(['?' for _ in column_names])})
            """, row)

    # Änderungen speichern und Verbindung schließen
    conn.commit()
    conn.close()

# Beispielverwendung
import_from_csv('jeopardy.db', 'questions', 'quiz.csv')
