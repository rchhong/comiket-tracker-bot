import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Create a table named 'user'
cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    discord_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    last_updated TIMESTAMP NOT NULL
)
''')

# Create a table named 'doujin'
cursor.execute('''
CREATE TABLE IF NOT EXISTS doujin (
    _id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    price_in_yen INTEGER NOT NULL,
    price_in_usd REAL NOT NULL,
    is_r18 BOOLEAN NOT NULL,
    image_preview_url TEXT NOT NULL,
    url TEXT NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    circle_name TEXT,
    author_names TEXT,
    genres TEXT,
    events TEXT
)
''')

# Create a table named 'reservation'
cursor.execute('''
CREATE TABLE IF NOT EXISTS reservation (
    _id INTEGER PRIMARY KEY,
    user_discord_id INTEGER NOT NULL,
    doujin_id INTEGER NOT NULL,
    datetime_added TIMESTAMP NOT NULL,
    FOREIGN KEY (user_discord_id) REFERENCES user (discord_id),
    FOREIGN KEY (doujin_id) REFERENCES doujin (_id)
)
''')

# Commit changes and close the connection
conn.commit()
conn.close()

print("Seeding completed.")
