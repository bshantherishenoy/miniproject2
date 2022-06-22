# ------------------------IMPORTS ------------------------#
import flask
from flask import Flask, render_template, request, redirect, send_from_directory,flash,session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import datetime
import pandas as pd
from csv import DictWriter
import uuid
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import csv
import ast
import glob
import os
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import LoginManager
import traceback
import sys
from modules.service_admin import Admin_Dashboard
from modules.service_branch import Branch_Service
from flask_session import Session
import numpy as np


# ---------------------Initializing Dataframe ------------#
output = pd.DataFrame()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['SESSION_TYPE'] = "filesystem"

Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', "sqlite:///hardwareshop45.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Session(app)

index = None
indexs = None

port = 5100


# ----------------------- models ------------------------#
class Branch(db.Model):
    branch_id = db.Column(db.Integer,primary_key=True)
    branch_name = db.Column(db.String(16),nullable=False)
    branch_location = db.Column(db.String(16),nullable=False)
    users = relationship('Users',backref='branch') 
    admin = relationship('Admin',backref='branch')
class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_username = db.Column(db.String(100), nullable=False,unique=True)
    user_password = db.Column(db.String(16), nullable=False)
    user_branch = db.Column(db.Integer, db.ForeignKey("branch.branch_id"))
class Admin(db.Model):
    admin_id = db.Column(db.Integer,primary_key = True)
    admin_name = db.Column(db.String(20),nullable=False)
    admin_password = db.Column(db.String(16),nullable=False)
    admin_branch = db.Column(db.Integer, db.ForeignKey("branch.branch_id"),primary_key=True)



db.create_all()

# -----------------------config---------------------------#

uuids = None



@app.context_processor
def inject_today_date():
    global uuids
    uuids = uuid.uuid4()
    return {'today_date': datetime.date.today(),
            'uuid':uuids}


def validate_upload(f):
    def wrapper():
        if 'completed' not in flask.session or not flask.session['completed']:
            return flask.redirect('/')
        return f()
    return wrapper


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever
# --------------------------------Data----------------------------#


