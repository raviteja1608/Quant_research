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

# Add current directory to path to enable local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import custom modules - using the actual filenames from your directory
try:
    from telegram_bot import send_telegram_group
except ImportError:
    try:
        # Fallback: try importing from the notebook exports if .py doesn't exist
        import nbformat
        from nbconvert import PythonExporter
        # This is more complex - better to just have the .py files
        print("✗ Error: Could not import telegram_bot.py")
        print("  Please ensure telegram_bot.py exists")
        sys.exit(1)
    except:
        print("✗ Error: Could not import telegram_bot")
        print("  Make sure telegram_bot.py exists in:", os.path.dirname(os.path.abspath(__file__)))
        sys.exit(1)

try:
    from ibkr_functions import IBKR_Functions
except ImportError:
    print("✗ Error: Could not import ibkr_functions.py")
    print("  Make sure ibkr_functions.py exists in:", os.path.dirname(os.path.abspath(__file__)))
    sys.exit(1)


# ==================== CONFIGURATION ====================

# Stock configuration: symbol, exchange, currency
STOCK_CONFIG = [
    ('BAC', 'SMART', 'USD'),
    ('BNP', 'SBF', 'EUR'),
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
    'BAC': {'call': 0, 'put': 51},
    'BNP': {'call': 85, 'put': 72},
    'CVX': {'call': 165, 'put': 145},
    'EUN2': {'call': 0, 'put': 56},
    'HEIA': {'call': 74, 'put': 0},
    'IBIT': {'call': 60, 'put': 41},
    'OR': {'call': 400, 'put': 0},
    'PEP': {'call': 0, 'put': 135},
    'SAN1': {'call': 87, 'put': 0}
}

# IBKR Connection settings
IBKR_HOST = '127.0.0.1'
IBKR_PORT = 7496  # 7496 for live, 7497 for paper
IBKR_CLIENT_ID = 1

# Service settings
UPDATE_INTERVAL_MINUTES = 5
RECONNECT_DELAY_SECONDS = 60


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
            print(f"  {symbol} ({exchange}): {data}")
            
            # Only keep 'last' field from the data
            if data and 'last' in data and data['last'] > 0:
                results[clean_symbol] = {'last': data['last']}
            elif data and 'bid' in data and data['bid'] > 0:
                # Fallback to bid if last is not available
                results[clean_symbol] = {'last': data['bid']}
            elif data and 'close' in data and data['close'] > 0:
                # Fallback to close if neither last nor bid available
                results[clean_symbol] = {'last': data['close']}
            else:
                print(f"  ⚠️  {symbol}: No valid price data (might need market data subscription)")
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
            
            # Format and send message
            if stocks_dict:
                formatted_message = format_stock_message(stocks_dict, calls_dict, puts_dict)
                print("\n" + formatted_message)
                
                try:
                    send_telegram_group(formatted_message)
                    print("\n✓ Message sent to Telegram")
                except Exception as e:
                    print(f"\n✗ Failed to send Telegram message: {e}")
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
