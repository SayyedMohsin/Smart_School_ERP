import sqlite3
import os

# Database Reset
if os.path.exists('school_data.db'):
    os.remove('school_data.db')

conn = sqlite3.connect('school_data.db')
cursor = conn.cursor()

# Admin Login (User: admin, Pass: admin123)
cursor.execute('''CREATE TABLE Admin (username TEXT, password TEXT)''')
cursor.execute("INSERT INTO Admin VALUES ('admin', 'admin123')")

# Students
cursor.execute('''CREATE TABLE Students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, class_name TEXT, dob TEXT, mobile TEXT, address TEXT, photo TEXT,
    school_fee REAL DEFAULT 0, bus_fee REAL DEFAULT 0, old_balance REAL DEFAULT 0, total_due REAL DEFAULT 0,
    status TEXT DEFAULT 'Active')''')

# Staff
cursor.execute('''CREATE TABLE Teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, post TEXT, dob TEXT, mobile TEXT, address TEXT, email TEXT, photo TEXT,
    status TEXT DEFAULT 'Active')''')

# Transactions (Ab 'fee_type' bhi save hoga - School ya Bus)
cursor.execute('''CREATE TABLE Transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    student_id INTEGER, 
    amount REAL, 
    fee_type TEXT, 
    mode TEXT, 
    date TEXT, 
    receipt_no TEXT)''')

# Archive
cursor.execute('''CREATE TABLE Archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, original_id INTEGER, name TEXT, class_name TEXT, mobile TEXT, info TEXT, deleted_by TEXT, date TEXT)''')

conn.commit()
conn.close()
print("Database Updated with Bus Fee Support & Login!")