import requests
import numpy as np
import pandas as pd
import time
import json
import logging
import os
from threading import Thread
from keep import keep_alive  # Import the keep_alive function from keep.py

# Hardcoded API keys and tokens
TELEGRAM_TOKEN = "6987736147:AAGtzXRQL8d2pkvUijq1X05mdzuyLO8vd5g"  # Your Telegram bot token
API_KEY = "72a7a3627d030f1b8f06ea07f5e30f32007d4e6e338ae584010feb82dab6f86e"  # Your CryptoCompare API key
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Track bot start time for uptime calculation
start_time = time.time()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define symbol lists
SYMBOL_LISTS = {
    "LIST1": ["1INCHUSDT"]
              #,"A8","Aave","ACA","ACE","ACH","ACT","ACX","ADA","AERGO","AGLD","AI16Z","AIN","AITECH","AIXBT","ALCH","ALGO","AI","ALICE","ALPH","ALPINE","ALT","ALU","AMP","ANKR","ANLOG","ANYONE","APE","API3","APT"
              #,"ARB","ARC","ARKM","ARK","ARPA","ASI","ASTO","AR","ASTR","ATH","ATOM","AURORA","AVAAI","AVAIL","AVA","AVAX","AXL","AZERO","BAD","BAI","BANANA","BAND","BAT","BEAM","BGB","BGSC","BICO",
              #"BIO","BLUR","BLZ","BMT","BRN","BSV","BTT","CARV","CELO","CELR","CFX","CHR","CHZ","CKB","CLORE","COOKIE","COREUM","CORE","CREO","CROS","CSPR","CTSI","CVC","CYBER","DEGEN","DENT","DMAIL","DOT"
              #,"DTEC","D","DUSK","EGLD","ELA","ELF","ENJ","ENS","EOS","EPT","ETC","ETHW","FET","FHE","FIDA","FIL","FITFI","FLOW","FLUX","FTN","FUEL","GALA","GAS","GFAL","GHX","GLMR","GLM","GMT","GOMINING","GPS"
              #,"GRASS","GRT","GTC","HBAR","HEI","HIGH","HIVE","HNT","HOOK","HOT","HYPER","IAG","ICE","ICP","ICX","ID","IMX","IOTX","IP","IQ","JASMY","KAIA","KAITO","KAS","KDA","KLAY","KSM","L3","LAT","LINK"
              #,"LNQ","LOOKS","LPT","LRC","LSK"]  # List 1: BTC, LIT

    
    "LIST2": [" LUNA", " LYX", " MAGIC", " MANA", " MANTA"
  , " MASA", " MASK", " MDT", " MERL", " METIS"
  , " ME", " MINA", " MOBILE", " MOCA", " MOVE"
  , " MOVR", " MTL", " MVL", " MYRIA", " NC"
  , " NEAR", " NEXA", " NFP", " NFT", " NIL"
  , " NKN", " NMT", " NS", " NTRN", " NYM"
  , " OAS", " OGN", " OMG", " OM", " ONE"
  , " ONG", " OORT", " OP", " ORAI", " ORBS"
  , " ORDI", " OXT", " PARTI", " PEAQ", " PHA"
  , " PHB", " PLUME", " POL", " POLYX", " POND"

  , " PORTAL", " POWR", " PRIME", " PROMPT", " PROM"
  , " PROPC", " PROPS", " PYTH", " PYUSD", " QKC"
  , " QNT", " QTUM", " QUBIC", " RAD", " RARE"
  , " RDNT", " RIF"," RLC", " ROAM", " ROOT"
  , " ROSE"," RSR", " RSS3"," SAFE", " SAGA"
  , " SAND", " SCR", " SEI", " SFP", " SHELL"
  , " SIGN", " SKL", " SLF", " SNT", " SONIC"
  ," STMX"," STORJ", " STPT", " STRAX", " STX"
  , " SUI", " SWARMS", " SWEAT", " SXP", " SYS"
  , " TAIKO", " TAO", " TEL", " TET", " TIA"
  
  , " TLOS", " TNSR", " TON", " TRB", " TRIAS"
  , " TWT", " U2U", " UMA", " URO", " UXLINK"
  , " VAI", " VANA", " VANRY", " VET", " VIC"
  , " VIRTUAL", " VR", " VTHO", " WAL", " WAVES"
  , " WAXP", " WCT", " WELL", " WILD", " WLD"
  , " WSDM", " W", " XAI"," XCN", " XDC"
  , " XEM", " XION", " XLM", " XPR", " XRD"
  , " XRP", " XTER", " XTZ"," ZBCN", " ZBU"
  , " ZEN", " ZETA", " ZIG", " ZIL", " ZKJ"
  , " ZK", " ZRC", " ZRO", " ZZZ" ]   # List 2: BTC, ETH
}

