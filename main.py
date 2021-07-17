# ------------------------IMPORTS ------------------------#
import flask
from flask import Flask, render_template, request, redirect, send_from_directory
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

# ---------------------Initializing Dataframe ------------#
output = pd.DataFrame()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

index = None
indexs = None
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


def write_json(data, filename="json/products.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def write_jsons(data, filename="json/users.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def search(list, n):
    global index
    for i in range(len(list)):
        if list[i]["product_id"] == n:
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
    with open('json/users.json') as f:
        contents = json.loads(f.read())

    if request.method == "POST":
        data = request.form
        if data['submit_button'] == 'Administrator':
            if data['Name'] == contents['admin']['name'] and data['Password'] == contents['admin']['password']:
                flask.session['completed'] = True
                return redirect("admin", code=302)
            else:
                num = 1
                return render_template("index.html", post=num)

        elif data['submit_button'] == 'Employee':
            global flag
            for i in contents['employee']:
                if data['Name'] == i['name'] and check_password_hash(i["password"], data["Password"]) and data['Id'] == i['employee_id']:
                    print(f"{data['Name']} == {i['name']} and {data['Password']} == {i['password']} and {data['Id']} == {i['employee_id']}")
                    flag = True

            if flag:
                # flask.session['completed'] = True
                user = {
                    'Name': data['Name'],
                    'Id': data['Id']
                }
                new_row = user
                x=datetime.datetime.now()
                field_names = ['Name', 'Id', 'Time']
                new_row.update({'Time': str(x)})
                with open('event.csv', 'a') as f_object:
                    dictwriter_object = DictWriter(f_object, fieldnames=field_names)
                    dictwriter_object.writerow(new_row)
                    f_object.close()
                return render_template("Employee_login.html", edata=user)
            else:
                num = 1
                return render_template("index.html", post=num)
        else:
            num = 1
            return render_template("index.html", post=num)

    else:
        num = 0
        flask.session['completed'] = False
        return render_template("index.html", post=num)


# ------------------------------Routes to employee-----------------------#
@app.route('/events')
def events():
    column = ['Name', 'Id', 'Time']
    ds = pd.read_csv('event.csv', names=column)
    with open("templates/events.html", mode="w") as file:
        file.write(ds.to_html())
    return render_template("events.html")


@app.route('/Employee_login/<user>', methods=["GET", "POST"])
def Employee_login(user):
    if type(user) is dict:
        return render_template("Employee_login.html", edata=user)
    else:
        x = user.replace("'", '"')
        data = json.loads(x)
        print(type(data))
        return render_template("Employee_login.html", edata=data)


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
    with open('json/products.json') as f1:
        pro_cons = json.load(f1)
        pro_con = pro_cons["products"]
    print("CAME INSIDE FUNTCTION")
    found = False
    pos = None
    for i in range(len(pro_con)):
        print(f"{Name} == {pro_con[i]['name']}")
        if Name == pro_con[i]['name']:
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


@app.route('/Billing/<user>', methods=['GET', 'POST'])
def Billing(user):
    print(user)
    x = user.replace("'", '"')
    data = json.loads(x)
    print(type(data))
    with open('json/products.json') as f1:
        pro_cons = json.load(f1)
        pro_con = pro_cons["products"]
    global output, state
    if request.method == "POST":
        print("POST HAPPENED")
        datas = request.form
        print(datas)
        new_row = {
            "Invoice NO": datas["Invoice No"],
            "EmployeeId": datas["EmployeeId"],
            "CustomerName": datas["CustomerName"],
            "CustomerPhoneno": datas["CustomerPhoneno"],
            "Date": datas["Date"],
            "EmployeeName": datas["EmployeeName"],
            "Products": request.form.getlist('name'),
            "Price": request.form.getlist('value'),
            "Total": datas['TotalPrice']
        }

        Name = request.form.getlist('name')
        Quantity = request.form.getlist('value')
        print(output.head())
        print(Name)
        print(Quantity)
        for m in range(len(Name)):
            index = check_product(Name[m])
            print(f"The index is+ {index}")
            if index != -1:
                pro_con[index]["quantity"] = pro_con[index]["quantity"] - int(Quantity[m])
                print(f'{pro_con[index]["quantity"]} = {pro_con[index]["quantity"]} - {int(Quantity[m])}')
                print("This is happening")
                if pro_con[index]["quantity"] > 0:
                    print("this came here")
                    state = 0
                else:
                    pro_con[index]["quantity"] = pro_con[index]["quantity"] + int(Quantity[m])
                    state = 1
                    print(f"{state} its True from out this means the values is negative")
                    break
            else:
                state = 1
                print(f"{state} This means the product is not found")
                break
        print(type(user))
        print(type(data))
        print(data)
        if state == 0:
            output = output.append(new_row, ignore_index=True)
            print(output.head())
            print(new_row)
            print(f"{state} its True in")
            output.to_csv('customer_data.csv', mode='a', header=False, index=False)
            data_csv = import_csv("customer_data.csv")
            last_row = data_csv[-1]
            print(last_row)
            create_invoice(last_row)
            write_json(pro_cons)
            return render_template("Billing.html", edata=data, products=pro_con, states=state)
        return render_template("Billing.html", edata=data, products=pro_con, states=state)
    else:
        return render_template("Billing.html", edata=data, products=pro_con, states=state)


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


# @app.route('/shit', endpoint="shit")
# @validate_upload
# def shit():
#     return '<h1>Shit working!!</h1>'


@app.route('/employee', methods=['GET', 'POST'], endpoint="employee")
@validate_upload
def employee():
    if request.method == "POST":
        employee_data = request.form
        print(employee_data)
        if employee_data["post"] == 'adding':
            hash_and_salted_password = generate_password_hash(
                employee_data["Password"],
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_emp = {
                "employee_id": employee_data["Employee Id"],
                "name": employee_data["Name"],
                "password": hash_and_salted_password
            }
            with open('json/users.json') as f1:
                emp = json.load(f1)
                emp_list = emp["employee"]
                for i in emp_list:
                    if new_emp["employee_id"] == i["employee_id"]:
                        return render_template('employee.html', data=emp_list, warning=2)

            emp_list.append(new_emp)
            write_jsons(emp)
            return render_template('employee.html', data=emp_list)

        elif employee_data['post'] == 'Deleting':
            ID = int(employee_data['Employee Id'])
            with open('json/users.json') as f1:
                emp = json.load(f1)
                emp_list = emp["employee"]
            f1.close()
            print("came here")
            if search_for_employee(emp_list, ID):
                print("came inside if")
                emp_list.pop(indexs)
                print("____________list is____________")
                print(emp_list)
                write_jsons(emp)
                return render_template("employee.html", data=emp_list)
            else:
                return render_template('employee.html', data=emp_list, warning=1)

    else:
        with open("json/users.json") as file:
            contents = json.load(file)
            employees = contents["employee"]
        return render_template('employee.html', data=employees)


@app.route('/products', methods=['GET', 'POST'], endpoint="products")
@validate_upload
def products():
    global index
    if request.method == "POST":
        imd = request.form
        print(imd)
        if imd['post'] == 'adding':
            new_product = {
                "product_id": int(imd['Product Id']),
                "name": imd['Name'].title(),
                "type": imd['Type'],
                "quantity": int(imd['Quantity']),
                "price": int(imd['Price'])
                 }
            print(new_product)
            with open('json/products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]
                for i in pro_con:
                    if new_product["product_id"] == i["product_id"]:
                        return render_template('products.html', data=pro_con, warning=1)

                pro_con.append(new_product)

            write_json(pro_cons)
            return render_template('products.html', data=pro_con)

        elif imd['post'] == 'Deleting':
            ID = int(imd['Product Id'])
            with open('json/products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]

            if search(pro_con, ID):
                pro_con.pop(index)
                print("____________list is____________")
                print(pro_con)
                write_json(pro_cons)
                return render_template('products.html', data=pro_con)
            else:
                return render_template('products.html', data=pro_con, warning=1)

        elif imd['post'] == 'Modifying':
            print(imd)
            ID = int(imd['Product Id'])
            with open('json/products.json') as f1:
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
                return render_template('products.html', data=pro_con)
            else:
                return render_template('products.html', data=pro_con, warning=1)

    else:
        with open('json/products.json') as f1:
            pro_cons = json.load(f1)
            pro_con = pro_cons["products"]
        return render_template('products.html', data=pro_con)


if __name__ == "__main__":
    app.run(debug=True)

