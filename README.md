# Quantitative Research Repository

A comprehensive quantitative research and algorithmic trading platform with market data access, backtesting capabilities, option pricing models, and live trading execution via Interactive Brokers API.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [New: Interactive Brokers API Integration](#new-interactive-brokers-api-integration)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This repository provides a complete quantitative research and algorithmic trading framework that includes:

- **Market Data Access**: Multiple data sources (EODHD, Interactive Brokers)
- **Backtesting Engine**: Comprehensive backtesting capabilities
- **Option Pricing Models**: Black-Scholes and other pricing models
- **Live Trading**: Real-time order execution via Interactive Brokers API
- **Portfolio Management**: Real-time monitoring and risk management
- **Research Tools**: Advanced analytics and visualization

## ✨ Features

### Core Functionality
- ✅ Historical market data fetching (EODHD API)
- ✅ Real-time market data (Interactive Brokers API)
- ✅ Comprehensive backtesting engine
- ✅ Option pricing models (Black-Scholes, etc.)
- ✅ Portfolio optimization and analysis
- ✅ Risk management tools

### Trading Infrastructure
- ✅ Live order execution via Interactive Brokers API
- ✅ Multiple order types (Market, Limit, Stop, Stop-Limit)
- ✅ Real-time portfolio monitoring
- ✅ Position management and tracking
- ✅ Account information and balance tracking

### Data Analysis
- ✅ Technical indicators and signals
- ✅ Statistical analysis and modeling
- ✅ Correlation analysis
- ✅ Performance metrics and reporting

## 🚀 New: Interactive Brokers API Integration

### What's New
We've added comprehensive Interactive Brokers (IBKR) API integration that enables:

- **Real-time Market Data**: Live quotes, historical data, and market depth
- **Order Management**: Place, modify, and cancel orders programmatically
- **Portfolio Monitoring**: Real-time position tracking and P&L monitoring
- **Account Management**: Access account information and balances
- **Risk Management**: Automated stop-losses and position sizing
- **Integration**: Seamless integration with existing backtesting engine

### Key Benefits
- **Live Trading**: Execute backtesting strategies in real-time
- **Professional-Grade**: Enterprise-level trading infrastructure
- **Risk Management**: Built-in risk controls and monitoring
- **Flexibility**: Support for stocks, options, futures, and more
- **Reliability**: Robust error handling and reconnection logic

### Quick Start with IBKR API
```python
from IBKR_Functions import IBKR_Functions, IBKRConfig, create_stock_contract

# Configure connection (paper trading)
config = IBKRConfig(port=7497)

# Connect and get market data
with IBKR_Functions(config) as ibkr:
    if ibkr.connect():
        # Get market data
        contract = create_stock_contract('AAPL')
        market_data = ibkr.get_market_data(contract)
        print(f"AAPL Last Price: ${market_data.last:.2f}")
        
        # Get portfolio positions
        positions = ibkr.get_portfolio_positions()
        print(positions)
```

## 📁 Repository Structure

```
Quant_research/
├── IBKR_Functions.ipynb          # NEW: Interactive Brokers API functions
├── IBKR_README.md               # NEW: IBKR API documentation
├── IBKR_Integration_Example.md  # NEW: Complete integration examples
├── requirements.txt             # NEW: Python dependencies
├── EODHD_Functions.ipynb        # EODHD API functions
├── BackTesting_Engine.ipynb     # Backtesting framework
├── Option_Pricing_Models.ipynb  # Option pricing models
├── Option_analysis.ipynb        # Option analysis tools
├── Archive/                     # Historical versions
│   ├── Input_Tools_v1_old.ipynb
│   └── Research_Tools_v1_old.ipynb
├── simple_test.py              # NEW: Basic functionality tests
└── LICENSE                     # MIT License
```

## 🚀 Getting Started

### Prerequisites

1. **Python Environment**
   ```bash
   python >= 3.7
   ```

2. **API Access**
   - EODHD API key (for historical data)
   - Interactive Brokers account (for live trading)

3. **Interactive Brokers Setup** (Optional, for live trading)
   - Download and install TWS or IB Gateway
   - Enable API access in account settings
   - Configure API settings in TWS/Gateway

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/raviteja1608/Quant_research.git
   cd Quant_research
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **For Interactive Brokers API** (Optional)
   ```bash
   pip install ibapi
   ```

4. **Run Tests**
   ```bash
   python simple_test.py
   ```

### Configuration

1. **EODHD API Configuration**
   ```python
   # In EODHD_Functions.ipynb
   API_Eodhd = "your_eodhd_api_key"
   ```

2. **Interactive Brokers Configuration**
   ```python
   # Paper trading (recommended for testing)
   config = IBKRConfig(port=7497)
   
   # Live trading (use with caution)
   config = IBKRConfig(port=7496)
   ```

## 📚 Usage Examples

### 1. Basic Market Data Analysis
```python
# Using EODHD API
from EODHD_Functions import EODHD_Functions

client = EODHD_Functions()
historical_data = client.Fetch_historical_price("AAPL.US", "2023-01-01", "2023-12-31", "d")
print(historical_data.head())
```

### 2. Live Trading with IBKR API
```python
# Using Interactive Brokers API
from IBKR_Functions import IBKR_Functions, IBKRConfig, create_stock_contract, create_limit_order

config = IBKRConfig(port=7497)  # Paper trading

with IBKR_Functions(config) as ibkr:
    if ibkr.connect():
        # Place a limit order
        contract = create_stock_contract('AAPL')
        order = create_limit_order('BUY', 100, 150.00)
        order_id = ibkr.place_order(contract, order)
        print(f"Order placed: {order_id}")
```

### 3. Option Pricing
```python
# Using Black-Scholes model
from Option_Pricing_Models import black_scholes

call_price, put_price = black_scholes(
    S=100,      # Current stock price
    K=105,      # Strike price
    T=30/365,   # Time to expiration
    r=0.05,     # Risk-free rate
    sigma=0.2   # Volatility
)
print(f"Call Price: ${call_price:.2f}, Put Price: ${put_price:.2f}")
```

### 4. Backtesting Strategy
```python
# Using backtesting engine
# See BackTesting_Engine.ipynb for comprehensive examples
```

### 5. Portfolio Monitoring
```python
# Real-time portfolio monitoring
from IBKR_Functions import real_time_portfolio_monitor

with IBKR_Functions(config) as ibkr:
    if ibkr.connect():
        # Start monitoring
        monitor_thread = real_time_portfolio_monitor(ibkr, update_interval=60)
        # Monitor runs in background
```

## 📖 Documentation

### Core Documentation
- **[IBKR_README.md](IBKR_README.md)**: Complete Interactive Brokers API documentation
- **[IBKR_Integration_Example.md](IBKR_Integration_Example.md)**: Detailed integration examples
- **[EODHD_Functions.ipynb](EODHD_Functions.ipynb)**: EODHD API functions and examples
- **[BackTesting_Engine.ipynb](BackTesting_Engine.ipynb)**: Backtesting framework documentation

### Jupyter Notebooks
- **[IBKR_Functions.ipynb](IBKR_Functions.ipynb)**: Interactive Brokers API implementation
- **[Option_Pricing_Models.ipynb](Option_Pricing_Models.ipynb)**: Option pricing models
- **[Option_analysis.ipynb](Option_analysis.ipynb)**: Option analysis tools

### API References
- [Interactive Brokers API Documentation](https://interactivebrokers.github.io/tws-api/)
- [EODHD API Documentation](https://eodhd.com/financial-apis/)

## 🛡️ Risk Management

### Built-in Risk Controls
- **Position Sizing**: Automated position sizing based on risk parameters
- **Stop Losses**: Automatic stop-loss order placement
- **Portfolio Limits**: Maximum position and exposure limits
- **Real-time Monitoring**: Continuous portfolio monitoring and alerts

### Best Practices
1. **Always start with paper trading**
2. **Use appropriate position sizing**
3. **Set stop-loss orders**
4. **Monitor portfolio regularly**
5. **Keep detailed logs**
6. **Have emergency procedures**

## 🔧 Testing

### Run Basic Tests
```bash
python simple_test.py
```

### Test IBKR Connection (requires TWS/Gateway)
```python
from IBKR_Functions import IBKR_Functions, IBKRConfig

config = IBKRConfig(port=7497)
with IBKR_Functions(config) as ibkr:
    if ibkr.connect():
        print("Connection successful!")
```

## 📈 Advanced Features

### Algorithmic Trading
- **Signal Generation**: Multiple technical indicators
- **Strategy Backtesting**: Historical performance analysis
- **Live Execution**: Automated order placement
- **Performance Tracking**: Real-time P&L monitoring

### Research Tools
- **Data Analysis**: Statistical analysis and modeling
- **Visualization**: Charts and graphs
- **Correlation Analysis**: Asset correlation studies
- **Risk Metrics**: VaR, Sharpe ratio, and more

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves significant risk of loss. Always:

- Test thoroughly in paper trading
- Use appropriate risk management
- Understand the risks involved
- Consult with financial advisors
- Follow all regulatory requirements
- Never risk more than you can afford to lose

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Interactive Brokers](https://www.interactivebrokers.com/)
- [EODHD Financial APIs](https://eodhd.com/)
- [Python for Finance](https://github.com/topics/quantitative-finance)

---

**📞 Support**: For questions and issues, please open an issue in the repository.

**🌟 Star this repository** if you find it useful!

---

*Last updated: January 2024*