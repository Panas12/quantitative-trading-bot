"""
Minimal Live Trading Example for Capital.com

This script demonstrates placing a MINIMAL size trade on your LIVE account.
Uses the smallest position size possible (0.01 lots) for safe testing.

⚠️ WARNING: This uses REAL MONEY on your LIVE account!
Only run this if you're ready to test with real funds.
"""

from capital_com_api import CapitalComAPI, CapitalComAPIError
import time


def main():
    """Place a minimal test trade on GOLD"""
    
    print("="*70)
    print("  MINIMAL LIVE TRADE TEST - Capital.com")
    print("="*70)
    print("\n⚠️  WARNING: This will place a REAL trade with REAL money!")
    print("  Position size: 0.01 lots (MINIMUM SIZE)")
    print("  Instrument: GOLD")
    print("\n" + "="*70)
    
    # User confirmation
    confirm = input("\nType 'YES' to proceed with live trade: ")
    if confirm != 'YES':
        print("Cancelled. No trade placed.")
        return
    
    api = None
    position_id = None
    
    try:
        # Initialize and authenticate
        print("\n[1/6] Authenticating with Capital.com LIVE account...")
        api = CapitalComAPI()
        api.authenticate()
        print("      ✓ Connected")
        
        # Get balance
        print("\n[2/6] Checking account balance...")
        balance = api.get_account_balance()
        print(f"      Balance: ${balance['balance']:.2f}")
        print(f"      Available: ${balance['available']:.2f}")
        
        if balance['available'] < 10:
            print("\n✗ ERROR: Insufficient funds (need at least $10)")
            return
        
        # Get current market price
        print("\n[3/6] Fetching current GOLD price...")
        market = api.get_market_details('GOLD')
        snapshot = market.get('snapshot', {})
        current_price = float(snapshot.get('bid', 0))
        
        if current_price == 0:
            print("✗ ERROR: Could not get current price. Market may be closed.")
            return
        
        print(f"      Current GOLD price: ${current_price:.2f}")
        
        # Calculate stop loss and take profit
        # Using very tight stops for minimal risk
        stop_loss = current_price - 2  # $2 stop loss
        take_profit = current_price + 5  # $5 take profit
        
        print("\n[4/6] Placing BUY order...")
        print(f"      Size: 0.01 lots (MINIMUM)")
        print(f"      Entry: ~${current_price:.2f}")
        print(f"      Stop Loss: ${stop_loss:.2f} (risk: $2)")
        print(f"      Take Profit: ${take_profit:.2f} (potential: $5)")
        
        # Place the order
        result = api.create_position(
            epic='GOLD',
            direction='BUY',
            size=0.01,  # MINIMUM SIZE
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        deal_ref = result.get('dealReference')
        print(f"\n      ✓ Order placed! Deal Reference: {deal_ref}")
        
        # Wait for order to process
        print("\n[5/6] Waiting for order processing...")
        time.sleep(3)
        
        # Check position
        positions = api.get_positions()
        
        if positions:
            for pos in positions:
                if deal_ref in pos['position'].get('dealReference', ''):
                    position_id = pos['position']['dealId']
                    pos_data = pos['position']
                    
                    print(f"\n      ✓ Position OPEN")
                    print(f"      Deal ID: {position_id}")
                    print(f"      Size: {pos_data['size']}")
                    print(f"      Current P&L: ${pos_data.get('profit', 0):.2f}")
                    break
        
        # Ask user if they want to close immediately
        print("\n[6/6] Position Management")
        close_now = input("\n      Close position immediately? (y/n): ")
        
        if close_now.lower() == 'y' and position_id:
            print("\n      Closing position...")
            api.close_position(position_id)
            print("      ✓ Position closed")
            
            # Get final balance
            time.sleep(2)
            final_balance = api.get_account_balance()
            pnl = final_balance['balance'] - balance['balance']
            
            print(f"\n      Final Balance: ${final_balance['balance']:.2f}")
            print(f"      Trade P&L: ${pnl:.2f}")
        else:
            print("\n      Position left OPEN - manage it manually in Capital.com")
        
        print("\n" + "="*70)
        print("  ✓ TEST COMPLETED")
        print("="*70)
        
    except CapitalComAPIError as e:
        print(f"\n✗ API Error: {e}")
        
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if api:
            print("\nLogging out...")
            api.logout()


if __name__ == '__main__':
    main()
