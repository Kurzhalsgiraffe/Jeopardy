import sqlite3
import csv

def export_to_csv(db_path, table_name, csv_path):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Alle Daten aus der Tabelle abrufen
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # Spaltennamen abrufen
    column_names = [description[0] for description in cursor.description]

    # CSV-Datei schreiben
    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=";")

        # Spaltennamen in die CSV schreiben
        csv_writer.writerow(column_names)

        # Datenzeilen in die CSV schreiben
        csv_writer.writerows(rows)

    # Verbindung schließen
    conn.close()

# Beispielverwendung
export_to_csv('quiz.db', 'quiz', 'output.csv')
