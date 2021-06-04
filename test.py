products=[
    {
        "product_id": 7,
        "name": "Toolbox",
        "type": "hardware",
        "quantity": 100,
        "price": 40
    },
    {
        "product_id": 3,
        "name": "Lawnmover",
        "type": "Agriculture",
        "quantity": 90,
        "price": 90
    },
    {
        "product_id": 4,
        "name": "Magnet",
        "type": "hardware",
        "quantity": 100,
        "price": 20
    }
]
Name =['Lawnmover', 'Toolbox']
Quantity= ['1', '1']

for i in range(len(products)):
    for m in range(len(Name)):
        if products[i]["name"] == Name[m]:
            # print(f"{products[i]['quantity']} -= {Quantity[i]}")
            products[i]["quantity"] = products[i]["quantity"]-int(Quantity[i])



print(products)