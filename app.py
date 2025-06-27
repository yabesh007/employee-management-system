import calendar
from collections import defaultdict
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tkinter import Canvas
from flask import Flask, Response, render_template, send_file, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
import os

app = Flask(__name__, static_folder="static")
app.secret_key = 'your_secret_key'  # Change this to a secure key

# Configure Database (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Base directory where all HTML files are stored
BASE_DIR = r"D:/employee management system/"  # Change this to your actual file location

# Dummy user database (Replace with a real database later)
users = {
    "admin": "password",
    "yabesh": "1234"
}

# ---------------------- Database Model ----------------------
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    date_of_joining = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Present")



# Create the database tables
with app.app_context():
    db.create_all()

# ---------------------- Routes ----------------------

# Serve the Login Page
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return send_file(os.path.join(BASE_DIR,r"D:/emloyee managment system/index.html"))

# Handle Login Request
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in users and users[username] == password:
        session['user'] = username  # Store user in session
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('home') + "?error=1")

# Serve the Employee Entry Page
@app.route('/employee_entry.html')
def employee_entry():
    if 'user' in session:
        return send_file(os.path.join(BASE_DIR,r"D:/emloyee managment system/employee_entry.html"))
    return redirect(url_for('/dashboard'))

# Serve the Employees Page
@app.route('/employees.html')
def employees():
    if 'user' in session:
        return send_file(os.path.join(BASE_DIR,r"D:/emloyee managment system/employees.html"))
    return redirect(url_for('/dashboard'))

#serve the edit employee page
@app.route('/edit_employee.html')
def edit_employee_page():
    return send_file(r"D:/emloyee managment system/edit_employee.html")


# serve the analysis page
@app.route('/employee_analysis.html')
def employee_analysis():
    file_path = r"D:/emloyee managment system/employee_analysis.html"

    # ✅ Check if the file exists before serving
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Error: employee_analysis.html not found!", 404

@app.route('/reports.html')
def reports():
    if 'user' in session:
        file_path = os.path.join(BASE_DIR,r"D:/emloyee managment system/reports.html") 
        if os.path.exists(file_path):
            return send_file(file_path)
        return "Error: reports.html not found!", 404
    return redirect(url_for('home')) 



    # ---------------------- Add Employee Function ----------------------

# Function to generate a new unique Employee ID

def generate_employee_id():
    last_employee = Employee.query.order_by(Employee.id.desc()).first()
    if last_employee:
        last_id = int(last_employee.employee_id[3:])  # Extract number from 'EMPXXX'
        new_id = f"EMP{last_id + 1:03d}"  # Format: EMP001, EMP002, etc.
    else:
        new_id = "EMP001"  # First employee ID
    return new_id

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'user' in session:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        department = request.form['department']
        date_of_joining = request.form['dateOfJoining']
        salary = float(request.form['salary'])
        address = request.form['address']

        # Generate a new employee ID
        employee_id = generate_employee_id()

        # Check if email already exists
        if Employee.query.filter_by(email=email).first():
            return "Error: Employee with this email already exists!", 400

        # Create and store new employee
        new_employee = Employee(
            employee_id=employee_id,
            name=name,
            email=email,
            phone=phone,
            department=department,
            date_of_joining=date_of_joining,
            salary=salary,
            address=address
        )
        db.session.add(new_employee)
        db.session.commit()

        # ✅ Redirect to the dashboard after adding the employee
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('home'))


@app.route('/get_highest_salary_employee', methods=['GET'])
def get_highest_salary_employee():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # Fetch the employee with the highest salary
        highest_salary_employee = Employee.query.order_by(Employee.salary.desc()).first()

        if highest_salary_employee:
            print("Highest Salary Employee:", highest_salary_employee.name, highest_salary_employee.salary)  # ✅ Debugging
            return jsonify({
                "name": highest_salary_employee.name.strip(),  # ✅ Removes extra spaces
                "salary": f"Rs {highest_salary_employee.salary:,.2f}"  # ✅ Formats salary correctly
            })
        else:
            print("No employees found in database")  # ✅ Debugging
            return jsonify({"error": "No employees found"}), 404

    except Exception as e:
        print("Error fetching highest salary employee:", str(e))  # ✅ Debugging
        return jsonify({"error": "Server error"}), 500



