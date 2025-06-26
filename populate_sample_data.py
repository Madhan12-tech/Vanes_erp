import sqlite3

def populate_sample_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Sample Employees
    employees = [
        ("EMP001", "Ravi Kumar", "Site Engineer", "Production"),
        ("EMP002", "Anjali Sharma", "Accountant", "Accounts"),
        ("EMP003", "Manoj Das", "Project Manager", "Project"),
        ("EMP004", "Kiran Reddy", "Design Head", "Sales / Design"),
    ]

    for emp in employees:
        c.execute("INSERT INTO employees (emp_id, name, role, department) VALUES (?, ?, ?, ?)", emp)

    # Sample Raw Materials
    materials = [
        ("Coils", "Aluminum Coil", 120, "Kg"),
        ("Coils", "GI Coil", 300, "Kg"),
        ("Bolts", "M10 Bolt", 500, "Nos"),
        ("Gaskets", "Rubber Gasket", 250, "Nos"),
    ]

    for item in materials:
        c.execute("INSERT INTO raw_materials (category, material_name, stock_qty, unit) VALUES (?, ?, ?, ?)", item)

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully.")

if __name__ == '__main__':
    populate_sample_data()