def write_json(data, filename="json/default_products.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def write_jsons(data, filename="json/users.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def search(list, n):
    global index
    for i in range(len(list)):
        if list[i]["Product_Id"] == n:
            index = i
            return True
    return False


def search_for_employee(list, n):
    global indexs
    print(list)
    print("came inside function")
    for i in range(len(list)):
        if int(list[i]["employee_id"]) == n:
            indexs = i
            print(f"Index is {indexs}")
            return True
    return False


# ------------------------ROUTES INDEX---------------------------#
flag = False


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        data = request.form
        select = int(request.form.get('comp_select'))
        if select == 1:
            if Admin.query.filter_by(admin_id=data["id"]).first():
                db = Admin.query.filter_by(admin_id=data["id"]).first()
                print(data)
                
                if data["password"] == db.admin_password:
                    session["type"] = "Admin"
                    session["username"]  =  data["id"]
                    return redirect('/Admin_Pannel')
                else:
                    flash("Invalid Password","info")
            else:
                print("This was not there")
                flash("Invalid credentials","danger")
        if select == 2:
            if Branch.query.filter_by(branch_id=data["id"]).first():
                app = Branch.query.filter_by(branch_id=data["id"]).first()
                if app.branch_name == data["password"]:
                    session["type"] = "Branch"
                    session["username"]  =  data["id"]
                    return redirect("/branch")
                else:
                    flash("Invalid Password" ,"info")     
            else:
                flash("There is no such Branch","danger")
        if select == 3:
            if Users.query.filter_by(user_id=data["id"]).first():
                data = Users.query.filter_by(user_id=data["id"]).first()
                session["type"] = "Employee"
                session["username"]  =  data.user_id
                flash("Login Successful")
                return redirect("/Employee_login")
            
            else:
                flash("There is no such User","danger")
        return render_template("register.html")
    else:
        return render_template("register.html")
# --------------------------- Main Routes to Branch ----------------------#

@app.route('/branch',methods=['GET','POST'])
def main_branch():  
    id = session.get('username')
    branch_manager = Branch.query.filter_by(branch_id=id).first()
    branch = Branch_Service(branch_manager)
    # ----------Net price and revenue ------------- #
    net_price,total_price = branch.generate_revenue()
    # ----------Generate Monthly Sales ------------ #
    monthly = branch.generate_monthly_sales()
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sept","Oct","Nov","Dec"]
    d = list(monthly.keys())
    month = [months[d[i].month - 1] for i in range(len(d))]
    sales = list(monthly.values())
    # -------- Top 5 company    ----------------#
    types = branch.top_five_selling_company()
    print(types)
    products = list(types.keys())
    values = list(types.values())
    # -------- Top 25 products    ---------------#
    best_products = branch.generate_most_sold_products()['count']
    # -------- Types of the products being sold ------ #
    product_types = branch.generate_type_used()
    data_types = list(product_types.keys())
    data_values = list(product_types.values())    
    return render_template("branch.html",
                           branch_manager=branch_manager,
                           net_price=net_price,
                           total_price = total_price,
                           sales=sales,
                           months=month,
                           products=products,
                           values = values,
                           best_products=best_products,
                           data_types = data_types,
                           data_values = data_values)






















# ------------------------------Main Routes to Admin---------------------
@app.route('/Admin_Pannel',methods=['GET'])
def main_render():
    data = Admin_Dashboard()
    total_revenue,net_price= data.generate_revenue()
    
    branch_revenue = data.generate_branch_revenue()
    from_db = Branch.query.order_by(Branch.branch_name).all()
    branches = [i.branch_name.upper() for i in from_db ]
    
    print(branches)
    print(branch_revenue)
    
    revenue = list(branch_revenue.items())
    types = data.generate_type_used()
    products = list(types.keys())
    values = list(types.values())
    monthly = data.generate_monthly_sales()
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sept","Oct","Nov","Dec"]
    d = list(monthly.keys())
    month = [months[d[i].month - 1] for i in range(len(d))]
    sales = list(monthly.values())
   
    return render_template("admin.html", 
                           revenue = revenue,
                           branches = branches,
                           total_revenue=total_revenue,
                           net_price = net_price,
                           products = products,
                           values = values,
                           dates = month,
                           sales = sales
                           )
    

@app.route('/admin_branch',methods=['GET','POST'])
def admin_branch():  
    data = Branch.query.order_by(Branch.branch_name).all()
    error = None
    return render_template("admin_branch.html",data=data,error = error)

@app.route("/deletebranch/<int:branch_id>")
def deletebranch(branch_id):
    branch_delete = Branch.query.get(branch_id)
    db.session.delete(branch_delete)
    try:
       db.session.commit()
    except:
        Error = "Please Delete all the dependencies with this branch"
        flash(Error,"Danger")
    return redirect('/admin_branch')

@app.route("/addbranch",methods=['GET','POST'])
def addbranch():
    if request.method == 'POST':
        data = request.form
        new_branch = Branch(
            branch_id=data["branch_id"],
            branch_name=data["branch_name"].lower(),
            branch_location=data["branch_location"].lower(),
            
        )
        db.session.add(new_branch)
        db.session.commit()
        return redirect("/admin_branch")
    return render_template("add_branch.html") 

@app.route("/editbranch/<int:branch_id>",methods=["GET","POST"])
def editbranch(branch_id):
    branch = Branch.query.get(branch_id)
    if request.method == "POST":
        data = request.form
        branch.branch_name = data["branch_name"]
        branch.branch_location =  data['branch_location']
        db.session.commit()
        return redirect('/admin_branch')
    return render_template("edit_branch.html",branch=branch)

    
# ------------------------------Routes to employee-----------------------#
@app.route('/events')
def events():
    column = ['Name', 'Id', 'Time']
    ds = pd.read_csv('event.csv', names=column)
    with open("templates/events.html", mode="w") as file:
        file.write(ds.to_html())
    return render_template("events.html")


@app.route('/Employee_login', methods=["GET", "POST"])
def Employee_login():
    id = session.get('username')
    edata = Users.query.filter_by(user_id=id).first()
    return render_template("Employee_login.html", edata=edata)
   
  
# --------------------------READ CSV------------------------#
def import_csv(csvfilename):
    data_csv = []
    with open(csvfilename, "r", encoding="utf-8", errors="ignore") as scraped:
        reader = csv.reader(scraped, delimiter=',')
        row_index = 0
        for row in reader:
            if row:  # avoid blank lines
                row_index += 1
                columns = [str(row_index), row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]
                data_csv.append(columns)
    return data_csv

# -----------------------------------PDF ---------------------------#


pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))


