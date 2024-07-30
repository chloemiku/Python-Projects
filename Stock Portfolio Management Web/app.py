import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
# clear when the user closes browser. PERM session = lasts beyond current browser session. use persistant storage mechanism
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # specifies storage type
Session(app)  # initialize Flask-Session extension with 'app' object

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    # Fetch user's cash balance
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    cash_balance = user_cash[0]["cash"]

    # Fetch user's transactions
    user_transactions = db.execute("""
        SELECT symbol, SUM(amount) as total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING total_shares > 0
    """, user_id)

    # Initialize total value
    total_stock_value = 0

    # List: store portfolio details
    portfolio = []

    # Get current stock prices and calculate total value
    for transaction in user_transactions:
        symbol = transaction["symbol"]
        total_shares = transaction["total_shares"]
        current_price = lookup(symbol)["price"]
        current_stock_value = total_shares * current_price

        # Append stock details to portfolio list
        portfolio.append({
            "symbol": symbol,
            "shares": total_shares,
            "current_price": usd(current_price),
            "total_value": usd(current_stock_value)
        })

        total_stock_value += current_stock_value

    # Get total cash + stock value
    total_value = cash_balance + total_stock_value

    return render_template("index.html", cash=usd(cash_balance), cash_balance=usd(cash_balance), portfolio=portfolio,
                           total_stock_value=usd(total_stock_value), total_value=usd(total_value))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        stock_info = lookup(request.form.get("symbol"))
        shares_str = request.form.get("shares")

        # Validate the input
        if not stock_info:
            return apology("Invalid symbol", 400)

        # Check if shares is a float or not a valid integer
        try:
            shares_float = float(shares_str)
            shares = int(shares_str)
            if shares != shares_float or shares <= 0:
                return apology("Invalid number input", 400)
        except ValueError:
            return apology("Invalid number input", 400)

        if stock_info and shares:
            available_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            purchase_amount = float(shares) * stock_info["price"]
            if available_cash[0]["cash"] < float(purchase_amount):
                return apology("not enough cash", 400)
            else:
                db.execute("UPDATE users SET cash = ? WHERE id = ?",
                           available_cash[0]["cash"] - float(purchase_amount), session["user_id"])
                db.execute("INSERT INTO transactions (user_id, transaction_date_time, symbol, amount, price) VALUES(?, ?, ?, ?, ?)",
                           session["user_id"], datetime.now(), stock_info["symbol"], shares, stock_info["price"])

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY transaction_date_time DESC", session["user_id"])

    for transaction in transactions:
        if transaction["amount"] > 0:
            transaction["type"] = "Buy"
        else:
            transaction["type"] = "Sell"
            transaction["amount"] = abs(transaction["amount"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Check the existance of user and password. Any 1 condition holds true, then logged in; else considered invalid
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in - keep track of current user
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # POST: call lookup function, display result
    if request.method == "POST":
        stock_info = lookup(request.form.get("symbol"))
        if stock_info:
            stock_info = lookup(request.form.get("symbol"))

            return render_template("quoted.html", stock_info=stock_info)

        else:
            return apology("Invalid stock quote", 400)
    else:

        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Check for possible errors
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password", 400)

        elif (request.form.get("password") != request.form.get("confirmation")):
            return apology("not same password", 400)

        elif len(rows) != 0:
            return apology("username has been taken", 400)

        # if no error, insert new user into users table
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"),
                   generate_password_hash(request.form.get("password")))

        user_id = db.execute("SELECT id FROM users WHERE username = ?",
                             request.form.get("username"))
        session["user_id"] = user_id[0]["id"]

        # login user
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares_str = request.form.get("shares")

        # Validate input
        try:
            shares_float = float(shares_str)
            shares = int(shares_str)
            if shares != shares_float or shares <= 0:
                return apology("Invalid number input", 400)
        except ValueError:
            return apology("Invalid number input", 400)

        stock_info = lookup(symbol)
        if not stock_info:
            return apology("Invalid symbol", 400)

        # Check if user owns the stock and has enough shares to sell
        user_shares = db.execute(
            "SELECT SUM(amount) AS total_shares FROM transactions WHERE user_id = ? AND symbol = ?", user_id, symbol)
        total_shares = user_shares[0]["total_shares"]

        if total_shares is None or total_shares < shares:
            return apology("Not enough shares", 400)

        # Calculate the sale amount and update the user's cash
        sale_amount = shares * stock_info["price"]
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", sale_amount, user_id)

        # Insert the sale transaction
        db.execute("INSERT INTO transactions (user_id, transaction_date_time, symbol, amount, price) VALUES (?, ?, ?, ?, ?)",
                   user_id, datetime.now(), symbol, -shares, stock_info["price"])

        return redirect("/")

    else:
        # Fetch user's stocks
        user_stocks = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(amount) > 0", user_id)
        return render_template("sell.html", stocks=user_stocks)


@app.route("/buy_sell", methods=["POST"])
@login_required
def buy_sell():
    """Buy or sell shares of stock"""
    user_id = session["user_id"]
    stock_info = lookup(request.form.get("symbol"))
    shares = int(request.form.get("shares"))
    action = request.form.get("action")

    if not stock_info or shares <= 0:
        return apology("Invalid input", 400)

    current_price = stock_info["price"]
    transaction_cost = shares * current_price

    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    user_shares = db.execute("""
        SELECT SUM(amount) as total_shares
        FROM transactions
        WHERE user_id = ? AND symbol = ?
        GROUP BY symbol
    """, user_id, stock_info["symbol"])

    if action == "buy":
        if transaction_cost > user_cash:
            return apology("Not enough cash", 400)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", user_cash - transaction_cost, user_id)
        db.execute("""
            INSERT INTO transactions (user_id, transaction_date_time, symbol, amount, price)
            VALUES (?, ?, ?, ?, ?)
        """, user_id, datetime.now(), stock_info["symbol"], shares, current_price)

    elif action == "sell":
        if user_shares and user_shares[0]["total_shares"] >= shares:
            db.execute("UPDATE users SET cash = ? WHERE id = ?",
                       user_cash + transaction_cost, user_id)
            db.execute("""
                INSERT INTO transactions (user_id, transaction_date_time, symbol, amount, price)
                VALUES (?, ?, ?, ?, ?)
            """, user_id, datetime.now(), stock_info["symbol"], -shares, current_price)
        else:
            return apology("Not enough shares", 400)

    return redirect("/")
