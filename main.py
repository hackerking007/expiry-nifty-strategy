import datetime
import time
from kite_login import get_kite_instance

# Add known NSE holidays (shift expiry to Wednesday if Thursday is off)
nse_holidays = {
    "2025-07-17",  # Example Thursday holiday
}

def get_weekly_expiry():
    today = datetime.date.today()
    thursday = today + datetime.timedelta((3 - today.weekday()) % 7)
    if thursday.strftime("%Y-%m-%d") in nse_holidays:
        expiry = thursday - datetime.timedelta(days=1)
    else:
        expiry = thursday
    return expiry.strftime("%d%b%Y").upper()

kite = get_kite_instance()
lot_size = 50
expiry = get_weekly_expiry()
monitor_interval = 30

def wait_for_930():
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 30:
            return
        time.sleep(1)

def get_30min_candle():
    instrument_token = kite.ltp("NSE:NIFTY 50")["NSE:NIFTY 50"]["instrument_token"]
    today = datetime.date.today()
    candles = kite.historical_data(instrument_token, today, today + datetime.timedelta(days=1), "15minute")
    return candles[1]

def get_strike(price):
    return int(round(price / 50.0) * 50)

def fetch_option_symbol(strike, option_type):
    return f"NFO:NIFTY{expiry}{strike}{option_type}"

def place_order(tradingsymbol, quantity, transaction_type):
    order_id = kite.place_order(
        tradingsymbol=tradingsymbol,
        exchange="NFO",
        transaction_type=transaction_type,
        quantity=quantity,
        order_type="MARKET",
        product="MIS",
        variety="regular"
    )
    print(f"{transaction_type} order placed for {tradingsymbol}. Order ID: {order_id}")
    return order_id

def monitor_exit(sell_symbol, hedge_symbol, entry_price):
    stop_loss = entry_price + (entry_price / 2)
    print(f"🟡 Monitoring SL ₹{stop_loss:.2f}, Target ₹3 for {sell_symbol}")

    while True:
        ltp = kite.ltp(sell_symbol)[sell_symbol]["last_price"]
        now = datetime.datetime.now()

        if ltp >= stop_loss:
            print(f"🔴 SL hit at ₹{ltp:.2f}")
            break
        elif ltp <= 3:
            print(f"✅ Target hit at ₹{ltp:.2f}")
            break
        elif now.hour == 15 and now.minute == 25:
            if abs(ltp - entry_price) <= 1:
                print(f"⚪ Breakeven exit at ₹{ltp:.2f}")
                break
            else:
                print(f"🟢 Holding till expiry. LTP: ₹{ltp:.2f}")
                return

        time.sleep(monitor_interval)

    # Exit both legs
    place_order(sell_symbol, lot_size, "BUY")
    place_order(hedge_symbol, lot_size, "SELL")
    print("💼 Trade exited")

def detect_existing_trade():
    positions = kite.positions()["net"]
    for pos in positions:
        if pos["product"] == "MIS" and pos["quantity"] == -lot_size and "NIFTY" in pos["tradingsymbol"]:
            print(f"🟢 Existing trade found: {pos['tradingsymbol']}")
            sell_symbol = f"NFO:{pos['tradingsymbol']}"
            entry_price = kite.ltp(sell_symbol)[sell_symbol]["last_price"]
            # Detect hedge leg
            hedge_symbol = find_hedge_symbol(pos["tradingsymbol"])
            return sell_symbol, hedge_symbol, entry_price
    return None, None, None

def find_hedge_symbol(sell_tradingsymbol):
    if "PE" in sell_tradingsymbol:
        strike = int(sell_tradingsymbol[11:16])
        hedge_strike = strike - 300
        return fetch_option_symbol(hedge_strike, "PE")
    elif "CE" in sell_tradingsymbol:
        strike = int(sell_tradingsymbol[11:16])
        hedge_strike = strike + 300
        return fetch_option_symbol(hedge_strike, "CE")
    return None

def run_strategy():
    today = datetime.datetime.today()
    if today.weekday() != 3:
        print("❌ Not expiry day (Thursday). Exiting.")
        return

    # STEP 1: Check if trade already active
    sell_symbol, hedge_symbol, entry_price = detect_existing_trade()
    if sell_symbol:
        print("🔄 Resuming monitoring of existing position...")
        monitor_exit(sell_symbol, hedge_symbol, entry_price)
        return

    # STEP 2: Fresh entry
    wait_for_930()
    candle = get_30min_candle()
    high, low = candle["high"], candle["low"]
    spot_price = kite.ltp("NSE:NIFTY 50")["NSE:NIFTY 50"]["last_price"]
    atm_strike = get_strike(spot_price)

    if spot_price > high:
        sell_symbol = fetch_option_symbol(atm_strike, "PE")
        hedge_symbol = fetch_option_symbol(atm_strike - 300, "PE")
    elif spot_price < low:
        sell_symbol = fetch_option_symbol(atm_strike, "CE")
        hedge_symbol = fetch_option_symbol(atm_strike + 300, "CE")
    else:
        print("🔸 No breakout. No trade today.")
        return

    # Place entry orders
    place_order(sell_symbol, lot_size, "SELL")
    place_order(hedge_symbol, lot_size, "BUY")
    time.sleep(5)
    entry_price = kite.ltp(sell_symbol)[sell_symbol]["last_price"]
    print(f"🚀 Trade placed. Entry price: ₹{entry_price:.2f}")
    monitor_exit(sell_symbol, hedge_symbol, entry_price)

if __name__ == "__main__":
    run_strategy()