# import company's logo
im = Image.open('logo.jpg')
width, height = im.size
ratio = width / height
image_width = 400
image_height = int(image_width / ratio)

# Page information
page_width = 2156
page_height = 3050

# Invoice variables
company_name = 'Hardware Shop'
payment_terms = 'x'
contact_info = 'x'
margin = 100

pdf_file_name = None


def create_invoice(last_row):
    # Reading values from excel file
    customer=last_row[1]
    invoice_number = last_row[6]
    invoice_date = last_row[3]
    customer_phno = last_row[2]
    employee_id = last_row[4]
    employee_name = last_row[5]
    products = "".join(last_row[8])
    total_amount = last_row[9]
    quantity = "".join(last_row[7])

    # Creating a pdf file and setting a naming convention
    c = canvas.Canvas(f"static/files/{str(invoice_number)}.pdf")
    c.setPageSize((page_width, page_height))

    # Drawing the image
    c.drawInlineImage("logo.jpg", page_width - image_width - margin,
                      page_height - image_height - margin,
                      image_width, image_height)

    # Invoice information
    c.setFont('Arial', 80)
    text = 'INVOICE'
    text_width = stringWidth(text, 'Arial', 80)
    c.drawString((page_width - text_width) / 2, page_height - image_height - margin, text)
    y = page_height - image_height - margin * 4
    x = 2 * margin
    x2 = x + 550

    c.setFont('Arial', 45)
    c.drawString(x, y, 'Issued by: ')
    c.drawString(x2, y, company_name)
    y -= margin

    c.drawString(x, y, 'Issued to: ')
    c.drawString(x2, y, customer)
    y -= margin

    c.drawString(x, y, 'Invoice number: ')
    c.drawString(x2, y, str(invoice_number))
    y -= margin

    c.drawString(x, y, 'Invoice date: ')
    c.drawString(x2, y, invoice_date)
    y -= margin

    c.drawString(x, y, 'Customer Phone No: ')
    c.drawString(x2, y, customer_phno)
    y -= margin * 2

    c.drawString(x, y, 'Invoice issued for performed ' + employee_name + ' for ' + invoice_date)
    y -= margin * 2

    c.drawString(x, y, 'Amount including GST: ')
    c.drawString(x2, y, 'INR ' + str(total_amount))
    y -= margin

    c.drawString(x, y, 'Products: ')
    y -= margin
    res = ast.literal_eval(products)
    print(f"ITSRES{res}")
    for i in range(len(res)):
        print(i)
        c.drawString(x, y, res[i])
        y -= margin

    for i in range(len(res)):
        y += margin

    y += margin
    c.drawString(x2, y, 'Quantity: ')
    y -= margin * 1
    res = ast.literal_eval(quantity)
    print(f"ITSRES{res}")
    for i in range(len(res)):
        print(i)
        c.drawString(x2, y, res[i])
        y -= margin

    c.drawString(x, y, 'Total amount: ')
    c.drawString(x2, y, 'INR ' + str(total_amount))
    y -= margin * 3

    c.drawString(x, y, 'Return will only be excepted only after the purchase of item within 2 days')
    y -= margin
    c.drawString(x, y, 'Any issues please contact Ashwini & Shantheri')
    y -= margin
    c.drawString(x, y, 'In case of any questions, contact info@thebestcompany.com')

    # Saving the pdf file
    c.save()
    global pdf_file_name
    pdf_file_name = f"{str(invoice_number)}.pdf"
    return print("INVOICE CREATED")


