import flask
from flask import Flask, render_template, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import json
import datetime
import pandas as pd
from csv import DictWriter

# ---------------------Initializing Dataframe --------------#
output = pd.DataFrame()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

index = None
indexs = None
# -----------------------config----------------------------#


@app.context_processor
def inject_today_date():
    return {'today_date': datetime.date.today()}



def validate_upload(f):
    def wrapper():
        if 'completed' not in flask.session or not flask.session['completed']:
            return flask.redirect('/')
        return f()
    return wrapper
# -----------------------Data---------------------------#


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


# ------------------------------Routes to employee--------------#
@app.route('/events')
def events():
    column = ['Name','Id','Time']
    ds = pd.read_csv('event.csv', names=column)
    with open("templates/events.html", mode="w") as file:
        file.write(ds.to_html())
    return render_template("events.html")




@app.route('/Employee_login/<user>', methods=["GET", "POST"])
def Employee_login(user):
    if request.method == "POST":
        return render_template("Employee_login.html", edata=user)
    return render_template("Employee_login.html", edata=user)


@app.route('/customers')
def Customer():
    output.to_csv('customer_data.csv', mode='a', header=False)
    columns = ['invoice', 'CustomerName', 'CustomerPhoneno', 'Date', 'EmployeeID', 'EmployeeName', 'Quantity', 'Product\'s', 'Price', 'Total']
    df = pd.read_csv('customer_data.csv', names=columns)
    with open("templates/customer.html", mode="w") as file:
        file.write(df.to_html())
    return render_template("customer.html")


@app.route('/Billing/<user>', methods=['GET', 'POST'])
def Billing(user):
    print(user)
    x = user.replace("'", '"')
    data = json.loads(x)
    print(type(data))
    with open('json/products.json') as f1:
        pro_cons = json.load(f1)
        pro_con = pro_cons["products"]
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
        global output
        output = output.append(new_row, ignore_index=True)
        print(output.head())
        print(new_row)
        Name = request.form.getlist('name')
        Quantity = request.form.getlist('value')
        Price = request.form.getlist('price')
        print(output.head())
        print(Name)
        print(Quantity)
        for i in range(len(pro_con)):
            for m in range(len(Name)):
                if pro_con[i]["name"] == Name[m]:
                    # print(f"{products[i]['quantity']} -= {Quantity[i]}")
                    pro_con[i]["quantity"] = pro_con[i]["quantity"] - int(Quantity[m])

        write_json(pro_cons)
        print(type(user))
        print(type(data))
        print(data)
        return render_template("Billing.html", edata=data, products=pro_con)
    else:
        return render_template("Billing.html", edata=data, products=pro_con)


# --------------------------Routs to Admin----------------#


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

            with open("json/users.json") as file:
                emp = json.load(file)
                emp_list = emp["employee"]
                emp_list.append(new_emp)
            write_jsons(emp)
            return render_template('employee.html', data=emp_list)

        elif employee_data['post'] == 'Deleting':
            ID = int(employee_data['Employee Id'])
            with open('json/users.json') as f1:
                emp = json.load(f1)
                emp_list = emp["employee"]
            print("came here")
            if search_for_employee(emp_list, ID):
                print("came inside if")
                emp_list.pop(indexs)
                print("________________list is____________")
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
                "name": imd['Name'],
                "type": imd['Type'],
                "quantity": int(imd['Quantity']),
                "price": int(imd['Price'])
                 }
            print(new_product)
            with open('json/products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]
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
                print("________________list is____________")
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
                pro_con[index]["name"] = imd['Name']
                pro_con[index]["type"] = imd['Type']
                pro_con[index]["quantity"] = int(imd['Quantity'])
                pro_con[index]["price"] = int(imd['Price'])
                print("________________list is____________")
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

# ---------------csv------------------#
# def add():
#     pass
# def remove():
#     pass
# def calculate():
#     pass
# def sum_all_amounts():
#     pass

# -----------  DATA  ------------------#