@app.route('/get_recent_employees', methods=['GET'])
def get_recent_employees():
    """Returns only the 3 most recently added employees for the dashboard"""
    if 'user' in session:
        employees = Employee.query.order_by(Employee.id.desc()).limit(3).all()  # Fetch latest 3 employees
        total_employees = Employee.query.count()  # Get total employee count

        employee_list = [
            {
                "id": emp.id,
                "employeeId": emp.employee_id,
                "name": emp.name,
                "email": emp.email,
                "phone": emp.phone,
                "department": emp.department,
                "dateOfJoining": emp.date_of_joining,
                "salary": emp.salary,
                "address": emp.address,
                "status": emp.status
            } for emp in employees
        ]

        return jsonify({
            "employees": employee_list,
            "totalEmployees": total_employees
        })

    return jsonify({"error": "Unauthorized"}), 403



# API to Get Employees (JSON Response for Frontend)
@app.route('/get_employees', methods=['GET'])
def get_employees():
    if 'user' in session:
        # Fetch all employees from the database
        employees = Employee.query.all()

        total_employees = len(employees)  # Get total number of employees

        employee_list = [
            {
                "id": emp.id,
                "employeeId": emp.employee_id, 
                "name": emp.name, 
                "email": emp.email,
                "phone": emp.phone, 
                "department": emp.department,
                "dateOfJoining": emp.date_of_joining, 
                "salary": emp.salary,
                "address": emp.address,
                "status": emp.status
            } for emp in employees
        ]

        return jsonify({
            "employees": employee_list,
            "totalEmployees": total_employees
        })
    
    return jsonify({"error": "Unauthorized"}), 403


@app.route('/filter_employees', methods=['GET'])
def filter_employees():
    if 'user' in session:
        # Fetch filter parameters from frontend
        name_filter = request.args.get('name', '').strip()
        department_filter = request.args.get('department', '').strip()
        min_salary = request.args.get('min_salary', type=float, default=0)
        max_salary = request.args.get('max_salary', type=float, default=float('inf'))
        date_of_joining_filter = request.args.get('date_of_joining', '').strip()

        # Start with base query
        query = Employee.query

        if name_filter:
            query = query.filter(Employee.name.ilike(f"%{name_filter}%"))  # Case-insensitive search
        if department_filter:
            query = query.filter(Employee.department == department_filter)
        if date_of_joining_filter:
            query = query.filter(Employee.date_of_joining == date_of_joining_filter)
        if min_salary or max_salary:
            query = query.filter(Employee.salary.between(min_salary, max_salary))

        employees = query.all()
        total_employees = len(employees)  # Get filtered employee count

        employee_list = [
            {
                "id": emp.id,
                "employeeId": emp.employee_id, 
                "name": emp.name, 
                "email": emp.email,
                "phone": emp.phone, 
                "department": emp.department,
                "dateOfJoining": emp.date_of_joining, 
                "salary": emp.salary,
                "address": emp.address
            } for emp in employees
        ]

        return jsonify({
            "employees": employee_list,
            "totalEmployees": total_employees
        })

    return jsonify({"error": "Unauthorized"}), 403



# Add DELETE function right below the above routes
@app.route('/delete_employee/<int:id>', methods=['DELETE'])
def delete_employee(id):
    if 'user' in session:
        employee = Employee.query.get(id)
        if employee:
            db.session.delete(employee)
            db.session.commit()
            return jsonify({"message": "Employee deleted successfully"}), 200
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"error": "Unauthorized"}), 403

