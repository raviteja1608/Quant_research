"""
Stock Price Alert Service
Monitors stock prices and sends alerts via Telegram
"""

import json
import sys
import os
import time
from datetime import datetime
import threading
import signal
from collections import OrderedDict

# Add Deployment directory to path to enable local imports
DEPLOYMENT_DIR = r'C:\Python\Investing\Deployment'
if DEPLOYMENT_DIR not in sys.path:
    sys.path.insert(0, DEPLOYMENT_DIR)

# Import custom modules from Deployment directory
from telegram_bot import send_telegram_group
print("✓ Successfully imported telegram_bot")

from ibkr_functions import IBKR_Functions
print("✓ Successfully imported ibkr_functions")



# ==================== CONFIGURATION ====================

# Stock configuration: symbol, exchange, currency
STOCK_CONFIG = [
    ('ALV', 'SMART', 'EUR'),
    ('BAC', 'SMART', 'USD'),
    ('CS', 'SBF', 'EUR'),
    ('CVX', 'SMART', 'USD'),    
    ('EUN2', 'IBIS2', 'EUR'),
    ('HEIA', 'AEB', 'EUR'),
    ('IBIT', 'SMART', 'USD'),
    ('OR', 'SBF', 'EUR'),
    ('PEP', 'SMART', 'USD'),
    ('SAN1', 'SBF', 'EUR')
]

# Option strike prices configuration
OPTIONS_CONFIG = {
    'ALV': {'call': 0, 'put': 330},
    'BAC': {'call': 0, 'put': 50},
    'CS': {'call': 0, 'put': 35.5},
    'CVX': {'call': 165, 'put': 150},
    'EUN2': {'call': 0, 'put': 56},
    'HEIA': {'call': 76, 'put': 60},
    'IBIT': {'call': 60, 'put': 40},
    'OR': {'call': 420, 'put': 0},
    'PEP': {'call': 0, 'put': 135},
    'SAN1': {'call': 0, 'put': 74}
}

# IBKR Connection settings
IBKR_HOST = '127.0.0.1'
IBKR_PORT = 7496  # 7496 for live, 7497 for paper
IBKR_CLIENT_ID = 1

# Service settings
UPDATE_INTERVAL_MINUTES = 5
RECONNECT_DELAY_SECONDS = 60
JUMP_THRESHOLD_PERCENT = 4.0  # Threshold for jump alerts


# ==================== HELPER FUNCTIONS ====================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    running = False


def format_stock_message(stocks_dict, calls_dict, puts_dict):
    """
    Format stock data dictionary into a nicely formatted Telegram message.
    
    Note: IBKR returns -1 for unavailable data (market closed, no quotes, etc.)
    This function treats -1 the same as missing data.
    """
    # Get first available timestamp
    timestamp = None
    for data in stocks_dict.values():
        if 'timestamp' in data:
            timestamp = data['timestamp']
            break
    
    # Header
    message = "📊 *Stock Price Alert*\n"
    if timestamp:
        message += f"🕐 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    else:
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Table with monospace formatting
    message += "```\n"
    message += f"{'Stock':<8} {'Bid':>8} {'Call':>8} {'Put':>8}\n"
    message += f"{'-'*8} {'-'*8} {'-'*8} {'-'*8}\n"
    
    for symbol, data in stocks_dict.items():
        # Get last price (the only field we're storing from get_stock_data_parallel)
        bid_value = data.get('last', 0)
        
        # If last price is invalid, try to get it from other possible fields
        if bid_value <= 0:
            bid_value = data.get('bid', 0)
        if bid_value <= 0:
            bid_value = data.get('close', 0)
        
        call = calls_dict.get(symbol, 0)
        put = puts_dict.get(symbol, 0)
        
        # Format call/put, showing '-' if zero
        call_str = f"{call:.0f}" if call > 0 else "-"
        put_str = f"{put:.0f}" if put > 0 else "-"
        
        message += f"{symbol:<8} {bid_value:>8.2f} {call_str:>8} {put_str:>8}\n"
    
    message += "```"
    return message


