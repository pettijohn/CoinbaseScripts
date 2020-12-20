from TrailingStopLoss import lambdaHandler
import sys

if len(sys.argv) < 2:
    print("Usage: tsl (sandbox|prod) (dryrun|place)")
params =  {"stage": sys.argv[1], "order": sys.argv[2]}
lambdaHandler(params, None)