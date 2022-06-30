# Generating the total sales .
# Sales comarision with respect to the branch .
# Most sold type from the generated insights . 


import pandas as pd
import datetime
import json

from pandas.tseries.offsets import DateOffset
class Admin_Dashboard:
    def __init__(self):
        self.df = pd.read_csv("C://Users//shant//PycharmProjects//pythonProject//miniproject2//customer_data.csv")
        self.faster = []
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
    def predict_future(self,start,end):
        df = pd.read_csv("C://Users//shant//PycharmProjects//pythonProject//miniproject2//customer_data.csv")
        df = df[["date","Total_price"]]
        df['date'] = pd.to_datetime(df.date,  infer_datetime_format=True, errors ='coerce')
        data = df.groupby(pd.Grouper(key="date", freq="1W")).mean()
        from statsmodels.tsa.stattools import adfuller
        data['s_d'] = data['Total_price'] - data['Total_price'].shift(5)
        from statsmodels.graphics.tsaplots import plot_acf,plot_pacf
        import statsmodels.api as sm
        model  = sm.tsa.statespace.SARIMAX(data['Total_price'],order=(1,1,2),seasonal_order=(1,1,2,5))
        results = model.fit()
        data['forecast'] =  results.predict(start=start,end=end,dynamics=True)
        plot = data[['Total_price','forecast']].plot(figsize=(12,8))
        fig = plot.get_figure()
        fig.savefig("static//assets//output_normal.png")
        from pandas.tseries.offsets import DateOffset
        future_date  = [data.index[-1]+DateOffset(weeks=x) for x in range(1,12)]
        future_dataset_df = pd.DataFrame(index=future_date[1:],columns=data.columns)
        future_df = pd.concat([data,future_dataset_df])
        future_df['forecast'] =  results.predict(start=18,end=33,dynamics=True)
        plot2 = future_df[['Total_price','forecast']].plot(figsize=(12,12))
        fig = plot2.get_figure()
        fig.savefig("static//assets//output_future.png")
        return future_df
   
    def getPredict(self,df,num):
        output = pd.DataFrame()
        data= df.groupby(['product_id']).mean()
        data.reset_index('product_id',inplace=True)
        data1=data[data['product_id']==num]
        self.faster.append([data])
        
    def counter_value(self):
        df = pd.read_csv("C://Users//shant//PycharmProjects//pythonProject//miniproject2//customer_data.csv")
        df['date'] = pd.to_datetime(df.date,  infer_datetime_format=True, errors ='coerce')
        df = df[["date",'branch',"product_id","Quantity_ordered"]]
        with open("C://Users//shant//PycharmProjects//pythonProject//miniproject2//json//refactored_products.json") as file:
            data  = json.load(file)
            data = len(data["products"])
        for i in range(1,data+1):
            self.getPredict(df,i)
        return self.faster[-1][0].to_dict()



