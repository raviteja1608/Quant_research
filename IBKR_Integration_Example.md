# IBKR API Integration Example

This example demonstrates how to integrate the IBKR API with the existing backtesting engine in the Quant_research repository.

## Overview

This example shows how to:
1. Use IBKR API to fetch real-time market data
2. Run backtesting analysis using the existing engine
3. Execute live trades based on backtesting signals
4. Monitor portfolio performance in real-time

## Prerequisites

1. **Interactive Brokers Account**
   - Active IBKR account with API access enabled
   - TWS or IB Gateway installed and configured

2. **Python Environment**
   ```bash
   pip install ib_insync pandas numpy matplotlib
   ```

3. **TWS/Gateway Configuration**
   - Enable API connections
   - Set correct port (7497 for paper trading)
   - Add trusted IP addresses

## Example 1: Basic Market Data Integration

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from IBKR_Functions import IBKR_Functions, IBKRConfig, create_stock_contract

# Configure IBKR connection (paper trading)
config = IBKRConfig(port=7497)

# Portfolio of stocks to monitor
portfolio_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

def fetch_live_market_data(symbols, duration='1 M'):
    """Fetch live market data for analysis"""
    market_data = {}
    
    with IBKR_Functions(config) as ibkr:
        if not ibkr.connect():
            print("Failed to connect to IBKR")
            return {}
        
        for symbol in symbols:
            try:
                # Create contract
                contract = create_stock_contract(symbol)
                
                # Get historical data
                hist_data = ibkr.get_historical_data(contract, duration, '1 day')
                
                # Get current market data
                current_data = ibkr.get_market_data(contract)
                
                if not hist_data.empty and current_data:
                    # Convert to EODHD format for compatibility
                    from IBKR_Functions import ibkr_to_eodhd_format
                    eodhd_data = ibkr_to_eodhd_format(hist_data)
                    
                    market_data[symbol] = {
                        'historical': eodhd_data,
                        'current': current_data
                    }
                    
                    print(f"✓ {symbol}: {len(eodhd_data)} historical records, current price: ${current_data.last:.2f}")
                
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
    
    return market_data

# Usage
live_data = fetch_live_market_data(portfolio_symbols)
```

## Example 2: Backtesting Signal Generation

```python
def generate_trading_signals(market_data):
    """Generate trading signals using moving average crossover strategy"""
    signals = []
    
    for symbol, data in market_data.items():
        hist_data = data['historical']
        current_price = data['current'].last
        
        if len(hist_data) >= 20:  # Need enough data for analysis
            # Calculate moving averages
            hist_data['ma_5'] = hist_data['close'].rolling(5).mean()
            hist_data['ma_20'] = hist_data['close'].rolling(20).mean()
            
            # Get recent values
            ma_5_current = hist_data['ma_5'].iloc[-1]
            ma_20_current = hist_data['ma_20'].iloc[-1]
            ma_5_prev = hist_data['ma_5'].iloc[-2]
            ma_20_prev = hist_data['ma_20'].iloc[-2]
            
            # Generate signals
            if ma_5_prev <= ma_20_prev and ma_5_current > ma_20_current:
                # Golden cross - bullish signal
                signals.append({
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': 100,
                    'price': current_price,
                    'signal_type': 'GOLDEN_CROSS',
                    'confidence': 0.8
                })
            elif ma_5_prev >= ma_20_prev and ma_5_current < ma_20_current:
                # Death cross - bearish signal
                signals.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': 100,
                    'price': current_price,
                    'signal_type': 'DEATH_CROSS',
                    'confidence': 0.8
                })
    
    return signals

# Usage
signals = generate_trading_signals(live_data)
for signal in signals:
    print(f"Signal: {signal['action']} {signal['quantity']} {signal['symbol']} at ${signal['price']:.2f}")
