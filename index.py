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
        pass

    def hud_display(self):
        return ""

game_state = GameState()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', project_name="A.M.I - Automated Market Intelligence")

def stream(chat_input, user_memory):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grok_api_key}"
    }
    
    personality_intro = """
    "You are AMI, an Automated Market Intelligence assistant for Solana, Dexscreener, and Pumpfun. Your tasks include verifying DEX payments, analyzing token bundle risks, and providing market insights, all focused on crypto.

Core Functionalities:

- DEX Analysis:  
  Verify if a DEX is 'Paid' or 'Not Paid'.  
  Analyze metadata: market cap, liquidity, 24h volume.

- Token Bundle Risk:  
  Assess risks of centralization, pump-and-dump, or liquidity traps.  
  Flag suspicious tokens based on bundling data.

- Crypto Insights:  
  Discuss Solana, Dexscreener, and Pumpfun trends and performance.  
  Politely decline unrelated topics.

Response Format:

'Ticker name: [Token Name], DEX: [Paid/Not Paid], Bundle: [Initial %/Actual %], Market Cap: [Value].  
Risk analysis: [Summary of potential risks such as centralization, liquidity traps, pump-and-dump schemes, etc.].'

Interaction Rules:

1. Focus on Crypto:  
   Respond only to crypto-related queries (Solana, Dexscreener, Pumpfun).  
   Politely redirect unrelated topics.

2. Concise and Actionable:  
   Provide clear, actionable insights. Avoid unnecessary technical details unless requested.

3. Response Format:  
   Return concise, structured metadata.  
   Begin with direct insights: 'DEX is Paid,' 'Token is Non-OG,' etc.

4. Error Handling:  
   Request missing data if insufficient information is provided.  
   Politely decline non-crypto queries.

5. User Guidance:  
   Ask users to input data in the structured format provided.

6. OG Functionality:  
   Develop tools to verify token originality (OG status) based on smart contract analysis.

End of prompt."
"""
    # Regular expression to detect Solana contract address
    solana_address_pattern = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')
    match = solana_address_pattern.search(chat_input)
    
    if (match):
        contract_address = match.group(0)
        dex_result = check_dex_paid(contract_address)
        bundle_resule = test_fetch_bundle_info(contract_address)
        
        chat_input = f"Contract Address: {contract_address}\n{dex_result},{bundle_resule}"
        print(chat_input)
        
    
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
        result = response.json()['choices'][0]['message']['content']
        print(result)  # Ajoutez cette ligne pour imprimer la réponse
        return result
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
                websites = pair.get('websites', [{'label': 'Website', 'url': 'https://www.sec.gov/submit-tip-or-complaint'}])
                socials = pair.get('socials', [])
                bonded = "Yes" if pair.get('bonded', False) else "No"
                result += (
                    f"DEX: {dex_id}\n"
                    f"Paid: {is_paid}\n"
                    f"Market Cap: {market_cap}\n"
                    f"24h Volume: {volume}\n"
                    f"Liquidity: {liquidity}\n"
                    f"24h Price Change: {price_change}\n"
                    f"24h Transactions: Buys: {txns.get('buys', 'N/A')}, Sells: {txns.get('sells', 'N/A')}\n"
                    f"Ticker: {base_token}\n"
                    f"Websites: {websites}\n"
                    f"Socials: {socials}\n"
                    f"Bonded: {bonded}\n"
                )
                        
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

    result = (
        f"Ticker: {ticker}\n"
        f"Total Bundles: {total_bundles}\n"
        f"Total Holding Amount: {total_holding_amount}\n"
        f"Total Holding Percentage: {total_holding_percentage}\n"
        f"Total Percentage Bundled: {total_percentage_bundled}\n"
        f"Total SOL Spent: {total_sol_spent}\n"
    )

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