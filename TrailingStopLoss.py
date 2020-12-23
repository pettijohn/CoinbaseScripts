import cbpro
from decimal import Decimal, ROUND_DOWN
import json
import sys


# Dry run an order - prepare JSON in the same manner as the post order method on API
def prepOrder(product_id, side, order_type, **kwargs):
    params = {'product_id': product_id,
                  'side': side,
                  'type': order_type}
    params.update(kwargs)
    return json.dumps(params, indent=2)

def lambdaHandler(event, context):
    # Validate @event is correct
    if not ('stage' in event and 'order' in event and 'stopTriggerPercent' in event and 'limitPercent' in event):
        print("ERROR - event input is incomplete.")
        return False
        quit()

    # Sandbox or prod? 
    if event['stage'] == "prod":
        print ("DANGER - USING PROD")
        stage = 'prod'
        apiEndpoint = "https://api.pro.coinbase.com"
    else:
        print ("Using SANDBOX API endpoint")
        stage = 'sandbox'
        apiEndpoint = "https://api-public.sandbox.pro.coinbase.com"

    if event['order'] == "place":
        reallyPlaceOrder = True
        print("REALLY PLACING ORDER")
    else:
        reallyPlaceOrder = False
        print("Dry run order")

    # Load API key
    with open('gdaxApiKey.json') as keys_file:
        keys = json.load(keys_file)[stage]
    auth_client = cbpro.AuthenticatedClient(keys['apiKey'], keys['apiSecret'], keys['passphrase'], api_url=apiEndpoint)

    # Identify all accounts with nontrivial balance and prepare to liquidate them all 
    accounts = filter(lambda a: Decimal(a['balance']) > 1 and (a['currency'] == 'ETH' or a['currency'] == 'BTC'), auth_client.get_accounts())
    totalLiquidation     = Decimal('0.0')
    totalLiquidationLast = Decimal('0.0')
    totalLiquidationMax  = Decimal('0.0')

    # For each account
    for account in accounts:
        # Prepare symbols & get balance 
        crypto = account['currency']
        product = crypto + '-USD'
        # Round down to precision supported by API. Without specifying down, sometimes it will round up, 
        # which will cause an insufficient funds error 
        totalCryptoToSell = Decimal(account['balance']).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)

        # Get 24 hour stats e.g. high, low, last
        # https://api.pro.coinbase.com/products/BTC-USD/stats
        public_client = cbpro.PublicClient(api_url=apiEndpoint)
        stats = public_client.get_product_24hr_stats(product)

        # Trailing Stop Loss rule, aka Bubble Chaser Liquidator
        last                = Decimal(stats['last'])
        high                = Decimal(stats['high'])                    # e.g. 24000
        stopTriggerPercent  = Decimal(event['stopTriggerPercent'])
        limitPercent        = Decimal(event['limitPercent'])
        p = Decimal('0.01')                                             # Precision, round to 0.01 for USD
        # When the last trade price is below this amount,
        targetStopUSD       = (high * stopTriggerPercent).quantize(p)   # e.g. 21000 
        # Create a sell order with the price above this amount (if zero, you'd lose it all in a flash crash)
        targetLimitUSD      = (high * limitPercent).quantize(p)         # e.g. 20400
        potentialLiquidationAmount  = (totalCryptoToSell * targetLimitUSD).quantize(p)
        totalLiquidationLast        = totalLiquidationLast + (totalCryptoToSell * last).quantize(p)
        totalLiquidationMax         = totalLiquidationMax + (totalCryptoToSell * high).quantize(p)

        print("=== Bubble Chaser Liquidator Settings ===")
        print("===              {0}              ===".format(product))
        print("24hr high was            {0}".format(high))
        print("Last price was           {0} @ {1}".format(last, (last/high).quantize(p)))
        print("Stop will be             {0} @ {1}".format(targetStopUSD, stopTriggerPercent))
        print("With limit of            {0} @ {1}".format(targetLimitUSD, limitPercent))
        

        if last <= targetStopUSD:
            print("WARN: Trade may execute immediately, last price is below stop price")

        # Check for open orders on this product 
        orders = list(auth_client.get_orders(product))
        placeOrder = False
        if len(orders) > 1:
            # Error state
            print("ABORT: There should be zero or one orders for {0}. Actual: {1}".format(product, len(orders)))
            continue
        if len(orders) == 1:
            # Evaluate if the stop needs to move up
            # '{"id": "c36b3ba0-12cf-481c-a08d-8534e7523149", "price": "18000.00000000", "size": "1.00000000", "product_id": "BTC-USD", "profile_id": "27e860da-56f9-45a9-85dd-6ce3527a51d6", "side": "sell", "type": "limit", "time_in_force": "GTC", "post_only": false, "created_at": "2020-12-19T19:30:39.035213Z", "fill_fees": "0.0000000000000000", "filled_size": "0.00000000", "executed_value": "0.0000000000000000", "status": "active", "settled": false, "stop": "loss", "stop_price": "20000.00000000"}'
            id = orders[0]['id']
            existingStopPriceUSD        = Decimal(orders[0]['stop_price'])
            existingLimitUSD            = Decimal(orders[0]['price'])
            size                        = Decimal(orders[0]['size'])
            existingLiquidationAmount   = existingLimitUSD * size
            print("Existing order with stop {0}".format(existingStopPriceUSD.quantize(p)))
            if existingStopPriceUSD < targetStopUSD:
                # Time to move the sell order higher!
                print("«« Cancelling existing order, ratcheting up stop price to {0}.".format(targetStopUSD))
                if reallyPlaceOrder:
                    cancelResult = auth_client.cancel_order(id)
                    print(json.dumps(cancelResult, indent=2))
                else: 
                    print("Not cancelling - dry run")
                placeOrder = True
            else:
                print("»» Existing order stands.")
                print("Liquidating approx USD   {0}".format(existingLiquidationAmount.quantize(p)))
                totalLiquidation    = totalLiquidation + existingLiquidationAmount
        
        # Now, place the sell order 
        if placeOrder or len(orders) == 0:
            print("Liquidating approx USD   {0}".format(potentialLiquidationAmount))
            totalLiquidation    = totalLiquidation + potentialLiquidationAmount
            jsonToPost  = prepOrder                  (product, 'sell', 'limit', stop='loss', 
                stop_price=str(targetStopUSD), price=str(targetLimitUSD), size=str(totalCryptoToSell), time_in_force='GTC') 
            
            if not reallyPlaceOrder:
                print("Dry run for order:")
            else:
                print("Really placing order:")    
            print(jsonToPost)

            if reallyPlaceOrder:
                orderResult = auth_client.place_order(product, 'sell', 'limit', stop='loss', 
                stop_price=str(targetStopUSD), price=str(targetLimitUSD), size=str(totalCryptoToSell), time_in_force='GTC')
                print("Order placed:")
                print(json.dumps(orderResult, indent=2))    
                pass

    print("=== === === === ===")
    print("Total to liquidate:")
    print("At limit  {0}".format(totalLiquidation.quantize(p)))
    print("At stop   {0}".format((totalLiquidation * (stopTriggerPercent / limitPercent)).quantize(p)))
    print("At last   {0}".format(totalLiquidationLast.quantize(p)))
    print("At high   {0}".format(totalLiquidationMax.quantize(p)))
