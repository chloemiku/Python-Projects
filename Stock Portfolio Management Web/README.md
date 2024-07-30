# Stock Portfolio Management Web App

This project is a Flask-based web application for managing a stock portfolio. It allows users to register, log in, buy and sell stocks, and view their portfolio and transaction history.

- **Description:**

	- **Flask Configuration:**
      - The application is configured to use Flask and Flask-Session for session management.
      - SQLite is used as the database to store user and transaction data.
    - **Routes and Functionality:**
      - index(): Displays the user’s portfolio, including the current cash balance and the total value of stocks owned.
      - buy(): Allows users to buy shares of stock by validating input and updating the database with the transaction.
      - history(): Shows the user’s transaction history, listing all buy and sell operations.
      - login(): Handles user login, checking credentials and maintaining user sessions.
      - logout(): Logs the user out by clearing the session.
      - quote(): Retrieves and displays stock quotes using a lookup function.
      - register(): Handles user registration, validating inputs and storing hashed passwords in the database.
      - sell(): Allows users to sell shares of stock, updating the database with the transaction.
      - buy_sell(): Combined route for buying and selling stocks, validating input, and updating the user’s portfolio and cash balance.
    - **Helpers and Utilities:**
      - Custom filters and helper functions are used to format currency and manage application-specific tasks.
      - The apology() function renders error messages for user feedback.

Overall, this project provides a comprehensive solution for managing stock portfolios, with features for user authentication, transaction handling, and portfolio display.