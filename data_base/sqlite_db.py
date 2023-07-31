import json
import sqlite3 as sq


def sql_start():
    global base, cur
    base = sq.connect('./data_base/database.db')
    cur = base.cursor()
    if not base:
        print("Database hasn't been connected")

    try:
        base.execute('BEGIN TRANSACTION;')

        sql_queries = (
            '''
            CREATE TABLE IF NOT EXISTS payments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL
                                     REFERENCES users (id),
                date         TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sum          REAL,
                payed_tokens INTEGER NOT NULL,
                invited_user INTEGER
            )
            STRICT;
            ''',
            '''
            CREATE TABLE IF NOT EXISTS usage_tokens (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id           INTEGER REFERENCES users (id),
                date              TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completion_tokens INTEGER,
                prompt_tokens     INTEGER,
                total_tokens      INTEGER NOT NULL
            )
            STRICT;
            ''',
            '''
            CREATE TABLE IF NOT EXISTS users (
                id      INTEGER PRIMARY KEY,
                context TEXT,
                name    TEXT,
                balance INTEGER
            )
            STRICT;
            ''',
            '''
            CREATE INDEX IF NOT EXISTS payments_user_id_IDX ON payments (
                user_id
            );
            ''',
            '''
            CREATE INDEX IF NOT EXISTS usage_tokens_user_id_IDX ON usage_tokens (
                user_id
            );
            ''')

        for query in sql_queries:
            base.execute(query)

        base.execute('COMMIT TRANSACTION;')

        # approve transaction
        base.commit()

    except sq.Error as e:
        print('Error creating table users: ', e)
        base.rollback()


def sql_stop():
    try:
        base.close()
    except sq.Error as e:
        print('Error closing database', e)


async def sql_add_command(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO users VALUES (?, ?, ?)', tuple(data.values()))
        base.commit()


def get_messages(user_id):
    query_result = cur.execute('SELECT context FROM users WHERE id = ?', user_id)
    row = query_result.fetchone()
    if row is not None:
        answer = row[0]
        return json.loads(answer)  # convert a JSON string back to a dictionary list
    else:
        return []


def reset_context(user_id):
    try:
        cur.execute("UPDATE users SET context=? WHERE id=?", (json.dumps([], ensure_ascii=False), user_id))
        base.commit()
    except sq.Error as e:
        print("Error reset_context: ", e)
        print("user_id: ", user_id)


def get_balance(user_id):
    query_result = cur.execute('SELECT balance FROM users WHERE id = ?', user_id)
    row = query_result.fetchone()
    if row is not None:
        answer = row[0]
        return answer
    else:
        return None


def spending_tokens(user_id, context, name, balance, completion_tokens, prompt_tokens, total_tokens):
    # Lists and tuples can be written via JSON. ASCII must be turned off because
    # otherwise Cyrillic alphabet turns into Unicode in the database

    new_balance = balance - total_tokens
    if new_balance < 0:
        new_balance = 0

    try:
        cur.execute('BEGIN TRANSACTION;')

        cur.execute(
            'INSERT OR REPLACE INTO users (id, context, name, balance) VALUES (?, ?, ?, ?)',
            (user_id, json.dumps(context, ensure_ascii=False), name, new_balance)
        )

        cur.execute(
            'INSERT INTO usage_tokens (user_id, completion_tokens, prompt_tokens, total_tokens) VALUES (?, ?, ?, ?)',
            (user_id, completion_tokens, prompt_tokens, total_tokens)
        )

        cur.execute('COMMIT TRANSACTION;')
        base.commit()

    except sq.Error as e:
        print("Error spending_tokens: ", e)
        print("user_id: ", user_id)
        print("context: ", context)


def give_balance(user_id, name, balance):
    try:
        cur.execute('INSERT OR IGNORE INTO users (id, name, balance, context) VALUES (?, ?, ?, ?)',
                    (user_id, name, balance, (json.dumps([], ensure_ascii=False)))
                    )
        base.commit()

    except sq.Error as e:
        print("Error give_balance: ", e, "user_id: ", user_id)
