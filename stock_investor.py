# -*- coding: utf-8 -*-

import configparser

from telethon.errors import SessionPasswordNeededError
from telethon import TelegramClient, events, sync
import MetaTrader5 as mt5

#import config
api_id = "{telegram_id}"
api_hash = "{telegram_hash}"


# use full phone number including + and country code
phone = "{phone}"
username = "{username}"


#List of channels, must be stored in a database later
channels = ["https://t.me/+HKk01IiDEkdjN2E8"]

def read_config():
    # Reading Configs
    config = configparser.ConfigParser()
    config.read("config.ini")
    
    # Setting configuration values
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']
    
    api_hash = str(api_hash)
    
    phone = config['Telegram']['phone']
    username = config['Telegram']['username']


#Extracting stock command from message
def extract_command(lines):
    #This will be changed by the telegram message
    #f = open("C:/Users/karim/OneDrive/Bureau/stock_command.txt","r")
    #lines = f.readlines()
    
    order = {"TP":"","LOT":"","ACTION":"","SYMBOL":""}
    lines = lines.split("\n")
    for line in lines:
        print(line)
        #Extract stock name
        if(line.find("BUY")!=-1 or line.find("SELL")!=-1 ):
            cmd = line.split(" ")
            if(line.find("BUY")!=-1):
                order["ACTION"] = "BUY"
            else:
                order["ACTION"] = "SELL"
            order["SYMBOL"] = cmd[1]
            order["LOT"] = cmd[2]
            
        #Extract TP 
        if(line.find("SL")!=-1):
            order["SL"] = line[line.find("SL")+3:]
            
        #Extract SL
        if(line.find("TP1")!=-1):
            order["TP1"] = line[line.find("TP1")+4:]
        if(line.find("TP2")!=-1):
            order["TP2"] = line[line.find("TP2")+4:]
        if(line.find("SL3")!=-1):
            order["TP3"] = line[line.find("TP3")+4:]
    print(order)
    return order

def connect_telegram(username, api_id, api_hash):
    # Create the client and connect
    client = TelegramClient(username, api_id, api_hash)
    client.start()
    print("======= Telegram Client Opened =======")
    # Ensure you're authorized
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))
    return client

def place_order(order_type,lot,symbol,tp,sl):
    # Extract symbol point
    point = mt5.symbol_info(symbol).point
    
    # Choose the deviation
    deviation = 10
    
    # Find the filling mode of symbol
    filling_type = mt5.symbol_info(symbol).filling_mode
    request = {}
    if(order_type == "BUY"):
        # Create dictionnary request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(symbol).ask,
            "deviation": deviation,
            "tp": mt5.symbol_info_tick(symbol).ask + 100*point,
            "sl": mt5.symbol_info_tick(symbol).ask - 100*point, 
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
        }
    elif (order_type == "SELL"):
       # Create dictionnary request
       request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(symbol).bid,
            "deviation": deviation,
            "tp": mt5.symbol_info_tick(symbol).ask - 100 * point,
            "sl": mt5.symbol_info_tick(symbol).ask + 100 * point, 
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
        }
    Test = mt5.order_check(request).comment
    if(Test == "Done" ):
        print(mt5.order_send(request))

read_config()
client = connect_telegram(username, api_id, api_hash)

#Init MetaTrader
mt5.initialize()

#Listen to new messages for each telegram channel
for channel in channels:
    channel = client.get_entity(channels[0])
    @client.on(events.NewMessage)
    async def my_event_handler(event):
        order = extract_command(event.raw_text)    
        print("Placing new order!")
        place_order(order["ACTION"],float(order["LOT"]),order["SYMBOL"],float(order["SL"]),float(order["TP1"]))
    client.run_until_disconnected()
