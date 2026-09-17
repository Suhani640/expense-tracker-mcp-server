from fastmcp import FastMCP
import os
import json
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)

mcp = FastMCP("ExpenseTracker")


def load_categories():
    with open(CATEGORIES_PATH, "r") as file:
        return json.load(file)
    



@mcp.tool()
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> dict:
    """Add a new expense entry to the database."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO expenses
                (date, amount, category, subcategory, note)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (date, amount, category, subcategory, note)
            )

            expense_id = cursor.fetchone()[0]

        conn.commit()

    return {
        "status": "ok",
        "id": expense_id
    }


@mcp.tool()
def list_expenses(
    start_date: str,
    end_date: str
) -> list:
    """List expense entries within an inclusive date range."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN %s AND %s
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )

            rows = cursor.fetchall()

            columns = [column.name for column in cursor.description]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

@mcp.tool()
def summarize(
    start_date: str,
    end_date: str,
    category: str | None = None
) -> list:
    """Summarize expenses by category within an inclusive date range."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:

            query = """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN %s AND %s
            """

            params = [start_date, end_date]

            if category:
                query += " AND category = %s"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            cursor.execute(query, params)

            rows = cursor.fetchall()

            columns = [column.name for column in cursor.description]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Return the expense categories."""
    
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as file:
        return file.read()


if __name__ == "__main__":
   mcp.run(
    transport="http",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000))
)