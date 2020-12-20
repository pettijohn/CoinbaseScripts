from TrailingStopLoss import lambdaHandler
import sys

if len(sys.argv) < 2:
    print("Usage: tsl (sandbox|prod) (dryrun|place)")
params =  {"stage": sys.argv[1], "order": sys.argv[2], 'stopTriggerPercent': '0.850', 'limitPercent': '0.830'}
lambdaHandler(params, None)