import cbpro
import json

# Do the same for GDAX
with open('gdaxApiKey.json') as keys_file:
    keys = json.load(keys_file)['sandbox']
auth_client = cbpro.AuthenticatedClient(keys['apiKey'], keys['apiSecret'], keys['passphrase'], api_url="https://api-public.sandbox.pro.coinbase.com")
accounts = auth_client.get_accounts()
print(accounts)