def calculate_live_jump(live_data, stock_name, threshold=5.0):
    """
    Calculate the intraday jump as percentage difference between high and low.
    
    Parameters:
    live_data (dict): Live stock data containing 'high', 'low', 'last', 'close'
    stock_name (str): Name of the stock
    threshold (float): Percentage threshold for significant jumps (default: 5.0%)
    
    Returns:
    dict: Jump information including jump percentage and threshold status
    """
    high = live_data.get('high', 0)
    low = live_data.get('low', 0)
    last = live_data.get('last', 0)
    close_prev = live_data.get('close', 0)
    
    # Handle invalid data (IBKR returns -1 for unavailable data)
    if high <= 0 or low <= 0 or last <= 0 or close_prev <= 0:
        return {
            'stock': stock_name,
            'high': high,
            'low': low,
            'last': last,
            'jump_pct': 0,
            'price_change_pct': 0,
            'threshold': threshold,
            'exceeds_threshold': False,
            'status': 'NO DATA'
        }
    
    # Calculate high-low jump percentage
    jump_pct = ((high - low) / low) * 100
    
    # Calculate current price vs previous close
    price_change_pct = ((last - close_prev) / close_prev) * 100
    
    # Check if jump exceeds threshold
    exceeds_threshold = jump_pct > threshold
    
    result = {
        'stock': stock_name,
        'high': high,
        'low': low,
        'last': last,
        'jump_pct': jump_pct,
        'price_change_pct': price_change_pct,
        'threshold': threshold,
        'exceeds_threshold': exceeds_threshold,
        'status': 'ALERT' if exceeds_threshold else 'OK'
    }
    
    return result


def format_jump_message(stocks_dict, threshold=5.0):
    """
    Format jump analysis into a Telegram message.
    
    Args:
        stocks_dict (dict): Dictionary of stock data
        threshold (float): Jump threshold percentage
    
    Returns:
        str: Formatted message for Telegram
    """
    # Get first available timestamp
    timestamp = None
    for data in stocks_dict.values():
        if 'timestamp' in data:
            timestamp = data['timestamp']
            break
    
    # Calculate jumps for all stocks
    live_jumps = []
    for stock_name, live_data in stocks_dict.items():
        jump_info = calculate_live_jump(live_data, stock_name, threshold)
        live_jumps.append(jump_info)
    
    # Header
    message = "📈 *Intraday Jump Analysis*\n"
    if timestamp:
        message += f"🕐 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
    else:
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"⚠️ Threshold: {threshold}%\n\n"
    
    # Count alerts
    alert_count = sum(1 for jump in live_jumps if jump['exceeds_threshold'])
    
    # Table with monospace formatting
    message += "```\n"
    message += f"{'Stock':<8} {'Jump%':>8} {'Δ%':>8} {'Status':<10}\n"
    message += f"{'-'*8} {'-'*8} {'-'*8} {'-'*10}\n"
    
    for jump in live_jumps:
        status_symbol = "⚠️" if jump['exceeds_threshold'] else "✓"
        message += f"{jump['stock']:<8} "
        message += f"{jump['jump_pct']:>8.2f} "
        message += f"{jump['price_change_pct']:>8.2f} "
        message += f"{status_symbol} {jump['status']:<8}\n"
    
    message += "```\n"
    
    # Summary
    if alert_count > 0:
        message += f"\n🚨 *{alert_count}* stock(s) exceed threshold!"
    else:
        message += f"\n✅ All stocks within normal range"
    
    return message


