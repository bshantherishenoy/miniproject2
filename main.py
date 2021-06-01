import flask
from flask import Flask, render_template, request, redirect , flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

index = None
indexs = None
# -----------------------config----------------------------#


def validate_upload(f):
    def wrapper():
        if 'completed' not in flask.session or not flask.session['completed']:
            return flask.redirect('/')
        return f()
    return wrapper
# -----------------------Data---------------------------#


with open('json/users.json') as f:
    contents = json.loads(f.read())


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


# ----------------------Login Manager------------------#
# login_manager = LoginManager()
# login_manager.init_app(app)
#
#
# @login_manager.user_loader
# def load_user(user_id):
#     return contents['admin']['employee_id'],contents['employee']['employee_id']

# ---------------------Routes---------------------------#


# @app.route('/')
# def home():
#     num = 0
#     return render_template('index.html', post=num)

flag = False

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        data = request.form
        print(data)
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
                print(f"{data['Name']} == {i['name']} and {data['Password']} == {i['password']} and {data['Id']} == {i['employee_id']}")
                if data['Name'] == i['name'] and check_password_hash(i["password"], data["Password"]) and data['Id'] == i['employee_id']:
                    flag = True

            if flag:
                return render_template("signup.html")
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


@app.route('/admin', endpoint="admin")
@validate_upload
def admin():
    return render_template('admin.html')


# @app.route('/shit', endpoint="shit")
# @validate_upload
# def shit():
#     return '<h1>Shit working!!</h1>'


@app.route('/employee', methods=['GET','POST'], endpoint="employee")
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
                "password":hash_and_salted_password
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