```

## Example 3: Live Trade Execution

```python
def execute_trading_signals(signals):
    """Execute trading signals via IBKR API"""
    from IBKR_Functions import create_live_trading_bridge
    
    executed_orders = []
    
    with IBKR_Functions(config) as ibkr:
        if not ibkr.connect():
            print("Failed to connect to IBKR")
            return []
        
        # Create trading bridge
        trading_bridge = create_live_trading_bridge(ibkr)
        
        for signal in signals:
            try:
                # Execute signal with limit order (small buffer from current price)
                if signal['action'] == 'BUY':
                    limit_price = signal['price'] * 1.001  # Buy slightly above current
                else:
                    limit_price = signal['price'] * 0.999  # Sell slightly below current
                
                order_id = trading_bridge(
                    signal['symbol'],
                    signal['action'],
                    signal['quantity'],
                    limit_price
                )
                
                if order_id:
                    executed_orders.append({
                        'order_id': order_id,
                        'symbol': signal['symbol'],
                        'action': signal['action'],
                        'quantity': signal['quantity'],
                        'price': limit_price,
                        'timestamp': datetime.now()
                    })
                    
                    print(f"✓ Order executed: {signal['action']} {signal['quantity']} {signal['symbol']} at ${limit_price:.2f} (Order ID: {order_id})")
                else:
                    print(f"✗ Failed to execute: {signal['action']} {signal['quantity']} {signal['symbol']}")
                    
            except Exception as e:
                print(f"Error executing signal for {signal['symbol']}: {e}")
    
    return executed_orders

# Usage
executed_orders = execute_trading_signals(signals)
```

## Example 4: Portfolio Monitoring

```python
def monitor_portfolio_performance():
    """Monitor portfolio performance in real-time"""
    from IBKR_Functions import real_time_portfolio_monitor
    
    with IBKR_Functions(config) as ibkr:
        if not ibkr.connect():
            print("Failed to connect to IBKR")
            return
        
        # Get initial portfolio snapshot
        positions = ibkr.get_portfolio_positions()
        account_summary = ibkr.get_account_summary()
        
        if not positions.empty:
            print("Current Portfolio Positions:")
            print(positions[['symbol', 'position', 'market_value', 'unrealized_pnl']])
            
            total_value = positions['market_value'].sum()
            total_pnl = positions['unrealized_pnl'].sum()
            
            print(f"\nPortfolio Summary:")
            print(f"Total Value: ${total_value:,.2f}")
            print(f"Total P&L: ${total_pnl:,.2f}")
        
        # Get account summary
        if not account_summary.empty:
            key_metrics = account_summary[account_summary['tag'].isin([
                'NetLiquidation', 'TotalCashValue', 'UnrealizedPnL', 'RealizedPnL'
            ])]
            print(f"\nAccount Summary:")
            for _, row in key_metrics.iterrows():
                print(f"{row['tag']}: ${float(row['value']):,.2f}")
        
        # Start real-time monitoring
        print(f"\nStarting real-time monitoring...")
        monitor_thread = real_time_portfolio_monitor(ibkr, update_interval=60)
        
        # Keep monitoring for 10 minutes
        import time
        time.sleep(600)
        
        print("Monitoring stopped.")

# Usage
monitor_portfolio_performance()
```

## Example 5: Complete Trading Strategy

```python
def complete_trading_strategy():
    """Complete automated trading strategy"""
    
    print("=== Automated Trading Strategy ===")
    print("1. Fetching live market data...")
    
    # Step 1: Fetch market data
    market_data = fetch_live_market_data(portfolio_symbols)
    
    if not market_data:
        print("No market data available. Exiting.")
        return
    
    print(f"✓ Market data fetched for {len(market_data)} symbols")
    
    # Step 2: Generate signals
    print("\n2. Generating trading signals...")
    signals = generate_trading_signals(market_data)
    
    if not signals:
        print("No trading signals generated.")
    else:
        print(f"✓ Generated {len(signals)} trading signals")
        for signal in signals:
            print(f"  - {signal['action']} {signal['quantity']} {signal['symbol']} ({signal['signal_type']})")
    
    # Step 3: Execute trades
    print("\n3. Executing trades...")
    executed_orders = execute_trading_signals(signals)
    
    if executed_orders:
        print(f"✓ Executed {len(executed_orders)} orders")
    else:
        print("No orders executed")
    
    # Step 4: Monitor portfolio
    print("\n4. Monitoring portfolio...")
    monitor_portfolio_performance()
    
    print("\n=== Strategy Complete ===")

