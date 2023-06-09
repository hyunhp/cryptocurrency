import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import dataframe_image as dfi

import os
from batch_target import extract_batch_coin
from download_csv import download_makedirs

from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Get daily batch coin information
batch_coin, day_of_week, current_date = extract_batch_coin()
formatted_date = current_date.strftime('%Y_%m_%d')
download_path = download_makedirs(day_of_week)

coin_lst = [i for i in os.listdir(download_path) if '.csv' in i]

# Makedir for saving forecasted images
def save_forecasted_makedirs(day_of_week, formatted_date):
    image_path  = os.getcwd() + '\\forecasted image\\' + str(day_of_week) + f'\\{formatted_date}'
    data_path   = os.getcwd() + '\\forecasted data\\' + str(day_of_week) + f'\\{formatted_date}'
    chart_path  = os.getcwd() + '\\forecasted chart\\' + str(day_of_week) + f'\\{formatted_date}'

    # Set the save image path
    if not os.path.exists(image_path):
        os.makedirs(image_path + '\\period')
        os.makedirs(image_path + '\\whole')
    
    # Set the save dataframe path
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    
    # Set the save chart path
    if not os.path.exists(chart_path):
        os.makedirs(chart_path)

    return image_path, data_path, chart_path

def color_negative_positive(value):
    if isinstance(value, (int, float)) and value < 0:
        color = 'blue'
    elif isinstance(value, (int, float)) and value >= 0:
        color = 'red'
    else:
        color = 'black'
    return 'color: {}'.format(color)

