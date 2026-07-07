from sqlalchemy import text

EXPECTED = {
    "bronze_customers", "bronze_products", "bronze_orders", "bronze_order_items",
    "bronze_web_sessions", "bronze_web_events", "bronze_marketing_spend",
    "bronze_ab_test_assignments", "bronze_reviews_nps",
}


def test_all_bronze_tables_exist():
    from config.db import get_engine
    with get_engine().connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name LIKE 'bronze_%'"
        )).fetchall()
    assert EXPECTED <= {r[0] for r in rows}
