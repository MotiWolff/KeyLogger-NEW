import sqlite3

def drop_all_tables():
    conn = sqlite3.connect('instance/keylogger.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Drop each table
    for table in tables:
        if table[0] != 'sqlite_sequence':  # Don't drop sqlite_sequence
            print(f"Dropping table: {table[0]}")
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
    
    conn.commit()
    conn.close()
    print("All tables dropped successfully")

if __name__ == "__main__":
    drop_all_tables() 