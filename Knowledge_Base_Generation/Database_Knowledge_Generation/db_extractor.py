import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.db import init_db

def extract_schema():
    conn = init_db()
    cur = conn.cursor()
    schema_info = {}

    try:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            table_info = {
                "columns": [],
                "primary_keys": [],
                "foreign_keys": []
            }

            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            columns = cur.fetchall()
            
            has_updated_at = any(col[0] == 'updated_at' for col in columns)

            for col_name, data_type in columns:
                col_info = {
                    "name": col_name,
                    "type": data_type,
                    "sample_values": []
                }
                
                try:
                    if has_updated_at:
                        cur.execute(f"SELECT {col_name} FROM {table} WHERE {col_name} IS NOT NULL AND {col_name}::text != '' GROUP BY {col_name} ORDER BY max(updated_at) DESC LIMIT 5")
                    else:
                        cur.execute(f"SELECT {col_name} FROM {table} WHERE {col_name} IS NOT NULL AND {col_name}::text != '' GROUP BY {col_name} LIMIT 5")
                    samples = [str(row[0]) for row in cur.fetchall()]
                    col_info["sample_values"] = samples
                except Exception as e:
                    print(f"Error fetching samples for {table}.{col_name}: {e}")
                    conn.rollback()

                table_info["columns"].append(col_info)

            try:
                cur.execute(f"""
                    SELECT a.attname
                    FROM   pg_index i
                    JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                         AND a.attnum = ANY(i.indkey)
                    WHERE  i.indrelid = '{table}'::regclass
                    AND    i.indisprimary;
                """)
                table_info["primary_keys"] = [row[0] for row in cur.fetchall()]
            except Exception as e:
                print(f"Error fetching PKs for {table}: {e}")
                conn.rollback()

            try:
                cur.execute(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table}';
                """)
                table_info["foreign_keys"] = [{"column": row[0], "foreign_table": row[1], "foreign_column": row[2]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error fetching FKs for {table}: {e}")
                conn.rollback()

            schema_info[table] = table_info

    finally:
        cur.close()
        conn.close()

    return schema_info
