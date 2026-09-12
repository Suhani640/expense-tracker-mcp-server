from fastmcp import FastMCP
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def load_categories():
    with open(CATEGORIES_PATH, "r") as file:
        return json.load(file)
    
def init_db():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            note TEXT
        )
    """)

    conn.commit()
    conn.close()
init_db()


@mcp.tool()
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> dict:
    """Add a new expense entry to the database."""

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO expenses
            (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, amount, category, subcategory, note)
        )

        return {
            "status": "ok",
            "id": cursor.lastrowid
        }


@mcp.tool()
def list_expenses(
    start_date: str,
    end_date: str
) -> list:
    """List expense entries within an inclusive date range."""

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

@mcp.tool()
def summarize(
    start_date: str,
    end_date: str,
    category: str | None = None
) -> list:
    """Summarize expenses by category within an inclusive date range."""

    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """

        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cursor = conn.execute(query, params)

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Return the expense categories."""
    
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as file:
        return file.read()


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)