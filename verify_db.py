"""
Database verification script
"""
import sqlite3
import os

DB_FILE = 'bbms_local.db'

if not os.path.exists(DB_FILE):
    print(f"Error: Database file '{DB_FILE}' not found!")
    exit(1)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=" * 60)
print("SCHBC BBMS Database Verification")
print("=" * 60)

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"\nTables created: {len(tables)}")
for table in tables:
    print(f"  - {table}")

# Count records in each table
print("\nRecord counts:")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count} records")

# Display BloodMaster records
print("\n--- BloodMaster Records ---")
cursor.execute("SELECT id, component, preparation, remark FROM blood_master")
for row in cursor.fetchall():
    print(f"  ID={row[0]}: {row[1]} - {row[2]} ({row[3]})")

# Display SystemSettings
print("\n--- SystemSettings ---")
cursor.execute("SELECT key, value, description FROM system_settings")
for row in cursor.fetchall():
    print(f"  {row[0]} = {row[1]}")
    print(f"    → {row[2]}")

# Display sample inventory
print("\n--- Sample Inventory (first 10 records) ---")
cursor.execute("""
    SELECT i.id, i.blood_type, b.preparation, i.current_qty 
    FROM inventory i 
    JOIN blood_master b ON i.prep_id = b.id 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  ID={row[0]}: {row[1]}형 {row[2]} - 재고: {row[3]}단위")

conn.close()

print("\n" + "=" * 60)
print("✓ Database verification completed successfully!")
print("=" * 60)
