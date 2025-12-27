import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

class SchoolERP:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart ERP - Edit & Receipt System")
        self.root.geometry("1100x700")
        
        # Sidebar & Layout
        self.sidebar = tk.Frame(self.root, bg="#2c3e50", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.content = tk.Frame(self.root, bg="white")
        self.content.pack(side="right", fill="both", expand=True)

        self.setup_menu()
        self.show_dashboard()

    def setup_menu(self):
        menu = [("Dashboard", self.show_dashboard), ("Students", self.view_students), 
                ("Fees & Receipt", self.fee_mgmt), ("Archives", self.view_archives)]
        for text, cmd in menu:
            tk.Button(self.sidebar, text=text, command=cmd, fg="white", bg="#34495e", pady=10).pack(fill="x")

    def clear_content(self):
        for widget in self.content.winfo_children(): widget.destroy()

    # --- EDIT POPUP WINDOW ---
    def open_edit_popup(self, s_id, old_name):
        popup = tk.Toplevel(self.root)
        popup.title("Edit Student")
        popup.geometry("300x200")
        
        tk.Label(popup, text=f"Edit Name for ID: {s_id}").pack(pady=10)
        new_name_ent = tk.Entry(popup)
        new_name_ent.insert(0, old_name)
        new_name_ent.pack()

        def update_data():
            conn = sqlite3.connect('school_data.db')
            curr = conn.cursor()
            curr.execute("UPDATE Students SET name=? WHERE student_id=?", (new_name_ent.get(), s_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Updated!")
            popup.destroy()
            self.view_students()

        tk.Button(popup, text="Save Changes", command=update_data, bg="green", fg="white").pack(pady=20)

    # --- STUDENT VIEW WITH EDIT/DELETE ---
    def view_students(self):
        self.clear_content()
        tree = ttk.Treeview(self.content, columns=("ID", "Name", "Roll", "Class"), show='headings')
        for col in ("ID", "Name", "Roll", "Class"): tree.heading(col, text=col)
        tree.pack(fill="both", expand=True)

        conn = sqlite3.connect('school_data.db')
        curr = conn.cursor()
        curr.execute("SELECT * FROM Students")
        for row in curr.fetchall(): tree.insert("", "end", values=row)
        conn.close()

        btn_frame = tk.Frame(self.content)
        btn_frame.pack(pady=10)

        def on_edit():
            selected = tree.selection()
            if selected:
                item = tree.item(selected)['values']
                self.open_edit_popup(item[0], item[1])

        tk.Button(btn_frame, text="Edit Selected", command=on_edit, bg="orange").pack(side="left", padx=5)

    # --- FEES & RECEIPT GENERATION ---
    def fee_mgmt(self):
        self.clear_content()
        tk.Label(self.content, text="Fee Entry & Receipt", font=("Arial", 18)).pack(pady=10)
        
        tk.Label(self.content, text="Student ID:").pack()
        sid_ent = tk.Entry(self.content); sid_ent.pack()
        tk.Label(self.content, text="Amount:").pack()
        amt_ent = tk.Entry(self.content); amt_ent.pack()

        def save_and_receipt():
            s_id = sid_ent.get()
            amt = amt_ent.get()
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 1. Save to DB
            conn = sqlite3.connect('school_data.db')
            curr = conn.cursor()
            curr.execute("INSERT INTO Fees (student_id, paid_fees, date_of_payment) VALUES (?,?,?)", (s_id, amt, date_str))
            conn.commit()
            conn.close()

            # 2. Generate Text Receipt (Bina kisi API ke)
            receipt_text = f"--- SCHOOL FEE RECEIPT ---\nDate: {date_str}\nStudent ID: {s_id}\nAmount: Rs.{amt}\nStatus: Paid\n--------------------------"
            filename = f"Receipt_SID_{s_id}_{datetime.now().strftime('%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(receipt_text)
            
            messagebox.showinfo("Success", f"Receipt Saved as {filename}")

        tk.Button(self.content, text="Pay & Print Receipt", command=save_and_receipt, bg="green", fg="white").pack(pady=20)

    def show_dashboard(self): self.clear_content(); tk.Label(self.content, text="Welcome to ERP", font=("Arial", 20)).pack(pady=50)
    def view_archives(self): self.clear_content(); tk.Label(self.content, text="Deleted Records (Archives)", font=("Arial", 20)).pack()

if __name__ == "__main__":
    root = tk.Tk()
    obj = SchoolERP(root)
    root.mainloop()