class forecast_model:
    def __init__(self, dataframe, max_date, future_days, image_path, data_path):
        self.dataframe = dataframe.copy()
        self.max_date = max_date
        self.future_days = future_days
        self.image_path = image_path
        self.data_path = data_path
    
    def model(self):
        train_df = self.dataframe.iloc[-self.max_date:].copy()

        # Set the date column as the index
        train_df['snapped_at'] = pd.to_datetime(train_df['snapped_at'])
        train_df.set_index(pd.DatetimeIndex(train_df['snapped_at']), inplace=True)
        train_df.sort_index(inplace=True)

        # Fit the ARIMA model
        model = ARIMA(train_df['price'], 
                      order=(1, 2, 2), 
                      enforce_stationarity=False, 
                      enforce_invertibility=False)
        model_fit = model.fit()

        # Forecast 7 days future prices
        forecast = model_fit.get_forecast(steps=self.future_days)
        forecast_values = forecast.predicted_mean
        conf_int = forecast.conf_int(alpha=0.9)  # Decrease alpha for a narrower interval (e.g., alpha=0.01)

        # Calculate percentage change from the last day in df to predicted values for 1 to 7 days
        last_day_price = train_df['price'].iloc[-1]
        percentage_change = (forecast_values / last_day_price - 1) * 100

        # Create a new index for the forecasted values
        forecast_index = pd.date_range(start=train_df.index[-1], periods=7, freq='D')
        forecast_values = forecast_values.tolist()

        return train_df, forecast_index, forecast_values, conf_int, percentage_change
    
    def period_chart(self, train_df, forecast_index, forecast_values, conf_int):
        plt.figure(figsize=(12, 8))
        plt.plot(train_df.index, train_df['price'], label='Actual', color='#B399CC')
        plt.plot(forecast_index, forecast_values, label='Forecast', color='red')

        for i in range(0, len(forecast_index) - 1):
            plt.axvspan(forecast_index[i], forecast_index[i] + pd.Timedelta(days=1), facecolor='#D8BFD8', alpha=0.3)

        lower_bound = conf_int['lower price'].tolist()
        upper_bound = conf_int['upper price'].tolist()
        plt.fill_between(forecast_index, lower_bound, upper_bound, color='red', alpha=0.5, label='Confidence Interval')

        plt.xlabel('Date')
        plt.ylabel('Price ($)')
        plt.title(f'{coin_name} Actual & Forecasted Prices')
        plt.legend(loc='best')
        plt.savefig(f'{image_path}\\period\\{symbol}_period_{formatted_date}.png')

    def whole_chart(self, forecast_index, forecast_values, conf_int):
        df = self.dataframe
        # Set the date column as the index
        df['snapped_at'] = pd.to_datetime(df['snapped_at'])
        df.set_index(pd.DatetimeIndex(df['snapped_at']), inplace=True)
        df.sort_index(inplace=True)

        plt.figure(figsize=(12, 8))
        plt.plot(df.index, df['price'], label='Actual', color ='#B399CC')  # Plot the entire period of the df DataFrame
        plt.plot(forecast_index, forecast_values, label='Forecast', color='red')

        for i in range(1, len(forecast_index)):
            plt.axvspan(forecast_index[i], forecast_index[i] + pd.Timedelta(days=1), facecolor='#D8BFD8', alpha=0.2)

        lower_bound = conf_int['lower price'].tolist()
        upper_bound = conf_int['upper price'].tolist()
        plt.fill_between(forecast_index, lower_bound, upper_bound, color='red', alpha=0.4, label='Confidence Interval')

        plt.xlabel('Date')
        plt.ylabel('Price ($)')
        plt.title(f'{coin_name} Actual & Forecasted Prices')
        plt.legend(loc='best')
        plt.savefig(f'{image_path}\\whole\\{symbol}_whole_{formatted_date}.png')

    def save_matrix(self, forecast_df):
        columns = ['Base Date',  'Forecast Date', 
                   'Base Price', 'Forecast Price',
                   'Percentage Change']
        styled_df = forecast_df[columns].style \
            .set_properties(**{'text-align': 'center'}) \
            .set_table_styles([{'selector': 'th', 'props': [('background-color', '#E7DDE7')]}]) \
            .hide(axis=0) \
            .format(r"{:.2}%", subset=['Percentage Change']) \
            .applymap(color_negative_positive)
        
        # Adjust header height
        styled_df = styled_df.set_table_attributes('style="border-collapse: collapse; font-size: 12px; '
                                                'table-layout: fixed; word-wrap: break-word; '
                                                'margin-bottom: 10px; margin-top: 10px; '
                                                'height: auto !important;"')

        image_path = f'{chart_path}\\{symbol}_chart_{formatted_date}.png'
        dfi.export(styled_df, image_path)

    def save_forecast_values(self, train_df, forecast_index, forecast_values, percentage_change):
        # Create a dataframe with predicted values and percentage change
        forecast_df = pd.DataFrame({
            'Base Date': train_df.index[-1].strftime('%Y_%m_%d'),
            'Forecast Date': (forecast_index + pd.Timedelta(days=1)).strftime('%Y_%m_%d'),
            'Base Price': [train_df['price'].iloc[-1]] * 7,
            'Forecast Price': forecast_values,
            'Percentage Change': percentage_change,
            'Market Cap': self.dataframe['market_cap'].iloc[-1],
            'Total Volume' : self.dataframe['total_volume'].iloc[-1]
        }).reset_index(drop=True)
        forecast_df.to_csv(f'{data_path}\\{symbol}_data_{formatted_date}.csv')

        return forecast_df

if __name__ == '__main__':
    image_path, data_path, chart_path = save_forecasted_makedirs(day_of_week, formatted_date)

    for coin in tqdm(coin_lst):
        coin_df = pd.read_csv(download_path + '/' + coin)
        symbol = coin.split('-')[0]
        coin_name = batch_coin.loc[batch_coin['symbol'] == symbol.upper(), 'coin_name'].values[0]

        forecast_coin = forecast_model(dataframe =coin_df, max_date = 180, 
                                       future_days = 7, image_path =image_path, data_path=data_path) 
        train_df, forecast_index, forecast_values, conf_int, percentage_change = forecast_coin.model()
        forecast_coin.period_chart(train_df, forecast_index, forecast_values, conf_int)
        forecast_coin.whole_chart(forecast_index, forecast_values, conf_int)
        
        forecast_df = forecast_coin.save_forecast_values(train_df, forecast_index, forecast_values, percentage_change)
        forecast_coin.save_matrix(forecast_df)