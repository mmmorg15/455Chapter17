import argparse
import os
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

import psycopg

EXPECTED_COUNTS = {
    "customers": 250,
    "orders": 5000,
    "order_items": 15022,
    "products": 100,
    "shipments": 5000,
    "product_reviews": 3000,
}

TABLES = [
    "customers",
    "products",
    "orders",
    "shipments",
    "order_items",
    "product_reviews",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import SQLite shop.db into Supabase/Postgres.")
    parser.add_argument(
        "--sqlite-path",
        default=os.path.join("shop.db", "shop.db"),
        help="Path to the source SQLite file.",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("SUPABASE_DB_URL"),
        help="Supabase/Postgres connection string. Can also come from SUPABASE_DB_URL.",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate existing destination data before import.",
    )
    return parser.parse_args()


def load_rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    cursor = connection.execute(f"select * from {table}")
    return cursor.fetchall()


def normalize_row(table: str, row: tuple) -> tuple:
    if table == "customers":
        return (
            row[0], row[1], row[2], row[3], date.fromisoformat(row[4]), parse_timestamp(row[5]),
            row[6], row[7], row[8], row[9], row[10], bool(row[11]),
        )
    if table == "products":
        return (row[0], row[1], row[2], row[3], Decimal(str(row[4])), Decimal(str(row[5])), bool(row[6]))
    if table == "orders":
        return (
            row[0], row[1], parse_timestamp(row[2]), row[3], row[4], row[5], row[6], row[7], row[8], bool(row[9]),
            row[10], Decimal(str(row[11])), Decimal(str(row[12])), Decimal(str(row[13])), Decimal(str(row[14])),
            Decimal(str(row[15])), bool(row[16]),
        )
    if table == "shipments":
        return (
            row[0], row[1], parse_timestamp(row[2]), row[3], row[4], row[5], row[6], row[7], bool(row[8]),
        )
    if table == "order_items":
        return (row[0], row[1], row[2], row[3], Decimal(str(row[4])), Decimal(str(row[5])))
    if table == "product_reviews":
        return (row[0], row[1], row[2], row[3], parse_timestamp(row[4]), row[5])
    raise ValueError(f"Unsupported table {table}")


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def import_table(pg_connection: psycopg.Connection, table: str, rows: list[tuple]) -> None:
    normalized_rows = [normalize_row(table, row) for row in rows]
    placeholders = {
        "customers": "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        "products": "(%s, %s, %s, %s, %s, %s, %s)",
        "orders": "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        "shipments": "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        "order_items": "(%s, %s, %s, %s, %s, %s)",
        "product_reviews": "(%s, %s, %s, %s, %s, %s)",
    }
    columns = {
        "customers": "customer_id, full_name, email, gender, birthdate, created_at, city, state, zip_code, customer_segment, loyalty_tier, is_active",
        "products": "product_id, sku, product_name, category, price, cost, is_active",
        "orders": "order_id, customer_id, order_datetime, billing_zip, shipping_zip, shipping_state, payment_method, device_type, ip_country, promo_used, promo_code, order_subtotal, shipping_fee, tax_amount, order_total, risk_score, is_fraud",
        "shipments": "shipment_id, order_id, ship_datetime, carrier, shipping_method, distance_band, promised_days, actual_days, late_delivery",
        "order_items": "order_item_id, order_id, product_id, quantity, unit_price, line_total",
        "product_reviews": "review_id, customer_id, product_id, rating, review_datetime, review_text",
    }

    insert_sql = f"insert into {table} ({columns[table]}) values {placeholders[table]}"
    with pg_connection.cursor() as cursor:
        cursor.executemany(insert_sql, normalized_rows)


def reset_sequences(pg_connection: psycopg.Connection) -> None:
    statements = [
        "select setval(pg_get_serial_sequence('customers', 'customer_id'), coalesce(max(customer_id), 1), true) from customers;",
        "select setval(pg_get_serial_sequence('products', 'product_id'), coalesce(max(product_id), 1), true) from products;",
        "select setval(pg_get_serial_sequence('orders', 'order_id'), coalesce(max(order_id), 1), true) from orders;",
        "select setval(pg_get_serial_sequence('shipments', 'shipment_id'), coalesce(max(shipment_id), 1), true) from shipments;",
        "select setval(pg_get_serial_sequence('order_items', 'order_item_id'), coalesce(max(order_item_id), 1), true) from order_items;",
        "select setval(pg_get_serial_sequence('product_reviews', 'review_id'), coalesce(max(review_id), 1), true) from product_reviews;",
    ]
    with pg_connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def verify_counts(sqlite_connection: sqlite3.Connection, pg_connection: psycopg.Connection) -> None:
    print("Verifying row counts...")
    for table, expected in EXPECTED_COUNTS.items():
        sqlite_count = sqlite_connection.execute(f"select count(*) from {table}").fetchone()[0]
        with pg_connection.cursor() as cursor:
            cursor.execute(f"select count(*) from {table}")
            postgres_count = cursor.fetchone()[0]
        if sqlite_count != expected:
            raise RuntimeError(f"SQLite count mismatch for {table}: expected {expected}, found {sqlite_count}")
        if postgres_count != expected:
            raise RuntimeError(f"Postgres count mismatch for {table}: expected {expected}, found {postgres_count}")
        print(f"  {table}: {postgres_count}")


def main() -> None:
    args = parse_args()
    if not args.postgres_url:
        raise RuntimeError("Provide --postgres-url or set SUPABASE_DB_URL.")

    sqlite_connection = sqlite3.connect(args.sqlite_path)
    postgres_connection = psycopg.connect(args.postgres_url)

    try:
        if args.truncate:
            with postgres_connection.cursor() as cursor:
                cursor.execute(
                    "truncate table delivery_scores, product_reviews, order_items, shipments, orders, products, customers restart identity cascade;"
                )

        for table in TABLES:
            rows = load_rows(sqlite_connection, table)
            print(f"Importing {table} ({len(rows)} rows)...")
            import_table(postgres_connection, table, rows)

        reset_sequences(postgres_connection)
        postgres_connection.commit()
        verify_counts(sqlite_connection, postgres_connection)
        print("Import complete.")
    finally:
        postgres_connection.close()
        sqlite_connection.close()


if __name__ == "__main__":
    main()