@app.route('/customers')
def Customer():
    # print("_________________CSV DATA_________________")
    columns = ['CustomerName', 'CustomerPhoneno', 'Date', 'EmployeeID', 'EmployeeName', 'Invoice NO', 'Quantity', 'Products', 'Total']
    df = pd.read_csv('customer_data.csv', names=columns )
    with open("templates/customer.html", mode="w") as file:
        file.write(df.to_html())
    return render_template("customer.html")


state = 0


def check_product(Name):
    print(f"this is the {Name}")
    with open('json/default_products.json') as f1:
        pro_cons = json.load(f1)
        pro_con = pro_cons["products"]
    print("CAME INSIDE FUNTCTION")
    found = False
    pos = None
    Name = int(Name)
    for i in range(len(pro_con)):
        if Name == pro_con[i]['Product_Id']:
            print("The product is found!!")
            found = True
            pos = i
            break
        else:
            found = False

    if found:
        return pos
    else:
        return -1

def product_details(product_id):
    with open("json//refactored_products.json") as file:
        data = json.load(file)
    data = data["products"]
    return data[int(product_id)-1]
    


@app.route('/Billing', methods=['GET', 'POST'])
def Billing():
    id = session.get('username')
    employee_details = Users.query.filter_by(user_id=id).first()
    
    with open('json/default_products.json') as f1:
        pro_cons = json.load(f1)
        pro_con = pro_cons["products"]
    global output, state
    if request.method == "POST":
        print("POST HAPPENED")
        datas = request.form
        print(datas)
        

        Name = request.form.getlist('name')
        Quantity = request.form.getlist('value')
        
        for m in range(len(Name)):
            index = check_product(Name[m])
            print(f"The index is+ {index}")
            if index != -1:
                pro_con[index]["Quantity"] = pro_con[index]["Quantity"] - int(Quantity[m])
                print(f'{pro_con[index]["Quantity"]} = {pro_con[index]["Quantity"]} - {int(Quantity[m])}')
                if pro_con[index]["Quantity"] > 0:
                    state = 0
                else:
                    pro_con[index]["Quantity"] = pro_con[index]["Quantity"] + int(Quantity[m])
                    state = 1
                    break
            else:
                state = 1
                break
      
            if state == 0:
                product_in = product_details(Name[m])               
                new_row = {
                        "name": datas["CustomerName"],
                        "phno": datas["CustomerPhoneno"],
                        "date": datas["Date"],
                        "employee_id": datas["EmployeeId"],
                        "employee_name": datas["EmployeeName"],
                        "branch" : employee_details.user_branch,
                        "ids": datas["Invoice No"],
                        "product_id": Name[m],
                        "product_type":product_in["Product_type"],
                        "product_name":product_in["Product_name"],
                        "product_company":product_in["Company"],
                        "Quantity_ordered": Quantity[m],
                        "Price of commodity":product_in["Price"],
                        "Total_Price": datas['TotalPrice'],
                        "net_price": product_in["net_price"]
                    }
                output = output.append(new_row, ignore_index=True)
        output.to_csv('customer_data.csv', mode='a', header=False, index=False)       
        return render_template("Billing.html", edata=employee_details, products=pro_con, states=state)
    else:
        return render_template("Billing.html", edata=employee_details, products=pro_con, states=state)


@app.route('/download')
def download():
    global pdf_file_name
    print(pdf_file_name)
    if pdf_file_name is None:
        list_of_files = glob.glob('static/files/*.pdf')  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        print(latest_file)
        prefix = "static/files\\"
        file_pdf = remove_prefix(latest_file,prefix)
        print(file_pdf)
        return send_from_directory(directory="static", path=f'files/{file_pdf}')
    return send_from_directory(directory="static", path=f'files/{pdf_file_name}')


