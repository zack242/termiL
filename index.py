import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response, render_template, session
import json
import re
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clé secrète pour les sessions

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
    session['conversation'] = []  # Initialiser la mémoire de conversation
    return render_template('index.html', project_name="A.M.I - Automated Market Intelligence")

def stream(chat_input, user_memory):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grok_api_key}"
    }
    
    personality_intro = """
Understood! Here's the updated version of the prompt:  

---

**You are AMI, an Automated Market Intelligence Assistant, specializing in Solana, Dexscreener, and Pumpfun. Your primary tasks include verifying DEX payments, analyzing token bundle risks, and providing concise market insights, all within the cryptocurrency domain.**

### Core Functionalities:
- **DEX Payment Verification**: Confirm payment status as 'Paid' or 'Not Paid'.  
- **Token Metadata Analysis**: Provide insights on market cap, liquidity, 24h volume, and other key metrics.  
- **Risk Assessment**: Identify risks such as centralization, pump-and-dump schemes, or liquidity traps.  
- **Token Bundle Monitoring**: Flag suspicious tokens based on bundle data and assess risks.  
- **Trends & Performance Insights**: Share concise market trends and performance metrics related to Solana, Dexscreener, and Pumpfun.  
- **Data Handling**: Only focus on Solana, Dexscreener, and Pumpfun. Politely decline unrelated topics (e.g., other blockchain ecosystems or non-crypto queries).  

### Response Rules:
1. **Initial Token Analysis**:  
   - Respond with **short, concise summaries** that include:  
     - DEX Paid status  
     - Bundle info (Total Percentage Bundled, Centralization %)  
     - Market Cap  
     - Bonded status  
     - Socials (indicate availability: *Twitter OK, Telegram OK, Website OK*)  
     - A brief analysis (risks or standout observations)  
   - Save detailed responses for when the user explicitly requests more information.  

2. **Polite Redirection**:  
   - Politely guide users to relevant channels for non-crypto-related or unsupported queries.  

3. **Actionable Insights**:  
   - Provide clear, structured insights without excessive jargon.  

4. **Missing Data**:  
   - Request any missing or unclear information politely.  

5. **Follow-Up Requests**:  
   - Elaborate on technical details only when asked.  

6. **Originality Check**:  
   - Assess token originality (OG status) using the smart contract or address when applicable.  

### Interaction Examples:  
- **Example Input**:  
  Metadata about a token, including DEX, Paid status, Market Cap, Liquidity, Bundles, and Social links.  

- **Example Initial Response**:  
  - **Ticker:** MINE  
  - **DEX:** Raydium  
  - **Paid:** Yes  
  - **Market Cap:** $287,778  
  - **Bundles:** 62.45% (Total Bundled: 72.57%)  
  - **Bonded:** Yes  
  - **Socials:** Twitter OK, Telegram OK, Website OK  
  - **Analysis:** Strong liquidity but high centralization suggests risks of manipulation or volatility.  

---

Let me know if you'd like further adjustments!
   
    """
    # Regular expression to detect Solana contract address
    solana_address_pattern = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')
    match = solana_address_pattern.search(chat_input)
    
    if match:
        contract_address = match.group(0)
        dex_result = check_dex_paid(contract_address)
        bundle_result = test_fetch_bundle_info(contract_address)
        chat_input = f"Here is some metadata about the token : {contract_address}\n{dex_result},{bundle_result}"
        print(chat_input)  # Ajoutez cette ligne pour imprimer le chat_input
        
    # Ajouter le chat_input à la mémoire de conversation
    if 'conversation' not in session:
        session['conversation'] = []
    session['conversation'].append({"role": "user", "content": chat_input})
    
    # Limiter la mémoire de conversation aux 20 derniers messages
    session['conversation'] = session['conversation'][-20:]

    # Construire les messages pour l'API en incluant la mémoire de conversation
    messages = [{"role": "system", "content": personality_intro}]
    messages.extend(session['conversation'])
    messages.append({"role": "user", "content": f"Memory: {user_memory}"})

    data = {
        "messages": messages,
        "model": "grok-beta",
        "stream": False,
        "temperature": 0
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content']
        print(result)  # Ajoutez cette ligne pour imprimer la réponse

        # Ajouter la réponse de l'IA à la mémoire de conversation
        session['conversation'].append({"role": "assistant", "content": result})
        
        # Limiter la mémoire de conversation aux 20 derniers messages
        session['conversation'] = session['conversation'][-20:]

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
                socials = pair.get('info', [])
                websites = pair.get('websites', [])
                boosts = pair.get('boosts', {}).get('active', 'N/A')
                result += (
                    f"DEX: {dex_id}\n"
                    f"Paid: {is_paid}\n"
                    f"Market Cap: {market_cap}\n"
                    f"24h Volume: {volume}\n"
                    f"Liquidity: {liquidity}\n"
                    f"24h Price Change: {price_change}\n"
                    f"24h Transactions: Buys: {txns.get('buys', 'N/A')}, Sells: {txns.get('sells', 'N/A')}\n"
                    f"Ticker: {base_token}\n"
                    f"Socials: {socials}\n"
                    f"Boosts: {boosts}\n"
                    f"Websites: {websites}\n"
        
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

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    
        ticker = data.get("ticker", "N/A")
        total_bundles = data.get("total_bundles", "N/A")
        total_holding_amount = data.get("total_holding_amount", "N/A")
        total_holding_percentage = data.get("total_holding_percentage", "N/A")
        total_percentage_bundled = data.get("total_percentage_bundled", "N/A")
        total_sol_spent = data.get("total_sol_spent", "N/A")
        bonded = "No (Still on Pumpfun)" if not data.get('bonded', False) else "Yes"

        result = (
            f"Ticker: {ticker}\n"
            f"Total Bundles: {total_bundles}\n"
            f"Total Holding Amount: {total_holding_amount}\n"
            f"Total Holding Percentage: {total_holding_percentage}\n"
            f"Total Percentage Bundled: {total_percentage_bundled}\n"
            f"Total SOL Spent: {total_sol_spent}\n"
            f"Bonded: {bonded}\n"
        )

        for bundle in data.get("bundles", []):
            if isinstance(bundle, dict):
                token_percentage = bundle.get("token_percentage", "N/A")
                unique_wallets = bundle.get("unique_wallets", "N/A")
                result += (f"Bundle Token Percentage: {token_percentage}\n"
                           f"Unique Wallets: {unique_wallets}\n")

        return result
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request failed: {e}")
        return "An error occurred while fetching bundle info."

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