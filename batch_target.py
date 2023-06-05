'''
PURPOSE : RETURN DAILY BATCH NAME
'''
import datetime
import pandas as pd

# COIN LIST PATH
name_path = '.\\document\\coin_download_link.csv'

def extract_batch_coin() :  
    # TODAY Parameter
    # Get the current date
    current_date = datetime.datetime.now()
    formatted_date = current_date.strftime('%Y_%m_%d')

    # Get the day of the week as an integer (Monday is 0 and Sunday is 6)
    day_of_week = current_date.weekday()

    # Coin name
    coin_name = pd.read_csv(name_path)
    batch_coin = coin_name.loc[coin_name['Batch_day'] == day_of_week].reset_index(drop=True)
    
    return batch_coin, day_of_week, current_date

if __name__ == '__main__':
    batch_coin, day_of_week, current_date = extract_batch_coin()