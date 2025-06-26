import sqlite3

def populate_sample_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ---------- Employees ----------
    employees = [
        ("EMP001", "Ravi Kumar", "Site Engineer", "Production"),
        ("EMP002", "Anjali Sharma", "Accountant", "Accounts"),
        ("EMP003", "Manoj Das", "Project Manager", "Project"),
        ("EMP004", "Kiran Reddy", "Design Head", "Sales / Design"),
    ]
    for emp in employees:
        c.execute("INSERT INTO employees (emp_id, name, role, department) VALUES (?, ?, ?, ?)", emp)

    # ---------- Raw Materials ----------
    materials = [
        ("Coils", "Aluminum Coil", 120, "Kg"),
        ("Coils", "GI Coil", 300, "Kg"),
        ("Bolts", "M10 Bolt", 500, "Nos"),
        ("Gaskets", "Rubber Gasket", 250, "Nos"),
    ]
    for item in materials:
        c.execute("INSERT INTO raw_materials (category, material_name, stock_qty, unit) VALUES (?, ?, ?, ?)", item)

    # ---------- Vendors ----------
    vendors = [
        ("VEND001", "ABC Fabricators", "Coimbatore", "9876543210", "0422-223344", "abc@fab.com", 
         "33ABCDE1234F1Z5", "ABCDE1234F", "TAN1234567A", 
         "Ravi Kumar", "1234567890", "Current", "HDFC Bank", "HDFC0001234", "123456")
    ]
    for vendor in vendors:
        c.execute('''INSERT INTO vendors (
            vendor_id, company_name, company_address, office_mobile,
            office_telephone, email, gstin, pan, tan,
            ben_name, ben_ac, ac_type, bank_name, ifsc, micr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', vendor)

    # ---------- Vendor Contacts ----------
    contacts = [
        ("VEND001", "Rajesh", "Sales", "Manager", "9999988888"),
        ("VEND001", "Sundar", "Tech", "Engineer", "9876543210")
    ]
    for contact in contacts:
        c.execute("INSERT INTO vendor_contacts (vendor_id, name, dept, desg, mob) VALUES (?, ?, ?, ?, ?)", contact)

    # ---------- Enquiries ----------
    enquiries = [
        ("TEI/Enquiry/001", "Tender", "Main Contractor", "L&T", "Metro Station Ducting", "In Progress", None),
        ("TEI/Enquiry/002", "Enquiry", "Sub Contractor", "Tata Projects", "Hospital HVAC Setup", "In Progress", None),
    ]
    for enquiry in enquiries:
        c.execute('''INSERT INTO enquiry_details (
            enquiry_id, enquiry_type, contractor_type, client_name, project_title, status, file_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?)''', enquiry)

    # ---------- Projects ----------
    projects = [
        ("TEI/Enquiry/001", "L&T", "Metro Station Ducting", "Approved"),
        ("TEI/Enquiry/002", "Tata Projects", "Hospital HVAC Setup", "Pending")
    ]
    for project in projects:
        c.execute("INSERT INTO project_details (project_id, client_name, project_title, status) VALUES (?, ?, ?, ?)", project)

    # ---------- Invoices ----------
    invoices = [
        ("INV001", "2025-06-01", "L&T", 125000.00),
        ("INV002", "2025-06-10", "Tata Projects", 98000.00),
    ]
    for inv in invoices:
        c.execute("INSERT INTO dc_invoice (invoice_no, date, client_name, amount) VALUES (?, ?, ?, ?)", inv)

    conn.commit()
    conn.close()
    print("✅ All sample data inserted successfully.")

if __name__ == '__main__':
    populate_sample_data()
