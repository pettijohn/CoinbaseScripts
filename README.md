# CoinbaseScripts
Utilities for Coinbase API

* Set up your [Coinbase](https://developers.coinbase.com/api/v2#api-key) and [GDAX](https://docs.gdax.com/#authentication) API keys. 
Create each key to have READ ONLY access to your account. 
Log into each account, and create json files of the following format. DO NOT COMMIT THEM TO GIT (gitignore does the needful--but be safe):


## gdaxApiKey.json
```json
{
    "sandbox": {
        "apiKey": "",
        "apiSecret": "",
        "passphrase": ""
    },
    "prod" : {
        "apiKey": "",
        "apiSecret": "",
        "passphrase": ""
    }
}
```
