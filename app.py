# ------------------------IMPORTS ------------------------#
import flask
from flask import Flask, render_template, request, redirect, send_from_directory,flash,session
from regex import F
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
import urllib.request
import numpy as np

import pdfkit


# ---------------------Initializing Dataframe ------------#
output = pd.read_csv("customer_data.csv")

app = Flask(__name__)

app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['SESSION_TYPE'] = "filesystem"

Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', "sqlite:///hardwareshop45.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

@app.route("/analysis_branch",methods=["GET","POST"])
def analysis_branch():
    id = session.get('username')
    branch_manager = Branch.query.filter_by(branch_id=id).first()
    branch = Branch_Service(branch_manager)
    branch.future_branch(branch_manager.branch_name)
    return render_template("branch_analysis.html",branch_manager=branch_manager)

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
@app.route('/count_analysis',methods=['GET','POST'])
def count_analysis():
    data = Admin_Dashboard()
    counts = data.counter_value()["product_id"]
    return render_template("count_analysis.html",counts=counts)

@app.route('/admin_branch_analysis',methods=['GET','POST'])
def admin_branch_analysis():
    all_branch = Branch.query.order_by(Branch.branch_name).all()
    for i in all_branch:
        branch = Branch_Service(i)
        branch.future_branch(i.branch_name)
    return render_template("admin_branch_analysis.html",branch_manager = all_branch)

@app.route('/analysis_admin',methods=["GET","POST"])
def analysis_admin():
    data = Admin_Dashboard()
    future = data.predict_future(18,23)
    return render_template("analysis_admin.html")
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
   
    found = False
    pos = None
    Name = int(Name)
    for i in range(len(pro_con)):
        if Name == pro_con[i]['Product_Id']:
            
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
                        "Total_price": datas['TotalPrice'],
                        "net_price": product_in["net_price"]
                    }
                output = output.append(new_row,ignore_index=True)
                print(output.tail())
                write_json(pro_cons)
        output.to_csv('customer_data.csv', header=True,index=False)       
        return redirect('/Billing')
    else:
        return render_template("Billing.html", edata=employee_details, products=pro_con, states=state)


@app.route('/download')
def download():
    global uuids
    convert_pdf(uuid)
    return send_from_directory(directory="static", path=f'files/{uuid}.pdf')
  



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
        emp_list = Users.query.filter_by(user_branch=branch_manager.branch_name).all()
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

