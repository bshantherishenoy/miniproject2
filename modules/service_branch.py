import pandas as pd
class Branch_Service:
    def __init__(self,branch_manager):
        self.branch_name = branch_manager.branch_name
        self.branch_id = branch_manager.branch_id
        self.branch_loaction = branch_manager.branch_location
        self.df = pd.read_csv("C://Users//shant//PycharmProjects//pythonProject//miniproject2//bill_stick.csv")
        self.df['date'] = pd.to_datetime(self.df.date,  infer_datetime_format=True, errors ='coerce')
        self.df["count"] = 1
        self.df = self.df[self.df["branch"] ==self.branch_name]
    def generate_revenue(self):
        net_price = self.df["net_price"].sum()
        total_price = self.df["Total_price"].sum()
        return round(net_price),round(total_price)
    def generate_monthly_sales(self):
        data = (self.df).groupby(pd.Grouper(key="date", freq="M")).sum()
        return data.to_dict()['Total_price']
    
    def generate_type_used(self):
        # Getting the type value
        x = self.df.groupby('product_type').sum()
        print(x)
        return x.to_dict()['Quantity_ordered']
    def generate_most_sold_products(self):
        aux = self.df[["product_name","product_company","count"]]
        data = aux.groupby(["product_name","product_company"]).sum()
        data = data.sort_values("count",ascending=False)
        top_25 = data.head(25)
        return top_25.to_dict()
    
    def top_five_selling_company(self):
        aux = self.df[["product_company","count"]]
        data = aux.groupby(["product_company"]).sum()
        data = data.sort_values("count",ascending=False)
        data = data.head(5)
        return data.to_dict()["count"]
              
    