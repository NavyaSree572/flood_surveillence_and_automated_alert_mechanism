import sqlite3

def refresh_db():
    conn = sqlite3.connect('flood_guardian.db')
    c = conn.cursor()
    
    # 1. Recreate Alerts Table with Status and GPS Columns
    print("Refreshing Alerts table...")
    c.execute("DROP TABLE IF EXISTS alerts")
    c.execute('''CREATE TABLE alerts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  person_id INTEGER, 
                  location TEXT, 
                  lat REAL, 
                  lon REAL, 
                  status TEXT DEFAULT 'Pending',
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # 2. Create Rescue Team Table for the Dashboard Section
    print("Initializing Rescue Team table...")
    c.execute("DROP TABLE IF EXISTS rescue_team")
    c.execute('''CREATE TABLE rescue_team 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  status TEXT, 
                  assignment TEXT)''')

    # 3. Insert Sample Rescue Team Data (as per your structure)
    team_members = [
        ("Commander Ketha", "Available", "Standby"),
        ("Officer Rahim", "Busy", "Alert #102"),
        ("Unit 4 (Drone)", "Available", "Standby"),
        ("Volunteer Group A", "Busy", "Zone 4 Evacuation")
    ]
    c.executemany("INSERT INTO rescue_team (name, status, assignment) VALUES (?, ?, ?)", team_members)

    conn.commit()
    conn.close()
    print("✅ Database Refreshed: Alerts and Rescue Team tables are ready!")

if __name__ == "__main__":
    refresh_db()