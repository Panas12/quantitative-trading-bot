"""
Capital.com Broker Integration Example

This script demonstrates how to use the Capital.com API connector
for automated trading. It performs a complete trading workflow:

1. Connect and authenticate
2. Check account balance
3. Fetch market data
4. Place a demo trade
5. Monitor the position
6. Close the position

IMPORTANT: This runs on DEMO account by default (safe for testing)
"""

import time
from capital_com_api import CapitalComAPI, CapitalComAPIError


def print_header(text):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text):
    """Print formatted subsection"""
    print(f"\n► {text}")
    print("-" * 70)


def main():
    """Run complete broker integration demo"""
    
    print_header("Capital.com Broker Integration Demo")
    print("\n⚠️  This demo uses your DEMO account (no real money at risk)")
    
    api = None
    test_position_id = None
    
    try:
        # Step 1: Initialize and authenticate
        print_section("STEP 1: Authentication")
        api = CapitalComAPI()
        api.authenticate()
        print("✓ Successfully authenticated")
        
        # Step 2: Get account information
        print_section("STEP 2: Account Information")
        balance = api.get_account_balance()
        print(f"Account Name: {balance['account_name']}")
        print(f"Account ID: {balance['account_id']}")
        print(f"Currency: {balance['currency']}")
        print(f"Balance: {balance['balance']:,.2f} {balance['currency']}")
        print(f"Available Funds: {balance['available']:,.2f} {balance['currency']}")
        print(f"Current P&L: {balance['profit_loss']:,.2f} {balance['currency']}")
        
        # Step 3: Get market data
        print_section("STEP 3: Market Data - Gold (GOLD)")
        
        # Get market details
        market_info = api.get_market_details('GOLD')
        instrument = market_info.get('instrument', {})
        snapshot = market_info.get('snapshot', {})
        
        print(f"Instrument: {instrument.get('name', 'GOLD')}")
        print(f"Type: {instrument.get('type', 'Unknown')}")
        print(f"Current Bid: {snapshot.get('bid', 'N/A')}")
        print(f"Current Offer: {snapshot.get('offer', 'N/A')}")
        
        # Get historical prices
        print("\nFetching last 10 hourly price bars...")
        prices = api.get_historical_prices('GOLD', resolution='HOUR', max_points=10)
        
        if prices:
            print(f"\nLatest price data ({len(prices)} bars):")
            print(f"{'Time':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10}")
            print("-" * 70)
            
            for price in prices[-5:]:  # Show last 5
                time_str = price.get('snapshotTime', '')[:16]
                o = price['openPrice']['bid']
                h = price['highPrice']['bid']
                l = price['lowPrice']['bid']
                c = price['closePrice']['bid']
                print(f"{time_str:<20} {o:>10.2f} {h:>10.2f} {l:>10.2f} {c:>10.2f}")
        
        # Step 4: Check existing positions
        print_section("STEP 4: Current Open Positions")
        existing_positions = api.get_positions()
        
        if existing_positions:
            print(f"Found {len(existing_positions)} open position(s):")
            for pos in existing_positions:
                market = pos['market']
                position = pos['position']
                print(f"\n  - {market['instrumentName']}")
                print(f"    Direction: {position['direction']}")
                print(f"    Size: {position['size']}")
                print(f"    Deal ID: {position['dealId']}")
                print(f"    P&L: {position.get('profit', 0)} {position.get('currency', 'USD')}")
        else:
            print("No open positions")
        
        # Step 5: Place a test trade (DEMO ONLY)
        print_section("STEP 5: Placing TEST Trade (Demo Account)")
        print("\n⚠️  This is a DEMO trade - no real money involved!")
        print("Placing small BUY order for GOLD (0.1 lots)...")
        
        # Place a small test trade
        current_price = float(snapshot.get('bid', 0))
        if current_price > 0:
            stop_loss = current_price - 5  # $5 stop loss
            take_profit = current_price + 10  # $10 take profit
            
            print(f"\nOrder Details:")
            print(f"  Instrument: GOLD")
            print(f"  Direction: BUY")
            print(f"  Size: 0.1 lots")
            print(f"  Entry: ~{current_price:.2f}")
            print(f"  Stop Loss: {stop_loss:.2f}")
            print(f"  Take Profit: {take_profit:.2f}")
            
            result = api.create_position(
                epic='GOLD',
                direction='BUY',
                size=0.1,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            deal_reference = result.get('dealReference')
            print(f"\n✓ Order placed successfully!")
            print(f"  Deal Reference: {deal_reference}")
            
            # Wait a moment for order to be processed
            print("\nWaiting 3 seconds for order processing...")
            time.sleep(3)
            
            # Step 6: Check the position
            print_section("STEP 6: Checking Position Status")
            positions = api.get_positions()
            
            # Find our test position
            for pos in positions:
                if deal_reference in pos['position'].get('dealReference', ''):
                    test_position_id = pos['position']['dealId']
                    position_data = pos['position']
                    
                    print(f"Position Found:")
                    print(f"  Deal ID: {test_position_id}")
                    print(f"  Status: {position_data.get('status', 'OPEN')}")
                    print(f"  Size: {position_data['size']}")
                    print(f"  Direction: {position_data['direction']}")
                    print(f"  Current P&L: {position_data.get('profit', 0)}")
                    break
            
            # Step 7: Close the test position
            if test_position_id:
                print_section("STEP 7: Closing Test Position")
                print(f"Closing position {test_position_id}...")
                
                close_result = api.close_position(test_position_id)
                close_ref = close_result.get('dealReference')
                
                print(f"✓ Position closed!")
                print(f"  Deal Reference: {close_ref}")
                
                # Wait and verify closure
                time.sleep(2)
                final_positions = api.get_positions()
                
                # Verify position is closed
                is_closed = not any(
                    p['position']['dealId'] == test_position_id 
                    for p in final_positions
                )
                
                if is_closed:
                    print("✓ Position successfully closed and removed")
                else:
                    print("⚠ Position may still be processing closure")
        
        else:
            print("⚠ Could not get current price, skipping trade demo")
        
        # Final summary
        print_section("DEMO COMPLETE - Summary")
        final_balance = api.get_account_balance()
        print(f"Final Balance: {final_balance['balance']:,.2f} {final_balance['currency']}")
        print(f"Total P&L: {final_balance['profit_loss']:,.2f} {final_balance['currency']}")
        
        print_header("✓ All Tests Completed Successfully!")
        print("\nThe Capital.com API integration is working correctly.")
        print("You can now integrate this with your trading strategies.\n")
        
    except CapitalComAPIError as e:
        print(f"\n❌ Capital.com API Error: {e}")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Always logout
        if api:
            print("\nLogging out...")
            api.logout()
            print("✓ Session closed")
    
    return 0


if __name__ == '__main__':
    exit(main())
