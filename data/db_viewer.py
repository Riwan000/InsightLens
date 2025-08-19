import sqlite3
conn = sqlite3.connect("data/insightlens.db")
for row in conn.execute("SELECT * FROM insights"):
    print(row)
conn.close()