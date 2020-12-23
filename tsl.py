from TrailingStopLoss import lambdaHandler
import sys

if len(sys.argv) < 5:
    print("Usage: tsl (sandbox|prod) (dryrun|place) <stop trigger percent e.g. 0.850> <limit percent e.g. 0.830>")
    quit()
params =  {"stage": sys.argv[1], "order": sys.argv[2], 'stopTriggerPercent': sys.argv[3], 'limitPercent': sys.argv[4]}
lambdaHandler(params, None)