# Generating the total sales .
# Sales comarision with respect to the branch .
# Most sold type from the generated insights . 


import pandas as pd
import datetime
import json

class Admin_Dashboard:
    def __init__(self):
        self.df = pd.read_csv("C://Users//shant//PycharmProjects//pythonProject//miniproject2//bill_stick.csv")
    def generate_revenue(self):
        # Getting the total  revenue of data
        total_revenue = self.df.Total_price.sum()
        net_revenue = self.df.net_price.sum()
        return total_revenue,round(net_revenue)

    def generate_branch_revenue(self):
        # Getting it in the form of the dict 
        x = self.df.groupby('branch').sum()
        print(x)
        return x.to_dict()['Total_price']
                
    def generate_type_used(self):
        # Getting the type value
        x = self.df.groupby('product_type').sum()
        print(x)
        return x.to_dict()['Quantity_ordered']
    def generate_monthly_sales(self):
        # Getting the monthly sales
        self.df['date'] = pd.to_datetime(self.df.date,  infer_datetime_format=True, errors ='coerce')
        data = self.df.groupby(pd.Grouper(key="date", freq="1M")).sum()
        return data.to_dict()['Total_price']
   
            



