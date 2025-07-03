#!/usr/bin/env python3
"""
IBKR API Test Script

This script tests the IBKR API implementation without requiring an actual connection.
It validates the structure and basic functionality of the IBKR_Functions class.
"""

import sys
import os

# Try to import pandas - if not available, skip DataFrame tests
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available, skipping DataFrame tests")

# Try to import numpy - if not available, skip numpy tests
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available, skipping numpy tests")

from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Union

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_structures():
    """Test data structure definitions"""
    print("Testing data structures...")
    
    # Test IBKRConfig
    from IBKR_Functions import IBKRConfig
    config = IBKRConfig(host='127.0.0.1', port=7497, client_id=1)
    assert config.host == '127.0.0.1'
    assert config.port == 7497
    assert config.client_id == 1
    print("✓ IBKRConfig test passed")
    
    # Test ContractDetails
    from IBKR_Functions import ContractDetails
    contract = ContractDetails(
        symbol='AAPL',
        sec_type='STK',
        exchange='SMART',
        currency='USD'
    )
    assert contract.symbol == 'AAPL'
    assert contract.sec_type == 'STK'
    print("✓ ContractDetails test passed")
    
    # Test OrderDetails
    from IBKR_Functions import OrderDetails
    order = OrderDetails(
        action='BUY',
        quantity=100,
        order_type='LMT',
        limit_price=150.00
    )
    assert order.action == 'BUY'
    assert order.quantity == 100
    assert order.limit_price == 150.00
    print("✓ OrderDetails test passed")

def test_utility_functions():
    """Test utility functions"""
    print("\\nTesting utility functions...")
    
    # Import utility functions
    from IBKR_Functions import (
        create_stock_contract, 
        create_option_contract,
        create_market_order,
        create_limit_order,
        create_stop_order,
        create_stop_limit_order
    )
    
    # Test stock contract creation
    stock_contract = create_stock_contract('AAPL')
    assert stock_contract.symbol == 'AAPL'
    assert stock_contract.sec_type == 'STK'
    assert stock_contract.exchange == 'SMART'
    assert stock_contract.currency == 'USD'
    print("✓ Stock contract creation test passed")
    
    # Test option contract creation
    option_contract = create_option_contract('AAPL', '20241220', 150.0, 'C')
    assert option_contract.symbol == 'AAPL'
    assert option_contract.sec_type == 'OPT'
    assert option_contract.expiry == '20241220'
    assert option_contract.strike == 150.0
    assert option_contract.right == 'C'
    print("✓ Option contract creation test passed")
    
    # Test order creation
    market_order = create_market_order('BUY', 100)
    assert market_order.action == 'BUY'
    assert market_order.quantity == 100
    assert market_order.order_type == 'MKT'
    print("✓ Market order creation test passed")
    
    limit_order = create_limit_order('SELL', 100, 155.00)
    assert limit_order.action == 'SELL'
    assert limit_order.quantity == 100
    assert limit_order.order_type == 'LMT'
    assert limit_order.limit_price == 155.00
    print("✓ Limit order creation test passed")

def test_ibkr_class_structure():
    """Test IBKR_Functions class structure"""
    print("\\nTesting IBKR_Functions class structure...")
    
    from IBKR_Functions import IBKR_Functions, IBKRConfig
    
    # Test class initialization
    config = IBKRConfig(port=7497)
    ibkr = IBKR_Functions(config)
    
    assert ibkr.config.port == 7497
    assert ibkr.connected == False
    assert ibkr.wrapper is not None
    print("✓ IBKR_Functions initialization test passed")
    
    # Test method existence
    methods = [
        'connect', 'disconnect', 'is_connected',
        'get_market_data', 'get_historical_data',
        'place_order', 'cancel_order', 'get_open_orders',
        'get_portfolio_positions', 'get_account_summary',
        'search_contracts'
    ]
    
    for method in methods:
        assert hasattr(ibkr, method), f"Method {method} not found"
    print("✓ All required methods exist")

