from TrailingStopLoss import lambdaHandler
from functools import reduce
import json
import sys

if len(sys.argv) < 8:
    print("Usage: tsl <stage> <order> <crypto> <minBalance> <amountToSell> <stopTriggerPercent> <limitPercent>")
    print("   where json input keys (all required):")
    print("   stage:              prod|sandbox")
    print("   order:              place|dryrun")
    print("   crypto:             BTC|ETH|any supported GDAX asset that has a USD trade pair")
    print("   minBalance:         decimal amount of crypto that must remain in account to initiate sell")
    print("   amountToSell:       decimal amount of crypto")
    print("   stopTriggerPercent: ratio of 24hr high e.g. 0.90")
    print("   limitPercent:       ratio of 24hr high e.g. 0.89")
    quit()

event =  {"stage": sys.argv[1], "order": sys.argv[2], "crypto": sys.argv[3], "minBalance": sys.argv[4], 
    "amountToSell": sys.argv[5], 'stopTriggerPercent': sys.argv[6], 'limitPercent': sys.argv[7]}
print(json.dumps(event))

if not reduce((lambda p,k: p and (k in event)), ['stage', 'order', 'crypto', 'minBalance', 'amountToSell', 'stopTriggerPercent', 'limitPercent'], True):
    print("ERROR - event input is incomplete.")
lambdaHandler(event, None)