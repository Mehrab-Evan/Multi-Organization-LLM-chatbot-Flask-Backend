import psycopg2
from psycopg2 import sql

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    database="SolvrzChat",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)



def create_table2():
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE web_user_messages (
                session_id TEXT PRIMARY KEY,
                msg_history BYTEA,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Function to insert an entry
def insert_user_message(session_id, msg_history):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO web_user_messages (session_id, msg_history)
            VALUES (%s, %s)
        """, (session_id, msg_history))
        conn.commit()


# Function to update the msg_history
def update_msg_history(session_id, new_msg_history):
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE web_user_messages
            SET msg_history = %s
            WHERE session_id = %s
        """, (new_msg_history, session_id))
        conn.commit()

# Function to get all columns of a specific user_id
def get_user_data(session_id):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT session_id, msg_history
            FROM web_user_messages
            WHERE session_id = %s
        """, (session_id,))
        user_data = cursor.fetchone()
        if user_data:
            session_id, msg_history = user_data
            return {
                "user_id": session_id,
                "msg_history": msg_history
            }
        else:
            return None

# Function to delete a row for a specific user_id
def delete_user_data(session_id):
    with conn.cursor() as cursor:
        cursor.execute("""
            DELETE FROM web_user_messages
            WHERE session_id = %s
        """, (session_id,))
        conn.commit()

# Example usage
if __name__ == "__main__":
    create_table2()
    # insert_user_message("user1", b"message_history_data")
    # update_msg_history(1, b"new_message_history_data")

# Close the connection
# conn.close()
#
# user_id = 1
# user_data = get_user_data(user_id)
# if user_data:
#     print("User Data:")
#     print("User ID:", user_data["user_id"])
#     print("User Name:", user_data["user_name"])
#     print("Message History:", user_data["msg_history"])