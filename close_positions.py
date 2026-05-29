import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import capital_com_api
sys.path.append('c:/Users/panay/Downloads/quantitative-trading-bot-master/quantitative-trading-bot-master')

from capital_com_api import CapitalComAPI

logging.basicConfig(level=logging.INFO)
load_dotenv('c:/Users/panay/Downloads/quantitative-trading-bot-master/quantitative-trading-bot-master/.env')

api = CapitalComAPI()
api.authenticate()
positions = api.get_positions()

print(f"Found {len(positions)} open positions")
for pos in positions:
    deal_id = pos['position']['dealId']
    epic = pos['market']['epic']
    print(f"Closing position {epic} (Deal ID: {deal_id})")
    try:
        api.close_position(deal_id)
        print(f"Closed {epic}")
    except Exception as e:
        print(f"Error closing {epic}: {e}")

api.logout()
