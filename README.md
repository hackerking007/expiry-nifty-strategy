# Nifty Options Expiry Bot

## Strategy
- Waits until 9:30 AM.
- Reads the 9:15–9:30 Nifty 50 candle.
- If breakout above high → sell ATM PE + buy hedge PE.
- If breakdown below low → sell ATM CE + buy hedge CE.
- Hedge selection is simplified; delta-based selection to be integrated later.# expiry-nifty-strategy
