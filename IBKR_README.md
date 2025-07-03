# Interactive Brokers API Implementation

This repository now includes comprehensive Interactive Brokers (IBKR) API functionality for Python, designed to work alongside the existing EODHD API functions.

## Overview

The IBKR implementation provides:
- ✅ Connection management to TWS/Gateway
- ✅ Real-time and historical market data
- ✅ Order placement and management
- ✅ Portfolio and account information
- ✅ Contract search and details
- ✅ Integration with existing backtesting engine
- ✅ Risk management tools
- ✅ Comprehensive examples and documentation

## Quick Start

### 1. Prerequisites

#### Software Requirements
- Interactive Brokers TWS (Trader Workstation) or IB Gateway
- Python 3.7+
- Valid Interactive Brokers account

#### Python Dependencies
```bash
pip install ibapi pandas numpy
```

### 2. Setup Interactive Brokers

1. **Download and Install**
   - TWS: [Download TWS](https://www.interactivebrokers.com/en/index.php?f=14099)
   - IB Gateway: [Download Gateway](https://www.interactivebrokers.com/en/index.php?f=16457)

2. **Configure API Access**
   - Launch TWS/Gateway
   - Go to File → Global Configuration → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Set Socket port:
     - Paper Trading: 7497 (TWS) or 4002 (Gateway)
     - Live Trading: 7496 (TWS) or 4001 (Gateway)
   - Add trusted IP: 127.0.0.1 (for local connections)

3. **Account Setup**
   - Enable API access in your IBKR account settings
   - Set up paper trading account for testing

### 3. Basic Usage

```python
from IBKR_Functions import IBKR_Functions, IBKRConfig, create_stock_contract, create_limit_order

# Configure connection (paper trading)
config = IBKRConfig(port=7497)  # Paper trading port

# Create IBKR instance and connect
with IBKR_Functions(config) as ibkr:
    if ibkr.connect():
        # Get market data
        contract = create_stock_contract('AAPL')
        market_data = ibkr.get_market_data(contract)
        print(f"AAPL Last Price: {market_data.last}")
        
        # Get historical data
        historical_data = ibkr.get_historical_data(contract, '1 M', '1 day')
        print(historical_data.tail())
        
        # Place an order
        order = create_limit_order('BUY', 100, 150.00)
        order_id = ibkr.place_order(contract, order)
        print(f"Order placed: {order_id}")
```

## Key Features

### 1. Connection Management
- Automatic connection handling
- Context manager support
- Connection status monitoring
- Error handling and reconnection

### 2. Market Data
- Real-time quotes (bid/ask/last)
- Historical data (various timeframes)
- Multiple data types (live, delayed, frozen)
- Market data subscriptions

### 3. Order Management
- Multiple order types (Market, Limit, Stop, Stop-Limit)
- Order status tracking
- Order modification and cancellation
- Execution reporting

### 4. Portfolio Management
- Real-time position monitoring
- Account summary information
- P&L tracking
- Risk metrics

### 5. Contract Search
- Symbol search functionality
- Contract details retrieval
- Multi-asset support (stocks, options, futures)
- Exchange information

## Advanced Usage

### Portfolio Monitoring
```python
# Real-time portfolio monitoring
config = IBKRConfig(port=7497)
with IBKR_Functions(config) as ibkr:
    if ibkr.connect():
        # Get current positions
        positions = ibkr.get_portfolio_positions()
        print(positions)
        
        # Get account summary
        account = ibkr.get_account_summary()
        print(account)
        
        # Start real-time monitoring
        monitor_thread = real_time_portfolio_monitor(ibkr, 60)
```

### Integration with Backtesting
```python
# Bridge backtesting signals to live trading
def execute_backtest_signals(signals):
    config = IBKRConfig(port=7497)
    with IBKR_Functions(config) as ibkr:
        if ibkr.connect():
            trading_bridge = create_live_trading_bridge(ibkr)
            
            for signal in signals:
                order_id = trading_bridge(
                    signal['symbol'], 
                    signal['action'], 
                    signal['quantity']
                )
                print(f"Signal executed: {signal} -> Order ID: {order_id}")
```

### Options Trading
```python
# Create option contract
option_contract = create_option_contract(
    symbol='AAPL',
    expiry='20241220',
    strike=150.0,
    right='C'  # Call option
)

# Get option market data
option_data = ibkr.get_market_data(option_contract)
print(f"Option Price: {option_data.last}")
```

## Configuration Options

### Connection Settings
```python
config = IBKRConfig(
    host='127.0.0.1',          # TWS/Gateway host
    port=7497,                 # TWS/Gateway port
    client_id=1,               # Unique client ID
    timeout=30,                # Connection timeout
    readonly=False             # Read-only mode
)
```

### Ports Reference
- **TWS Paper Trading**: 7497
- **TWS Live Trading**: 7496
- **Gateway Paper Trading**: 4002
- **Gateway Live Trading**: 4001

## Error Handling

The implementation includes comprehensive error handling:

```python
try:
    config = IBKRConfig(port=7497)
    with IBKR_Functions(config) as ibkr:
        if not ibkr.connect():
            print("Failed to connect to IBKR")
            return
        
        # Your trading logic here
        
except Exception as e:
    print(f"Error: {str(e)}")
    # Handle error appropriately
```

## Best Practices

### 1. Testing
- Always start with paper trading
- Test all functionality before live trading
- Use small position sizes initially
- Monitor performance and logs

### 2. Risk Management
- Implement position sizing rules
- Set stop-loss orders
- Monitor portfolio exposure
- Use appropriate order types

### 3. Performance
- Limit API call frequency
- Use efficient data structures
- Implement proper logging
- Monitor system resources

### 4. Security
- Secure API credentials
- Use IP whitelisting
- Implement authentication
- Regular security audits

## Integration with Existing Code

This IBKR implementation is designed to work seamlessly with the existing EODHD functions:

1. **Data Compatibility**: Use `ibkr_to_eodhd_format()` to convert data formats
2. **Backtesting Integration**: Bridge backtesting results to live trading
3. **Portfolio Management**: Real-time monitoring of live positions
4. **Risk Management**: Integration with existing risk models

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check TWS/Gateway is running
   - Verify API settings are enabled
   - Ensure correct port numbers
   - Check firewall settings

2. **Market Data Issues**
   - Verify market data subscriptions
   - Check market hours
   - Use appropriate data types
   - Handle delayed data permissions

3. **Order Rejections**
   - Check account permissions
   - Verify contract details
   - Ensure sufficient buying power
   - Review order parameters

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will provide detailed logging of all API interactions
```

## Examples

The `IBKR_Functions.ipynb` notebook includes comprehensive examples:

1. **Basic Connection and Market Data**
2. **Order Management**
3. **Contract Search**
4. **Advanced Order Types**
5. **Portfolio Monitoring**
6. **Backtesting Integration**
7. **Complete Trading Workflow**

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Interactive Brokers API documentation
3. Check Interactive Brokers API documentation
4. Review the example code

## Disclaimer

This code is for educational and research purposes. Trading involves risk of loss. Always:
- Test thoroughly in paper trading
- Understand the risks involved
- Consult with financial advisors
- Follow regulatory requirements
- Use appropriate risk management

## License

This implementation is provided under the same license as the main repository.