# Run the complete strategy
if __name__ == "__main__":
    complete_trading_strategy()
```

## Example 6: Risk Management Integration

```python
def enhanced_risk_management():
    """Enhanced risk management with position sizing and stop losses"""
    
    def calculate_position_size(symbol, price, risk_per_trade=0.02):
        """Calculate position size based on risk management rules"""
        # Get account value
        with IBKR_Functions(config) as ibkr:
            if ibkr.connect():
                account_summary = ibkr.get_account_summary()
                net_liq = account_summary[account_summary['tag'] == 'NetLiquidation']['value'].iloc[0]
                account_value = float(net_liq)
                
                # Calculate position size (2% risk per trade)
                risk_amount = account_value * risk_per_trade
                position_size = int(risk_amount / (price * 0.02))  # 2% stop loss
                
                return min(position_size, 1000)  # Max 1000 shares
        
        return 100  # Default position size
    
    def set_stop_losses(executed_orders):
        """Set stop loss orders for executed trades"""
        with IBKR_Functions(config) as ibkr:
            if not ibkr.connect():
                return
            
            for order in executed_orders:
                if order['action'] == 'BUY':
                    # Set stop loss at 2% below entry price
                    stop_price = order['price'] * 0.98
                    
                    from IBKR_Functions import create_stop_order, create_stock_contract
                    
                    contract = create_stock_contract(order['symbol'])
                    stop_order = create_stop_order('SELL', order['quantity'], stop_price)
                    
                    stop_order_id = ibkr.place_order(contract, stop_order)
                    
                    if stop_order_id:
                        print(f"✓ Stop loss set for {order['symbol']}: {stop_price:.2f}")
    
    # Usage in trading strategy
    def risk_managed_trading_strategy():
        # Fetch data and generate signals
        market_data = fetch_live_market_data(portfolio_symbols)
        signals = generate_trading_signals(market_data)
        
        # Adjust position sizes based on risk management
        for signal in signals:
            original_quantity = signal['quantity']
            risk_adjusted_quantity = calculate_position_size(signal['symbol'], signal['price'])
            signal['quantity'] = risk_adjusted_quantity
            
            print(f"Position size adjusted for {signal['symbol']}: {original_quantity} → {risk_adjusted_quantity}")
        
        # Execute trades
        executed_orders = execute_trading_signals(signals)
        
        # Set stop losses
        set_stop_losses(executed_orders)
        
        return executed_orders
    
    return risk_managed_trading_strategy()

# Usage
enhanced_orders = enhanced_risk_management()
```

## Configuration Tips

### 1. Paper Trading Setup
```python
# Always start with paper trading
config = IBKRConfig(
    host='127.0.0.1',
    port=7497,  # Paper trading port
    client_id=1,
    timeout=30
)
```

### 2. Live Trading Setup (Use with caution)
```python
# Only after thorough testing
config = IBKRConfig(
    host='127.0.0.1',
    port=7496,  # Live trading port
    client_id=1,
    timeout=30
)
```

### 3. Error Handling
```python
def safe_trading_execution():
    """Safe trading execution with comprehensive error handling"""
    try:
        with IBKR_Functions(config) as ibkr:
            if not ibkr.connect():
                raise ConnectionError("Failed to connect to IBKR")
            
            # Your trading logic here
            
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Log error, send alert, etc.
```

## Best Practices

1. **Always Test in Paper Trading First**
2. **Implement Proper Risk Management**
3. **Use Appropriate Position Sizing**
4. **Set Stop Losses**
5. **Monitor Performance Regularly**
6. **Keep Logs of All Activities**
7. **Have Emergency Stop Procedures**

## Disclaimer

This example is for educational purposes only. Trading involves significant risk of loss. Always:
- Test thoroughly in paper trading
- Use appropriate risk management
- Consult with financial advisors
- Follow all regulatory requirements
- Never risk more than you can afford to lose