# API route to handle employee update
@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403  # Ensure user is logged in

    employee = Employee.query.get(id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    if request.method == 'POST':  # Handle form submission
        data = request.form
        employee.name = data.get('name', employee.name)
        employee.email = data.get('email', employee.email)
        employee.phone = data.get('phone', employee.phone)
        employee.department = data.get('department', employee.department)
        employee.date_of_joining = data.get('dateOfJoining', employee.date_of_joining)
        employee.salary = float(data.get('salary', employee.salary))
        employee.address = data.get('address', employee.address)

        db.session.commit()
        return jsonify({"message": "Employee updated successfully"}), 200

    # If GET request, render the edit page with employee data
    return render_template('edit_employee.html', employee=employee)


@app.route('/download_filtered_csv', methods=['GET'])
def download_filtered_csv():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    # Get filter parameters from request
    name_filter = request.args.get('name', '').strip()
    department_filter = request.args.get('department', '').strip()
    min_salary = request.args.get('min_salary', type=float, default=0)
    max_salary = request.args.get('max_salary', type=float, default=float('inf'))

    # Query database with filters
    query = Employee.query
    if name_filter:
        query = query.filter(Employee.name.ilike(f"%{name_filter}%"))
    if department_filter:
        query = query.filter(Employee.department == department_filter)
    if min_salary or max_salary:
        query = query.filter(Employee.salary.between(min_salary, max_salary))

    employees = query.all()

    # Prepare CSV data
    csv_data = [["Employee ID", "Name", "Email", "Phone", "Department", "Date of Joining", "Salary", "Address"]]
    for emp in employees:
        csv_data.append([emp.employee_id, emp.name, emp.email, emp.phone, emp.department, emp.date_of_joining, emp.salary, emp.address])

    # Create CSV response
    csv_output = "\n".join([",".join(map(str, row)) for row in csv_data])
    response = Response(csv_output, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=filtered_employees.csv"

    return response



@app.route('/download_filtered_pdf', methods=['GET'])
def download_filtered_pdf():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    # Ensure the directory exists
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    name_filter = request.args.get('name', '').strip()
    department_filter = request.args.get('department', '').strip()
    min_salary = request.args.get('min_salary', type=float, default=0)
    max_salary = request.args.get('max_salary', type=float, default=float('inf'))

    query = Employee.query
    if name_filter:
        query = query.filter(Employee.name.ilike(f"%{name_filter}%"))
    if department_filter:
        query = query.filter(Employee.department == department_filter)
    if min_salary or max_salary:
        query = query.filter(Employee.salary.between(min_salary, max_salary))

    employees = query.all()

    if not employees:
        return jsonify({"error": "No employees found matching the filter"}), 404

    pdf_filename = "filtered_employees.pdf"
    pdf_path = os.path.join(BASE_DIR, pdf_filename)

    # Create the PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)
    
    # Title
    c.drawString(200, height - 50, "Filtered Employee Report")

    # Column Titles
    y_position = height - 80
    c.drawString(50, y_position, "Emp ID")
    c.drawString(120, y_position, "Name")
    c.drawString(250, y_position, "Department")
    c.drawString(380, y_position, "Salary")

    y_position -= 20  # Move below for data

    # Write employee data
    for emp in employees:
        if y_position < 50:  # If page is full, create a new page
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 80  # Reset y position

        c.drawString(50, y_position, emp.employee_id)
        c.drawString(120, y_position, emp.name)
        c.drawString(250, y_position, emp.department)
        c.drawString(380, y_position, f"Rs {emp.salary:,.2f}")
        y_position -= 20  # Move down for next employee

    c.save()

    # Return the generated PDF
    return send_file(pdf_path, as_attachment=True)




@app.route('/get_employee_analysis', methods=['GET'])
def get_employee_analysis():
    if 'user' in session:
        employees = Employee.query.all()

        # Dictionary to store employees joined per month & year
        joins_per_month_year = defaultdict(lambda: defaultdict(int))

        # Dictionary to store salary distribution
        salary_distribution = {
            "Below 20K": 0,
            "20K-50K": 0,
            "50K-100K": 0,
            "100K-200K": 0,
            "Above 200K": 0
        }

        for emp in employees:
            try:
                # Parse the joining date
                join_date = datetime.strptime(emp.date_of_joining, "%Y-%m-%d")
                year = join_date.year
                month = join_date.month  # Use numeric month for sorting
                joins_per_month_year[year][month] += 1
            except:
                continue  # Skip invalid date formats

            try:
                # Categorize employees based on salary range
                salary = float(emp.salary)
                if salary < 20000:
                    salary_distribution["Below 20K"] += 1
                elif salary < 50000:
                    salary_distribution["20K-50K"] += 1
                elif salary < 100000:
                    salary_distribution["50K-100K"] += 1
                elif salary < 200000:
                    salary_distribution["100K-200K"] += 1
                else:
                    salary_distribution["Above 200K"] += 1
            except:
                continue  # Skip invalid salaries

        # ✅ Sort months correctly (January to December)
        sorted_joins_per_month_year = {
            year: {calendar.month_name[month]: count for month, count in sorted(month_data.items())}
            for year, month_data in joins_per_month_year.items()
        }

        return jsonify({
            "joinsPerMonthYear": sorted_joins_per_month_year,
            "salaryDistribution": salary_distribution
        })

    return jsonify({"error": "Unauthorized"}), 403

@app.route('/get_department_analysis', methods=['GET'])
def get_department_analysis():
    if 'user' in session:
        employees = Employee.query.all()
        
        department_counts = {}
        for emp in employees:
            if emp.department in department_counts:
                department_counts[emp.department] += 1
            else:
                department_counts[emp.department] = 1

        return jsonify(department_counts)

    return jsonify({"error": "Unauthorized"}), 403




# ---------------------- API to Fetch Employee Reports ----------------------
@app.route('/get_reports', methods=['GET'])
def get_reports():
    if 'user' in session:
        employees = Employee.query.all()
        employee_list = [
            {
                "employee_id": emp.employee_id,
                "name": emp.name,
                "email": emp.email,
                "phone": emp.phone,
                "department": emp.department,
                "date_of_joining": emp.date_of_joining,
                "salary": emp.salary,
                "address": emp.address
            } for emp in employees
        ]
        return jsonify(employee_list)
    return jsonify({"error": "Unauthorized"}), 403

# ---------------------- CSV Export Route ----------------------
@app.route('/download_csv')
def download_csv():
    if 'user' in session:
        employees = Employee.query.all()
        csv_data = [["Employee ID", "Name", "Email", "Phone", "Department", "Date of Joining", "Salary", "Address"]]
        for emp in employees:
            csv_data.append([emp.employee_id, emp.name, emp.email, emp.phone, emp.department, emp.date_of_joining, emp.salary, emp.address])

        csv_file_path = os.path.join(BASE_DIR, "employee_report.csv")
        with open(csv_file_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(csv_data)

        return send_file(csv_file_path, as_attachment=True)
    return jsonify({"error": "Unauthorized"}), 403

# ---------------------- PDF Export Route ----------------------
@app.route('/download_pdf')
def download_pdf():
    if 'user' in session:
        employees = Employee.query.all()
        pdf_content = "Employee Report\n\n"
        pdf_content += "Employee ID | Name | Email | Phone | Department | Date of Joining | Salary | Address\n"
        pdf_content += "-" * 90 + "\n"

        for emp in employees:
            pdf_content += f"{emp.employee_id} | {emp.name} | {emp.email} | {emp.phone} | {emp.department} | {emp.date_of_joining} | {emp.salary} | {emp.address}\n"

        response = Response(pdf_content, mimetype="text/plain")
        response.headers["Content-Disposition"] = "attachment; filename=employee_report.txt"
        return response
    return jsonify({"error": "Unauthorized"}), 403



# Serve the Dashboard (Requires Login)
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return send_file(os.path.join(BASE_DIR,r"D:/emloyee managment system/dashboard.html"))
    return redirect(url_for('home'))

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


# ---------------------- Run the App ----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)