def test_integration_functions():
    """Test integration functions"""
    print("\\nTesting integration functions...")
    
    if not PANDAS_AVAILABLE:
        print("⚠ Skipping DataFrame integration tests (pandas not available)")
        return
    
    from IBKR_Functions import ibkr_to_eodhd_format, create_live_trading_bridge
    
    # Test data format conversion
    if not PANDAS_AVAILABLE:
        print("⚠ Skipping data format conversion test (pandas not available)")
        return
        
    sample_ibkr_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'open': [100, 101, 102, 103, 104],
        'high': [105, 106, 107, 108, 109],
        'low': [95, 96, 97, 98, 99],
        'close': [102, 103, 104, 105, 106],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })
    
    eodhd_format = ibkr_to_eodhd_format(sample_ibkr_data)
    
    assert 'date' in eodhd_format.columns
    assert 'open' in eodhd_format.columns
    assert 'high' in eodhd_format.columns
    assert 'low' in eodhd_format.columns
    assert 'close' in eodhd_format.columns
    assert 'volume' in eodhd_format.columns
    assert 'adjusted_close' in eodhd_format.columns
    assert len(eodhd_format) == 5
    print("✓ Data format conversion test passed")

def test_enums_and_constants():
    """Test enums and constants"""
    print("\\nTesting enums and constants...")
    
    from IBKR_Functions import MarketDataType, OrderType, TimeInForce
    
    # Test MarketDataType
    assert MarketDataType.LIVE.value == 1
    assert MarketDataType.DELAYED.value == 3
    print("✓ MarketDataType enum test passed")
    
    # Test OrderType
    assert OrderType.MARKET.value == 'MKT'
    assert OrderType.LIMIT.value == 'LMT'
    assert OrderType.STOP.value == 'STP'
    print("✓ OrderType enum test passed")
    
    # Test TimeInForce
    assert TimeInForce.DAY.value == 'DAY'
    assert TimeInForce.GOOD_TILL_CANCEL.value == 'GTC'
    print("✓ TimeInForce enum test passed")

def test_error_handling():
    """Test error handling scenarios"""
    print("\\nTesting error handling...")
    
    from IBKR_Functions import IBKR_Functions, IBKRConfig
    
    # Test with invalid configuration
    config = IBKRConfig(port=9999)  # Invalid port
    ibkr = IBKR_Functions(config)
    
    # These should handle errors gracefully
    result = ibkr.get_market_data(None)
    assert result is None
    print("✓ Market data error handling test passed")
    
    result = ibkr.get_historical_data(None)
    if PANDAS_AVAILABLE:
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    else:
        # In the mock implementation, it should return a mock DataFrame
        assert hasattr(result, 'empty')
    print("✓ Historical data error handling test passed")
    
    result = ibkr.place_order(None, None)
    assert result is None
    print("✓ Order placement error handling test passed")

def run_all_tests():
    """Run all tests"""
    print("=== IBKR API Implementation Test Suite ===\\n")
    
    try:
        test_data_structures()
        test_utility_functions()
        test_ibkr_class_structure()
        test_integration_functions()
        test_enums_and_constants()
        test_error_handling()
        
        print("\\n=== All Tests Passed! ===")
        print("✓ Data structures working correctly")
        print("✓ Utility functions working correctly")
        print("✓ IBKR_Functions class structure valid")
        if PANDAS_AVAILABLE:
            print("✓ Integration functions working correctly")
        else:
            print("⚠ Integration functions skipped (pandas not available)")
        print("✓ Enums and constants defined correctly")
        print("✓ Error handling implemented correctly")
        
        print("\\n=== Next Steps ===")
        print("1. Install Interactive Brokers TWS or Gateway")
        print("2. Configure API settings")
        print("3. Install required packages: pip install ibapi pandas numpy")
        print("4. Test connection with paper trading")
        print("5. Run the examples in IBKR_Functions.ipynb")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)