# Function to fetch data from the API
def fetch_data(symbol, timeframe):
    # Map user-friendly timeframe inputs to API endpoints
    timeframe_map = {
        "15M": ("histominute", 15),  # 15 minutes
        "1H": ("histohour", 1),      # 1 hour
        "4H": ("histohour", 4),      # 4 hours
        "D": ("histoday", 1),        # 1 day
        "W": ("histoday", 7)         # 1 week
    }

    if timeframe not in timeframe_map:
        raise ValueError("Invalid timeframe specified.")

    endpoint, aggregate = timeframe_map[timeframe]
    url = f"https://min-api.cryptocompare.com/data/{endpoint}?fsym={symbol}&tsym=USDT&limit=100&aggregate={aggregate}&api_key={API_KEY}&e=Bitget"

    response = requests.get(url)
    data = response.json()["Data"]
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Convert timestamp to datetime
    df.set_index('time', inplace=True)  # Set time as the index
    return df

# Function to calculate EMA
def calculate_ema(df, period):
    return df['close'].ewm(span=period, adjust=False).mean()

# Function to check for EMA crossovers
def check_crossover(df):
    df['EMA_10'] = calculate_ema(df, 10)
    df['EMA_20'] = calculate_ema(df, 20)
    df['EMA_50'] = calculate_ema(df, 50)

    # Check if EMA 10 and EMA 20 are above EMA 50 in the latest data point
    latest_row = df.iloc[-1]
    is_above = (latest_row['EMA_10'] > latest_row['EMA_50']) and (latest_row['EMA_20'] > latest_row['EMA_50'])

    return is_above

# Function to send a message via Telegram
def send_telegram_message(chat_id, message, reply_markup=None):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return None

# Function to handle the /start command
def handle_start_command(chat_id):
    # Create an inline keyboard with buttons for LIST1 and LIST2
    keyboard = {
        "inline_keyboard": [
            # Buttons for LIST1
            [{"text": "LIST1 - 15M", "callback_data": "/EMA LIST1 15M"},
             {"text": "LIST1 - 1H", "callback_data": "/EMA LIST1 1H"},
             {"text": "LIST1 - 4H", "callback_data": "/EMA LIST1 4H"},
             {"text": "LIST1 - D", "callback_data": "/EMA LIST1 D"},
             {"text": "LIST1 - W", "callback_data": "/EMA LIST1 W"}],

            # Buttons for LIST2
            [{"text": "LIST2 - 15M", "callback_data": "/EMA LIST2 15M"},
             {"text": "LIST2 - 1H", "callback_data": "/EMA LIST2 1H"},
             {"text": "LIST2 - 4H", "callback_data": "/EMA LIST2 4H"},
             {"text": "LIST2 - D", "callback_data": "/EMA LIST2 D"},
             {"text": "LIST2 - W", "callback_data": "/EMA LIST2 W"}],
        ]
    }

    # Welcome message with instructions
    welcome_message = (
        "Welcome! Use the buttons below to get the EMA crossover analysis for a specific list and timeframe.\n\n"
        "You can also use the following commands:\n"
        "/EMA <list_name> <timeframe> - Analyze a specific list and timeframe.\n"
        "/EMA <symbol> <timeframe> - Analyze a specific symbol and timeframe.\n"
        "/status - Check the bot's status.\n")

    # Send the welcome message with the inline keyboard
    send_telegram_message(chat_id, welcome_message, reply_markup=keyboard)

# Function to handle callback queries
def handle_callback_query(callback_query):
    chat_id = callback_query["message"]["chat"]["id"]
    data = callback_query["data"]  # e.g., "/EMA LIST1 15M"

    try:
        # Parse the command
        parts = data.split()
        if len(parts) != 3:
            raise ValueError("Invalid command format.")

        target = parts[1].upper()  # Extract list name or symbol
        timeframe = parts[2].upper()  # Extract timeframe (e.g., 15M)

        # Check if the target is a list or a symbol
        if target in SYMBOL_LISTS:
            analyze_list(target, timeframe, chat_id)
        else:
            analyze_symbol(target, timeframe, chat_id)

    except Exception as e:
        error_message = f"Error: {str(e)}"
        send_telegram_message(chat_id, error_message)

