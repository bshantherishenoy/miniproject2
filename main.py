from flask import Flask, render_template, request, redirect
import json


app = Flask(__name__)

index = None
# -----------------------Data---------------------------#
with open('json/users.json') as f:
    contents = json.loads(f.read())


def write_json(data, filename="json/products.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def search(list, n):
    global index
    for i in range(len(list)):
        if list[i]["product_id"] == n:
            index = i
            return True
    return False


# ---------------------Routes---------------------------#


@app.route('/')
def home():
    num = 0
    return render_template('index.html', post=num)


@app.route('/admin')
def admin():
    admindata = contents['admin']
    return render_template('admin.html', ad=admindata)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        data = request.form
        if data['submit_button'] == 'Administrator':
            if data['Name'] == contents['admin']['name'] and data['Password'] == contents['admin']['password']:
                return redirect("admin", code=302)
            else:
                num = 1
                return render_template("index.html", post=num)

        elif data['submit_button'] == 'Employee':
            for i in contents['employee']:
                if data['Name'] == i['name'] and data['Password'] == i['password']:
                    return render_template("signup.html")
                else:
                    num = 1
                    return render_template("index.html", post=num)
        else:
            num = 1
            return render_template("index.html", post=num)

    else:
        num = 1
        return render_template("index.html", post=num)


@app.route('/products', methods=['GET', 'POST'])
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
                return render_template('products.html', data=pro_con,warning=1)

        elif imd['post'] == 'Modifying':
            print(imd)
            ID = int(imd['Product Id'])
            with open('json/products.json') as f1:
                pro_cons = json.load(f1)
                pro_con = pro_cons["products"]

            if search(pro_con,ID):
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
                return render_template('products.html', data=pro_con,warning=1)

    else:
        with open('json/products.json') as f1:
            pro_cons = json.load(f1)
            pro_con = pro_cons["products"]
        return render_template('products.html', data=pro_con)


if __name__ == "__main__":
    app.run(debug=True)

# ----------  CANVAS ------------------#
# ----------   CODE  ------------------#
# -------------users.json-------------#
# def add_employees():
#     pass
# def delete():
#     pass
# #-------------products.json------------#
# def add_products():
#     pass
# def del_prod():
#     pass
# def update():
#     pass
# def modify():
#     pass
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