def get_stock_data_parallel(client, stock_config):
    """
    Get live data for multiple stocks in parallel using threading.
    This is MUCH faster than sequential requests.
    
    Args:
        client: Connected IBKR_Functions client
        stock_config: List of tuples (symbol, exchange, currency)
    
    Returns:
        dict: Dictionary of {symbol: market_data} in the same order as stock_config
    """
    results = {}
    threads = []
    
    def fetch_data(symbol, exchange, currency):
        """Thread worker function to fetch data for one stock"""
        try:
            data = client.get_live_data(
                symbol, 
                exchange=exchange, 
                currency=currency,
                snapshot=True,  # Snapshot mode is faster
            )
            # Use simple symbol name (remove numbers for SAN1)
            clean_symbol = symbol.replace('1', '') if symbol.startswith('SAN') else symbol
            
            # Debug logging to see what we're getting
            print(f"  {symbol} ({exchange}): last={data.get('last', 'N/A')}, high={data.get('high', 'N/A')}, low={data.get('low', 'N/A')}")
            
            # Store all relevant fields for jump analysis
            if data:
                stock_data = {}
                # Keep fields needed for both price and jump analysis
                for field in ['last', 'bid', 'close', 'high', 'low', 'timestamp']:
                    if field in data and data[field] not in [None, -1]:
                        stock_data[field] = data[field]
                
                # Ensure we have at least a price
                if 'last' not in stock_data or stock_data['last'] <= 0:
                    if 'bid' in stock_data and stock_data['bid'] > 0:
                        stock_data['last'] = stock_data['bid']
                    elif 'close' in stock_data and stock_data['close'] > 0:
                        stock_data['last'] = stock_data['close']
                
                results[clean_symbol] = stock_data
            else:
                print(f"  ⚠️  {symbol}: No valid data")
                results[clean_symbol] = {}
        except Exception as e:
            print(f"  ✗ Error fetching {symbol}: {e}")
            results[clean_symbol] = {}
    
    # Create and start threads for parallel execution
    for symbol, exchange, currency in stock_config:
        thread = threading.Thread(
            target=fetch_data,
            args=(symbol, exchange, currency)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Return results in the same order as stock_config
    ordered_results = OrderedDict()
    for symbol, exchange, currency in stock_config:
        clean_symbol = symbol.replace('1', '') if symbol.startswith('SAN') else symbol
        if clean_symbol in results:
            ordered_results[clean_symbol] = results[clean_symbol]
    
    return ordered_results


def run_price_monitor(interval_minutes=5, max_iterations=None):
    """
    Run price monitoring loop that fetches and sends stock data every N minutes.
    
    Args:
        interval_minutes (int): Minutes between each update (default: 5)
        max_iterations (int): Maximum number of iterations (None = infinite)
    """
    # Connect to IBKR once and keep connection alive
    print("=" * 60)
    print("STARTING STOCK PRICE MONITOR")
    print("=" * 60)
    
    client = IBKR_Functions(host='127.0.0.1', port=7496, client_id=2)
    
    if not client.connect():
        print("✗ Failed to connect to IBKR. Exiting.")
        return
    
    # Prepare call and put dictionaries
    calls_dict = {k: v['call'] for k, v in OPTIONS_CONFIG.items()}
    puts_dict = {k: v['put'] for k, v in OPTIONS_CONFIG.items()}
    
    # Clean up SAN1 -> SAN
    calls_dict['SAN'] = calls_dict.pop('SAN1', 0)
    puts_dict['SAN'] = puts_dict.pop('SAN1', 0)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"ITERATION {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Fetch all stock data in parallel (MUCH FASTER!)
            start_time = time.time()
            stocks_dict = get_stock_data_parallel(client, STOCK_CONFIG)
            fetch_duration = time.time() - start_time
            
            print(f"✓ Fetched {len(stocks_dict)} stocks in {fetch_duration:.2f} seconds")
            
            # Format and send FIRST message: Stock Prices
            if stocks_dict:
                formatted_message = format_stock_message(stocks_dict, calls_dict, puts_dict)
                print("\n" + formatted_message)
                
                try:
                    send_telegram_group(formatted_message)
                    print("\n✓ Message 1/2 sent to Telegram (Stock Prices)")
                except Exception as e:
                    print(f"\n✗ Failed to send price message: {e}")
                
                # Small delay between messages
                time.sleep(2)
                
                # Format and send SECOND message: Jump Analysis
                jump_message = format_jump_message(stocks_dict, JUMP_THRESHOLD_PERCENT)
                print("\n" + jump_message)
                
                try:
                    send_telegram_group(jump_message)
                    print("\n✓ Message 2/2 sent to Telegram (Jump Analysis)")
                except Exception as e:
                    print(f"\n✗ Failed to send jump message: {e}")
            else:
                print("✗ No stock data retrieved")
            
            # Check if we should stop
            if max_iterations and iteration >= max_iterations:
                print(f"\n✓ Reached maximum iterations ({max_iterations})")
                break
            
            # Wait for next interval
            wait_seconds = interval_minutes * 60
            print(f"\n⏳ Waiting {interval_minutes} minutes until next update...")
            time.sleep(wait_seconds)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
    finally:
        # Disconnect cleanly
        print("\n" + "="*60)
        client.disconnect()
        print("MONITORING ENDED")
        print("="*60)


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the service
    run_price_monitor(interval_minutes=5, max_iterations=None)