# Function to analyze EMA crossovers for a single symbol
def analyze_symbol(symbol, timeframe, chat_id):
    try:
        df = fetch_data(symbol, timeframe)
        is_above = check_crossover(df)

        # Prepare the message
        message = f"📊 Analysis for {symbol} ({timeframe}):\n\n"
        if is_above:
            message += "✅ Above EMA 10, 20, and 50:\n"
            message += f"-🚀 {symbol}\n"
        else:
            message += "❌ Not above EMA 10, 20, and 50:\n"
            message += f"-🔻 {symbol}\n"

        send_telegram_message(chat_id, message)
    except Exception as e:
        error_message = f"Error analyzing {symbol} ({timeframe}): {str(e)}"
        send_telegram_message(chat_id, error_message)

# Function to analyze EMA crossovers for a list of symbols
def analyze_list(list_name, timeframe, chat_id):
    try:
        if list_name not in SYMBOL_LISTS:
            raise ValueError(f"Invalid list name. Available lists: {', '.join(SYMBOL_LISTS.keys())}.")

        symbols = SYMBOL_LISTS[list_name]
        above_results = []
        not_above_results = []

        for symbol in symbols:
            df = fetch_data(symbol, timeframe)
            is_above = check_crossover(df)

            if is_above:
                above_results.append(f"-🚀 {symbol}")
            else:
                not_above_results.append(f"-🔻 {symbol}")

        # Prepare the message
        message = f"📊 Analysis for {list_name} ({timeframe}):\n\n"
        if above_results:
            message += "✅ Above EMA 10, 20, and 50:\n"
            message += "\n".join(above_results) + "\n\n"
        if not_above_results:
            message += "❌ Not above EMA 10, 20, and 50:\n"
            message += "\n".join(not_above_results)

        send_telegram_message(chat_id, message)
    except Exception as e:
        error_message = f"Error analyzing {list_name} ({timeframe}): {str(e)}"
        send_telegram_message(chat_id, error_message)

# Function to check alerts
def check_alerts():
    while True:
        # Add your alert-checking logic here
        time.sleep(60)  # Check alerts every 60 seconds

# Main function
def handle_telegram_commands():
    last_update_id = None
    while True:
        try:
            # Get updates from Telegram
            url = f"{TELEGRAM_API_URL}/getUpdates"
            params = {"timeout": 30, "offset": last_update_id}
            response = requests.get(url, params=params)
            updates = response.json().get("result", [])

            if not updates:
                logging.info("No updates found.")
            else:
                logging.info(f"Received updates: {updates}")

            for update in updates:
                last_update_id = update["update_id"] + 1  # Update the offset

                # Handle /start command
                if "message" in update and update["message"].get("text") == "/start":
                    chat_id = update["message"]["chat"]["id"]
                    handle_start_command(chat_id)

                # Handle callback queries
                if "callback_query" in update:
                    handle_callback_query(update["callback_query"])

                # Handle /EMA command
                if "message" in update and update["message"].get("text", "").startswith("/EMA"):
                    try:
                        # Parse the command
                        parts = update["message"]["text"].split()
                        if len(parts) != 3:
                            raise ValueError("Invalid command format. Use /EMA LISTNAME TIMEFRAME or /EMA SYMBOL TIMEFRAME.")

                        target = parts[1].upper()  # Extract list name or symbol
                        timeframe = parts[2].upper()  # Extract timeframe (e.g., 15M)

                        # Check if the target is a list or a symbol
                        if target in SYMBOL_LISTS:
                            analyze_list(target, timeframe, update["message"]["chat"]["id"])
                        else:
                            analyze_symbol(target, timeframe, update["message"]["chat"]["id"])

                    except Exception as e:
                        error_message = f"Error: {str(e)}. Please use the format /EMA LISTNAME TIMEFRAME or /EMA SYMBOL TIMEFRAME (e.g., /EMA LIST1 1H or /EMA BTC D)."
                        send_telegram_message(update["message"]["chat"]["id"], error_message)

            # Wait for 1 second before checking for new updates
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in handle_telegram_commands: {e}")
            time.sleep(5)  # Wait before retrying

# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    # Start the Flask server to keep the bot alive
    keep_alive()

    # Start the bot in a separate thread
    bot_thread = Thread(target=handle_telegram_commands)
    bot_thread.daemon = True
    bot_thread.start()

    # Keep the main thread alive
    while True:
        time.sleep(1)
