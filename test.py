import requests
import json

def check_dex_paid(contract_address):
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

    response = requests.get(url, headers=headers)
    data = json.loads(response.text)  # Correctly parse the JSON response

    result = ""
    if data and 'pairs' in data and data['pairs']:
        for pair in data['pairs']:  # Access the 'pairs' key in the JSON response
            base_token = pair['baseToken']
            dex_id = pair['dexId']
            is_paid = True  # Data found, so DEX is paid
            result += (f"Token Name: {base_token['name']}\n"
                       f"Ticker: {base_token['symbol']}\n"
                       f"Address: {base_token['address']}\n"
                       f"DEX: {dex_id}\n"
                       f"Paid: {is_paid}\n\n")
    else:
        result = "No pairs data found in the response.\nDEX: Not Paid"
    
    return result

# Example usage
print(check_dex_paid("4T2ChULRsrGSLtdNh665RTq4HMjW1PvP2x38pm2Kpump"))

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

    print(f"Ticker: {ticker}")
    print(f"Total Bundles: {total_bundles}")
    print(f"Total Holding Amount: {total_holding_amount}")
    print(f"Total Holding Percentage: {total_holding_percentage}")
    print(f"Total Percentage Bundled: {total_percentage_bundled}")
    print(f"Total SOL Spent: {total_sol_spent}")

    for bundle in data.get("bundles", []):
        if isinstance(bundle, dict):
            token_percentage = bundle.get("token_percentage", "N/A")
            unique_wallets = bundle.get("unique_wallets", "N/A")
            print(f"Bundle Token Percentage: {token_percentage}")
            print(f"Unique Wallets: {unique_wallets}")

if __name__ == "__main__":
    contract_address = "BnMPfgEwuuez1TFtmzbUbFCtBMsgVLKjhud311tpump"
    test_fetch_bundle_info(contract_address)