# --------------------------Routs to Admin--------------------#


@app.route('/admin', endpoint="admin")
@validate_upload
def admin():
    return render_template('admin.html')




@app.route('/employee', methods=['GET', 'POST'], endpoint="employee")
def employee():
    id = session.get('username')
    branch_manager = Branch.query.filter_by(branch_id=id).first()
    if request.method == "POST":
        employee_data = request.form
        print(employee_data)
        if employee_data["post"] == 'adding':
            # Creating the employee 
            hash_and_salted_password = generate_password_hash(
                employee_data["Password"],
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_emp = Users(
                user_id = employee_data["Employee Id"],
                user_username = employee_data["Name"],
                user_password =  hash_and_salted_password,
                user_branch = branch_manager.branch_name
            )
            db.session.add(new_emp)
            db.session.commit()
            emp_list = Users.query.order_by(Users.user_username).all()
            return render_template('employee.html', data=emp_list,branch_manager =branch_manager)

        elif employee_data['post'] == 'Deleting':
            ID = employee_data['Employee Id']
            Users.query.filter_by(user_id=ID).delete()
            try:
                db.session.commit()
                emp_list = Users.query.order_by(Users.user_username).all()
                return render_template("employee.html", data=emp_list,branch_manager =branch_manager)
            except:
                return render_template('employee.html', data=emp_list, warning=1,branch_manager =branch_manager)            

    else:
        emp_list = Users.query.order_by(Users.user_username).all()
        return render_template('employee.html', data=emp_list,branch_manager =branch_manager)


@app.route('/products', methods=['GET', 'POST'], endpoint="products")
def products():
    id = session.get('username')
    branch_manager = Branch.query.filter_by(branch_id=id).first()
    global index
    if request.method == "POST":
        imd = request.form
        print(imd)
        if imd['post'] == 'adding':
            new_product = {
                "Product_Id": int(imd["Product Id"]),
                "Product_name": imd['Name'].title(),
                "Product_type": imd['Type'],
                "Quantity": int(imd['Quantity']),
                "Price": int(imd['Price'])
                 }
            print(new_product)
            with open('json/default_products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]
                for i in pro_con:
                    if new_product["Product_Id"] == i["Product_Id"]:
                        return render_template('products.html',branch_manager=branch_manager, data=pro_con, warning=1)

                pro_con.append(new_product)

            write_json(pro_cons)
            return render_template('products.html', data=pro_con,branch_manager=branch_manager)

        elif imd['post'] == 'Deleting':
            ID = int(imd['Product Id'])
            with open('json/default_products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]

            if search(pro_con, ID):
                pro_con.pop(index)
                print("____________list is____________")
                print(pro_con)
                write_json(pro_cons)
                return render_template('products.html', data=pro_con,warning=0,branch_manager=branch_manager)
            else:
                return render_template('products.html', data=pro_con, warning=1,branch_manager=branch_manager)

        elif imd['post'] == 'Modifying':
            print(imd)
            ID = int(imd['Product Id'])
            with open('json/default_products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]

            if search(pro_con, ID):
                print(f"{index} Actually not found ")
                pro_con[index]["product_id"] = int(imd['Product Id'])
                pro_con[index]["name"] = imd['Name'].title()
                pro_con[index]["type"] = imd['Type']
                pro_con[index]["quantity"] = int(imd['Quantity'])
                pro_con[index]["price"] = int(imd['Price'])
                print("____________list is____________")
                print(pro_con)
                write_json(pro_cons)
                return render_template('products.html', data=pro_con,branch_manager=branch_manager)
            else:
                flash("Invalid ID","info")
                return render_template('products.html', data=pro_con,branch_manager=branch_manager)

    else:
        with open('json/default_products.json') as f1:
            pro_cons = json.load(f1)
            pro_con = pro_cons["products"]
        return render_template('products.html', data=pro_con,branch_manager=branch_manager)


if __name__ == "__main__":
    app.run( debug=True)

