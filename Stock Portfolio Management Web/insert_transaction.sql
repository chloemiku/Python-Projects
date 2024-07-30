CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    transaction_date_time DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    amount INTEGER NOT NULL,
    price NUMERIC NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
