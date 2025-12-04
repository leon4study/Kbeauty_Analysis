import pandas as pd, os
from reviews import load_reviews
from items import load_items
from mysql1 import MySqlClient
from dotenv import load_dotenv
load_dotenv()


ID = os.environ.get('ID') 
PW = os.environ.get('PW')
DB_SERVER_HOST = os.environ.get("DB_SERVER_HOST")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_DATABASE = os.environ.get("DB_DATABASE")
DB_PORT = os.environ.get("DB_PORT")

def main():

    my_sql_client = MySqlClient(
            server_name=DB_SERVER_HOST,
            database_name=DB_DATABASE,
            username=DB_USERNAME,
            password=DB_PASSWORD,
            port=DB_PORT
        )
    

    path ='/Users/jun/GitStudy/Data_4/Data/project5/'
    items_df = pd.read_csv(path+"items.csv", index_col= False)
    reviews_df = pd.read_csv(path+"reviews.csv", index_col= False)

    load_items(items_df, my_sql_client, "insert")
    print("items_insert")
    load_reviews(reviews_df, my_sql_client, "insert")
    print("reviews_insert")

main()