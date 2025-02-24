import sqlite3

def update_schema():
    conn = sqlite3.connect('instance/keylogger.db')
    c = conn.cursor()
    
    try:
        # Add new columns to device table if they don't exist
        c.execute("""
            ALTER TABLE device ADD COLUMN os_info TEXT;
        """)
    except:
        pass  # Column might already exist
        
    try:
        c.execute("""
            ALTER TABLE device ADD COLUMN hostname TEXT;
        """)
    except:
        pass
        
    try:
        c.execute("""
            ALTER TABLE device ADD COLUMN battery_level INTEGER;
        """)
    except:
        pass
        
    try:
        c.execute("""
            ALTER TABLE device ADD COLUMN ip_address TEXT;
        """)
    except:
        pass
    
    conn.commit()
    conn.close()
    print("Schema updated successfully")

if __name__ == "__main__":
    update_schema() 