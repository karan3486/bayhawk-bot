import sqlite3

# Connect to the database
def get_connection():
    return sqlite3.connect('chatbot_conversations.db')

# Create the conversation table
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        type TEXT CHECK(type IN ('Bot', 'User')) NOT NULL,
        content TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Insert data into the table
def insert_conversation(name, email, message_type, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO conversation (name, email, type, content)
    VALUES (?, ?, ?, ?)
    ''', (name, email, message_type, content))
    conn.commit()
    conn.close()

# Retrieve all conversations
import sqlite3

def get_all_conversations():
    # Connect to the database
    conn = sqlite3.connect('chatbot_conversations.db')
    cursor = conn.cursor()
    
    # Fetch all rows from the conversation table
    cursor.execute('SELECT * FROM conversation')
    rows = cursor.fetchall()
    conn.close()

    # Dictionary to group conversations by email
    grouped_conversations = {}

    for row in rows:
        user_id = row[0]
        name = row[1]
        email = row[2]
        msg_type = row[3]  # 'User' or 'Bot'
        content = row[4]

        # Initialize the user's conversation structure if not already done
        if email not in grouped_conversations:
            grouped_conversations[email] = {
                "name": name,
                "email": email,
                "conversation": []
            }

        # Append to the conversation, grouped into User and Bot pairs
        if msg_type == "User":
            # Start a new pair
            grouped_conversations[email]["conversation"].append({"User": content, "Bot": None})
        elif msg_type == "Bot":
            # Update the last pair with the Bot's response
            if grouped_conversations[email]["conversation"]:
                grouped_conversations[email]["conversation"][-1]["Bot"] = content
            else:
                # In case there's a Bot message without a prior User message
                grouped_conversations[email]["conversation"].append({"User": None, "Bot": content})

    # Convert the grouped dictionary into a list of dictionaries
    return list(grouped_conversations.values())
def delete_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    Delete from conversation;
    ''')
    conn.commit()
    conn.close()

delete_table()