import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response, render_template
import json
import re
import logging

app = Flask(__name__)

load_dotenv()

grok_api_key = os.getenv('GROK_API_KEY')

class GameState:
    def __init__(self):
        self.location = "Terminal"

    def update(self, chat_input):
        # Update the game state based on user input
        # This function can be expanded to handle specific actions and update the game state accordingly
        pass

    def hud_display(self):
        return ""

game_state = GameState()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

def stream(chat_input, user_memory):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grok_api_key}"
    }
    
    personality_intro = "hi"
   
    # Regular expression to detect Solana contract address
    solana_address_pattern = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')
    match = solana_address_pattern.search(chat_input)
    
    if match:
        contract_address = match.group(0)
        dex_result = check_dex_paid(contract_address)
        bundle_resule = test_fetch_bundle_info(contract_address)
        
        chat_input = f"Contract Address: {contract_address}\n{dex_result},{bundle_resule}"
        
        

    data = {
        "messages": [
            {"role": "system", "content": personality_intro},
            {"role": "user", "content": f"Memory: {user_memory}"},
            {"role": "user", "content": f"{chat_input}. Please provide a short answer only."}
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request failed: {e}")
        return "An error occurred while processing your request."

def check_dex_paid(contract_address):
    app.logger.info(f"Checking DEX for contract address: {contract_address}")
    url = f"https://www.checkdex.xyz/api/dexscreener?tokenAddress={contract_address}"
    headers = {
        "accept": "*/*",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }
    referrer = "https://www.checkdex.xyz/"
    referrer_policy = "strict-origin-when-cross-origin"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = json.loads(response.text)  # Correctly parse the JSON response
        app.logger.info(f"Response data: {data}")

        result = ""
        if data and 'pairs' in data and data['pairs']:
            for pair in data['pairs']:  # Access the 'pairs' key in the JSON response
                base_token = pair['baseToken']
                dex_id = pair['dexId']
                is_paid = True  # Data found, so DEX is paid
                market_cap = pair.get('marketCap', 'N/A')
                volume = pair.get('volume', {}).get('h24', 'N/A')
                liquidity = pair.get('liquidity', {}).get('usd', 'N/A')
                price_change = pair.get('priceChange', {}).get('h24', 'N/A')
                txns = pair.get('txns', {}).get('h24', {})

                result += (f"Token Name: {base_token['name']}\n"
                           f"Ticker: {base_token['symbol']}\n"
                           f"Address: {base_token['address']}\n"
                           f"DEX: {dex_id}\n"
                           f"Paid: {is_paid}\n"
                           f"Market Cap: {market_cap}\n"
                           f"24h Volume: {volume}\n"
                           f"Liquidity: {liquidity}\n"
                           f"24h Price Change: {price_change}\n"
                           f"24h Transactions: Buys: {txns.get('buys', 'N/A')}, Sells: {txns.get('sells', 'N/A')}\n\n")
        else:
            result = "No pairs data found in the response.\nDEX: Not Paid"
        
        app.logger.info(f"Result: {result}")
        return result
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request failed: {e}")
        return "An error occurred while processing your request."

def test_fetch_bundle_info(contract_address):
    url = f"https://trench.bot/api/bundle_info/{contract_address}"
    headers = {
        "accept": "*/*",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }
    referrer = f"https://trench.bot/bundles/{contract_address}"
    referrer_policy = "strict-origin-when-cross-origin"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    ticker = data.get("ticker", "N/A")
    total_bundles = data.get("total_bundles", "N/A")
    total_holding_amount = data.get("total_holding_amount", "N/A")
    total_holding_percentage = data.get("total_holding_percentage", "N/A")
    total_percentage_bundled = data.get("total_percentage_bundled", "N/A")
    total_sol_spent = data.get("total_sol_spent", "N/A")

    result = (f"Ticker: {ticker}\n"
              f"Total Bundles: {total_bundles}\n"
              f"Total Holding Amount: {total_holding_amount}\n"
              f"Total Holding Percentage: {total_holding_percentage}\n"
              f"Total Percentage Bundled: {total_percentage_bundled}\n"
              f"Total SOL Spent: {total_sol_spent}\n")

    for bundle in data.get("bundles", []):
        if isinstance(bundle, dict):
            token_percentage = bundle.get("token_percentage", "N/A")
            unique_wallets = bundle.get("unique_wallets", "N/A")
            result += (f"Bundle Token Percentage: {token_percentage}\n"
                       f"Unique Wallets: {unique_wallets}\n")

    return result

@app.route('/completion', methods=['POST'])
def completion_api():
    if request.method == "POST":
        data = request.form
        chat_input = data['chat_input']
        user_memory = data.get('user_memory', '')
        return Response(stream(chat_input, user_memory), mimetype='text/event-stream')
    else:
        return Response(None, mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)