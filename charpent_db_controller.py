import psycopg2
from psycopg2 import sql

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    database="chirpent",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)

def create_chirpent_user_table():
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE chirpent_user_table (
                user_id SERIAL PRIMARY KEY,
                user_name TEXT,
                email TEXT,
                password TEXT,
                phone TEXT,
                user_api TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def insert_chirpent_user(user_name, email, password, phone, user_api):
    with conn.cursor() as cursor:
        # Check if the email and password already exist in the database
        cursor.execute("SELECT * FROM chirpent_user_table WHERE email = %s AND user_name = %s", (email, user_name))
        existing_user = cursor.fetchone()

        if existing_user:
            # Email and password combination already exists, return "Not OK"
            return "Not OK"

        # Email and password combination does not exist, insert the new user
        cursor.execute("""
            INSERT INTO chirpent_user_table (userSname, email, password, phone, user_api)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_name, email, password, phone, user_api))

        conn.commit()
        return "OK"


if __name__ == "__main__":
    create_chirpent_user_table()