#!/usr/bin/env python3
"""
IBKR (Interactive Brokers) Native API Functions

This module contains comprehensive functions for interacting with the Interactive Brokers API
using the native TWS API (ibapi).

Features:
- Connection management
- Market data retrieval (real-time and historical)
- Order placement and management
- Portfolio and account information
- Position management
- Contract details and search

Prerequisites:
1. Install Interactive Brokers TWS or IB Gateway
2. Enable API connections in TWS/Gateway
3. Install required Python packages: pip install ibapi pandas numpy

Important Notes:
- Paper trading is recommended for testing
- Ensure proper risk management
- Always test in paper trading before live trading
"""

# Core libraries
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    # Create a minimal pandas-like DataFrame for basic functionality
    class MockDataFrame:
        def __init__(self):
            self.empty = True
            self.columns = []
        def copy(self):
            return MockDataFrame()
        def tail(self):
            return MockDataFrame()
    pd = type('pd', (), {'DataFrame': MockDataFrame})

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

import datetime as dt
import time
import logging
import threading
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

# Native IBKR API imports
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.order import Order
    from ibapi.ticktype import TickTypeEnum
    from ibapi.common import BarData
    IBAPI_AVAILABLE = True
    print("Native IBKR API (ibapi) imported successfully")
except ImportError:
    IBAPI_AVAILABLE = False
    print("Native IBKR API (ibapi) not available. Please install: pip install ibapi")
    # Create mock classes for structure testing
    class EWrapper:
        def __init__(self):
            pass
        def nextValidId(self, orderId):
            pass
        def tickPrice(self, reqId, tickType, price, attrib):
            pass
        def tickSize(self, reqId, tickType, size):
            pass
        def historicalData(self, reqId, bar):
            pass
        def position(self, account, contract, position, avgCost):
            pass
        def accountSummary(self, reqId, account, tag, value, currency):
            pass
        def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
            pass
        def error(self, reqId, errorCode, errorString):
            pass
    
    class EClient:
        def __init__(self, wrapper):
            self.wrapper = wrapper
        def connect(self, host, port, clientId):
            pass
        def disconnect(self):
            pass
        def isConnected(self):
            return False
        def run(self):
            pass
        def reqMarketDataType(self, dataType):
            pass
        def reqMktData(self, reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions):
            pass
        def cancelMktData(self, reqId):
            pass
        def reqHistoricalData(self, reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate, keepUpToDate, chartOptions):
            pass
        def placeOrder(self, orderId, contract, order):
            pass
        def cancelOrder(self, orderId):
            pass
        def reqAllOpenOrders(self):
            pass
        def reqPositions(self):
            pass
        def cancelPositions(self):
            pass
        def reqAccountSummary(self, reqId, groupName, tags):
            pass
        def cancelAccountSummary(self, reqId):
            pass
        def reqContractDetails(self, reqId, contract):
            pass
    
    class Contract:
        def __init__(self):
            self.symbol = ''
            self.secType = ''
            self.exchange = ''
            self.currency = ''
            self.lastTradeDateOrContractMonth = ''
            self.strike = 0.0
            self.right = ''
            self.multiplier = ''
            self.localSymbol = ''
            self.primaryExchange = ''
    
    class Order:
        def __init__(self):
            self.action = ''
            self.totalQuantity = 0
            self.orderType = ''
            self.lmtPrice = 0.0
            self.auxPrice = 0.0
            self.tif = 'DAY'
            self.outsideRth = False
            self.trailStopPrice = 0.0
            self.trailingPercent = 0.0
            self.goodTillDate = ''
    
    class BarData:
        def __init__(self):
            self.date = ''
            self.open = 0.0
            self.high = 0.0
            self.low = 0.0
            self.close = 0.0
            self.volume = 0
            self.wap = 0.0
            self.count = 0

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration and Constants
DEFAULT_HOST = '127.0.0.1'
DEFAULT_TWS_PORT = 7497  # TWS Paper Trading
DEFAULT_GATEWAY_PORT = 4002  # Gateway Paper Trading
LIVE_TWS_PORT = 7496  # TWS Live Trading
LIVE_GATEWAY_PORT = 4001  # Gateway Live Trading

# Default client ID
DEFAULT_CLIENT_ID = 1

# Market data types
class MarketDataType(Enum):
    LIVE = 1
    FROZEN = 2
    DELAYED = 3
    DELAYED_FROZEN = 4

# Order types
class OrderType(Enum):
    MARKET = 'MKT'
    LIMIT = 'LMT'
    STOP = 'STP'
    STOP_LIMIT = 'STP LMT'
    TRAILING_STOP = 'TRAIL'
    TRAILING_STOP_LIMIT = 'TRAIL LIMIT'

# Time in force
class TimeInForce(Enum):
    DAY = 'DAY'
    GOOD_TILL_CANCEL = 'GTC'
    IMMEDIATE_OR_CANCEL = 'IOC'
    FILL_OR_KILL = 'FOK'
    GOOD_TILL_DATE = 'GTD'

# Action types
class ActionType(Enum):
    BUY = 'BUY'
    SELL = 'SELL'
    SHORT_SELL = 'SSHORT'

# Data Structures
@dataclass
class IBKRConfig:
    """Configuration for IBKR connection"""
    host: str = DEFAULT_HOST
    port: int = DEFAULT_TWS_PORT
    client_id: int = DEFAULT_CLIENT_ID
    timeout: int = 30
    readonly: bool = False

@dataclass
class ContractDetails:
    """Contract details structure"""
    symbol: str
    sec_type: str
    exchange: str
    currency: str
    expiry: str = ''
    strike: float = 0.0
    right: str = ''
    multiplier: str = ''
    local_symbol: str = ''
    primary_exchange: str = ''

@dataclass
class OrderDetails:
    """Order details structure"""
    action: str  # BUY or SELL
    quantity: int
    order_type: str
    limit_price: float = 0.0
    stop_price: float = 0.0
    time_in_force: str = 'DAY'
    good_till_date: str = ''
    outside_rth: bool = False
    trail_stop_price: float = 0.0
    trailing_percent: float = 0.0

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    volume: int = 0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    timestamp: str = ''

@dataclass
class PositionData:
    """Position data structure"""
    symbol: str
    position: int
    market_price: float
    market_value: float
    average_cost: float
    unrealized_pnl: float
    realized_pnl: float
    account: str

# IBKR API Wrapper Class
class IBKRWrapper(EWrapper):
    """IBKR API Event Wrapper"""
    
    def __init__(self):
        EWrapper.__init__(self)
        self.next_order_id = None
        self.market_data = {}
        self.historical_data = {}
        self.positions = []
        self.account_summary = {}
        self.contract_details = {}
        self.orders = {}
        self.executions = []
        self.errors = []
        
    def nextValidId(self, orderId: int):
        """Receive next valid order ID"""
        super().nextValidId(orderId)
        self.next_order_id = orderId
        logger.info(f"Next valid order ID: {orderId}")
    
    def tickPrice(self, reqId: int, tickType: int, price: float, attrib):
        """Receive tick price data"""
        super().tickPrice(reqId, tickType, price, attrib)
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        
        if tickType == 1:  # Bid
            self.market_data[reqId]['bid'] = price
        elif tickType == 2:  # Ask
            self.market_data[reqId]['ask'] = price
        elif tickType == 4:  # Last
            self.market_data[reqId]['last'] = price
        elif tickType == 6:  # High
            self.market_data[reqId]['high'] = price
        elif tickType == 7:  # Low
            self.market_data[reqId]['low'] = price
        elif tickType == 9:  # Close
            self.market_data[reqId]['close'] = price
    
    def tickSize(self, reqId: int, tickType: int, size: int):
        """Receive tick size data"""
        super().tickSize(reqId, tickType, size)
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        
        if tickType == 8:  # Volume
            self.market_data[reqId]['volume'] = size
    
    def historicalData(self, reqId: int, bar: BarData):
        """Receive historical data"""
        super().historicalData(reqId, bar)
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'wap': bar.wap,
            'count': bar.count
        })
    
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        """Receive position data"""
        super().position(account, contract, position, avgCost)
        self.positions.append({
            'account': account,
            'symbol': contract.symbol,
            'sec_type': contract.secType,
            'exchange': contract.exchange,
            'currency': contract.currency,
            'position': position,
            'average_cost': avgCost
        })
    
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        """Receive account summary data"""
        super().accountSummary(reqId, account, tag, value, currency)
        if account not in self.account_summary:
            self.account_summary[account] = {}
        self.account_summary[account][tag] = {'value': value, 'currency': currency}
    
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float,
                   avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                   clientId: int, whyHeld: str, mktCapPrice: float):
        """Receive order status updates"""
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId,
                           parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        self.orders[orderId] = {
            'status': status,
            'filled': filled,
            'remaining': remaining,
            'avg_fill_price': avgFillPrice,
            'last_fill_price': lastFillPrice
        }
    
    def error(self, reqId: int, errorCode: int, errorString: str):
        """Receive error messages"""
        super().error(reqId, errorCode, errorString)
        error_msg = f"Error {errorCode}: {errorString}"
        self.errors.append(error_msg)
        logger.error(error_msg)

# Main IBKR Functions Class
class IBKR_Functions(EClient):
    """
    Comprehensive IBKR API Functions Class using Native API
    
    This class provides a complete interface to the Interactive Brokers API,
    including connection management, market data, order management, and portfolio functions.
    """
    
    def __init__(self, config: IBKRConfig = None):
        """Initialize IBKR Functions"""
        self.config = config or IBKRConfig()
        self.wrapper = IBKRWrapper()
        EClient.__init__(self, self.wrapper)
        self.connected = False
        self.request_id = 1000
        
    def get_next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def connect(self, host: str = None, port: int = None, client_id: int = None) -> bool:
        """
        Connect to Interactive Brokers TWS or Gateway
        
        Args:
            host: TWS/Gateway host address
            port: TWS/Gateway port
            client_id: Unique client identifier
            
        Returns:
            bool: True if connected successfully
        """
        try:
            if not IBAPI_AVAILABLE:
                logger.warning("Native IBKR API (ibapi) not available. Please install: pip install ibapi")
                return False
                
            # Use provided parameters or defaults
            host = host or self.config.host
            port = port or self.config.port
            client_id = client_id or self.config.client_id
            
            # Connect to TWS/Gateway
            super().connect(host, port, clientId=client_id)
            
            # Start the socket in a separate daemon thread
            api_thread = threading.Thread(target=self.run, daemon=True)
            api_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            if self.isConnected():
                self.connected = True
                logger.info(f"Connected to IBKR at {host}:{port} with client ID {client_id}")
                
                # Wait for next valid order ID
                timeout = 10
                start_time = time.time()
                while self.wrapper.next_order_id is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                return True
            else:
                logger.error("Failed to establish connection")
                return False
            
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.isConnected():
            super().disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.connected and self.isConnected()
    
    def _create_contract(self, contract_details: ContractDetails) -> Contract:
        """Create IBKR Contract object from ContractDetails"""
        contract = Contract()
        contract.symbol = contract_details.symbol
        contract.secType = contract_details.sec_type
        contract.exchange = contract_details.exchange
        contract.currency = contract_details.currency
        
        if contract_details.expiry:
            contract.lastTradeDateOrContractMonth = contract_details.expiry
        if contract_details.strike:
            contract.strike = contract_details.strike
        if contract_details.right:
            contract.right = contract_details.right
        if contract_details.multiplier:
            contract.multiplier = contract_details.multiplier
        if contract_details.local_symbol:
            contract.localSymbol = contract_details.local_symbol
        if contract_details.primary_exchange:
            contract.primaryExchange = contract_details.primary_exchange
            
        return contract
    
    def _create_order(self, order_details: OrderDetails) -> Order:
        """Create IBKR Order object from OrderDetails"""
        order = Order()
        order.action = order_details.action
        order.totalQuantity = order_details.quantity
        order.orderType = order_details.order_type
        order.tif = order_details.time_in_force
        order.outsideRth = order_details.outside_rth
        
        if order_details.limit_price > 0:
            order.lmtPrice = order_details.limit_price
        if order_details.stop_price > 0:
            order.auxPrice = order_details.stop_price
        if order_details.trail_stop_price > 0:
            order.trailStopPrice = order_details.trail_stop_price
        if order_details.trailing_percent > 0:
            order.trailingPercent = order_details.trailing_percent
        if order_details.good_till_date:
            order.goodTillDate = order_details.good_till_date
            
        return order
    
    def get_market_data(self, contract_details: ContractDetails, 
                       data_type: MarketDataType = MarketDataType.DELAYED) -> Optional[MarketData]:
        """
        Get real-time market data for a contract
        
        Args:
            contract_details: Contract details
            data_type: Market data type (live, delayed, etc.)
            
        Returns:
            MarketData object or None
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None
            
        try:
            # Create contract
            contract = self._create_contract(contract_details)
            
            # Get request ID
            req_id = self.get_next_request_id()
            
            # Request market data
            self.reqMarketDataType(data_type.value)
            self.reqMktData(req_id, contract, '', False, False, [])
            
            # Wait for data
            time.sleep(2)
            
            # Get data from wrapper
            if req_id in self.wrapper.market_data:
                data = self.wrapper.market_data[req_id]
                
                market_data = MarketData(
                    symbol=contract_details.symbol,
                    bid=data.get('bid', 0.0),
                    ask=data.get('ask', 0.0),
                    last=data.get('last', 0.0),
                    volume=data.get('volume', 0),
                    high=data.get('high', 0.0),
                    low=data.get('low', 0.0),
                    close=data.get('close', 0.0),
                    timestamp=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                
                # Cancel market data subscription
                self.cancelMktData(req_id)
                
                return market_data
            else:
                logger.warning(f"No market data received for {contract_details.symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return None
    
    def get_historical_data(self, contract_details: ContractDetails, duration: str = "1 M",
                          bar_size: str = "1 day", what_to_show: str = "TRADES",
                          use_rth: bool = True) -> pd.DataFrame:
        """
        Get historical data for a contract
        
        Args:
            contract_details: Contract details
            duration: How far back to retrieve data
            bar_size: Bar size (1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day)
            what_to_show: Type of data (TRADES, MIDPOINT, BID, ASK)
            use_rth: Use regular trading hours only
            
        Returns:
            DataFrame with historical data
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return pd.DataFrame()
            
        try:
            # Create contract
            contract = self._create_contract(contract_details)
            
            # Get request ID
            req_id = self.get_next_request_id()
            
            # Clear any existing data
            if req_id in self.wrapper.historical_data:
                del self.wrapper.historical_data[req_id]
            
            # Request historical data
            end_datetime = dt.datetime.now().strftime('%Y%m%d %H:%M:%S')
            self.reqHistoricalData(req_id, contract, end_datetime, duration, bar_size,
                                 what_to_show, int(use_rth), 1, False, [])
            
            # Wait for data
            timeout = 30
            start_time = time.time()
            while (req_id not in self.wrapper.historical_data or 
                   len(self.wrapper.historical_data[req_id]) == 0) and \
                  (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            # Get data from wrapper
            if req_id in self.wrapper.historical_data and self.wrapper.historical_data[req_id]:
                data = self.wrapper.historical_data[req_id]
                df = pd.DataFrame(data)
                
                # Convert date column
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                return df
            else:
                logger.warning(f"No historical data received for {contract_details.symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return pd.DataFrame()
    
    def place_order(self, contract_details: ContractDetails, 
                   order_details: OrderDetails) -> Optional[int]:
        """
        Place an order
        
        Args:
            contract_details: Contract details
            order_details: Order details
            
        Returns:
            Order ID if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None
            
        if self.wrapper.next_order_id is None:
            logger.error("Next order ID not available")
            return None
            
        try:
            # Create contract and order
            contract = self._create_contract(contract_details)
            order = self._create_order(order_details)
            
            # Get order ID
            order_id = self.wrapper.next_order_id
            self.wrapper.next_order_id += 1
            
            # Place order
            self.placeOrder(order_id, contract, order)
            
            logger.info(f"Order placed: {order_details.action} {order_details.quantity} {contract_details.symbol} at {order_details.limit_price if order_details.limit_price > 0 else 'Market'}")
            
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation request sent successfully
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return False
            
        try:
            self.cancelOrder(order_id)
            logger.info(f"Cancel request sent for order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            return False
    
    def get_open_orders(self) -> List[Dict]:
        """
        Get all open orders
        
        Returns:
            List of open orders
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return []
            
        try:
            # Request all open orders
            self.reqAllOpenOrders()
            
            # Wait for data
            time.sleep(2)
            
            # Return order data
            return list(self.wrapper.orders.values())
            
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []
    
    def get_portfolio_positions(self) -> List[PositionData]:
        """
        Get all portfolio positions
        
        Returns:
            List of PositionData objects
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return []
            
        try:
            # Clear existing positions
            self.wrapper.positions = []
            
            # Request positions
            self.reqPositions()
            
            # Wait for data
            time.sleep(3)
            
            # Convert to PositionData objects
            positions = []
            for pos in self.wrapper.positions:
                if pos['position'] != 0:  # Only include non-zero positions
                    position_data = PositionData(
                        symbol=pos['symbol'],
                        position=int(pos['position']),
                        market_price=0.0,  # Will be updated with market data
                        market_value=0.0,
                        average_cost=pos['average_cost'],
                        unrealized_pnl=0.0,
                        realized_pnl=0.0,
                        account=pos['account']
                    )
                    positions.append(position_data)
            
            # Cancel position updates
            self.cancelPositions()
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting portfolio positions: {str(e)}")
            return []
    
    def get_account_summary(self, account: str = 'All') -> Dict[str, Any]:
        """
        Get account summary information
        
        Args:
            account: Account number or 'All'
            
        Returns:
            Dictionary with account information
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return {}
            
        try:
            # Clear existing account summary
            self.wrapper.account_summary = {}
            
            # Request account summary
            req_id = self.get_next_request_id()
            tags = 'NetLiquidation,TotalCashValue,SettledCash,AccruedCash,BuyingPower,EquityWithLoanValue,GrossPositionValue,RegTEquity,RegTMargin,SMA,InitMarginReq,MaintMarginReq,AvailableFunds,ExcessLiquidity'
            
            self.reqAccountSummary(req_id, account, tags)
            
            # Wait for data
            time.sleep(3)
            
            # Cancel account summary updates
            self.cancelAccountSummary(req_id)
            
            return self.wrapper.account_summary
            
        except Exception as e:
            logger.error(f"Error getting account summary: {str(e)}")
            return {}
    
    def search_contracts(self, symbol: str, sec_type: str = 'STK', 
                        exchange: str = 'SMART', currency: str = 'USD') -> List[Dict]:
        """
        Search for contracts
        
        Args:
            symbol: Symbol to search
            sec_type: Security type
            exchange: Exchange
            currency: Currency
            
        Returns:
            List of contract details
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return []
            
        try:
            # Create contract for search
            contract = Contract()
            contract.symbol = symbol
            contract.secType = sec_type
            contract.exchange = exchange
            contract.currency = currency
            
            # Get request ID
            req_id = self.get_next_request_id()
            
            # Clear existing contract details
            if req_id in self.wrapper.contract_details:
                del self.wrapper.contract_details[req_id]
            
            # Request contract details
            self.reqContractDetails(req_id, contract)
            
            # Wait for data
            time.sleep(3)
            
            # Return contract details
            return self.wrapper.contract_details.get(req_id, [])
            
        except Exception as e:
            logger.error(f"Error searching contracts: {str(e)}")
            return []
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

# Contract Creation Utility Functions
def create_stock_contract(symbol: str, exchange: str = 'SMART', 
                         currency: str = 'USD', primary_exchange: str = '') -> ContractDetails:
    """Create a stock contract"""
    return ContractDetails(
        symbol=symbol,
        sec_type='STK',
        exchange=exchange,
        currency=currency,
        primary_exchange=primary_exchange
    )

def create_option_contract(symbol: str, expiry: str, strike: float, right: str,
                          exchange: str = 'SMART', currency: str = 'USD', 
                          multiplier: str = '100') -> ContractDetails:
    """Create an option contract"""
    return ContractDetails(
        symbol=symbol,
        sec_type='OPT',
        exchange=exchange,
        currency=currency,
        expiry=expiry,
        strike=strike,
        right=right,
        multiplier=multiplier
    )

def create_futures_contract(symbol: str, expiry: str, exchange: str, 
                           currency: str = 'USD', multiplier: str = '') -> ContractDetails:
    """Create a futures contract"""
    return ContractDetails(
        symbol=symbol,
        sec_type='FUT',
        exchange=exchange,
        currency=currency,
        expiry=expiry,
        multiplier=multiplier
    )

def create_forex_contract(symbol: str, currency: str = 'USD') -> ContractDetails:
    """Create a forex contract"""
    return ContractDetails(
        symbol=symbol,
        sec_type='CASH',
        exchange='IDEALPRO',
        currency=currency
    )

# Order Creation Utility Functions
def create_market_order(action: str, quantity: int, 
                       time_in_force: str = 'DAY', outside_rth: bool = False) -> OrderDetails:
    """Create a market order"""
    return OrderDetails(
        action=action,
        quantity=quantity,
        order_type=OrderType.MARKET.value,
        time_in_force=time_in_force,
        outside_rth=outside_rth
    )

def create_limit_order(action: str, quantity: int, limit_price: float,
                      time_in_force: str = 'DAY', outside_rth: bool = False) -> OrderDetails:
    """Create a limit order"""
    return OrderDetails(
        action=action,
        quantity=quantity,
        order_type=OrderType.LIMIT.value,
        limit_price=limit_price,
        time_in_force=time_in_force,
        outside_rth=outside_rth
    )

def create_stop_order(action: str, quantity: int, stop_price: float,
                     time_in_force: str = 'DAY', outside_rth: bool = False) -> OrderDetails:
    """Create a stop order"""
    return OrderDetails(
        action=action,
        quantity=quantity,
        order_type=OrderType.STOP.value,
        stop_price=stop_price,
        time_in_force=time_in_force,
        outside_rth=outside_rth
    )

def create_stop_limit_order(action: str, quantity: int, limit_price: float, stop_price: float,
                           time_in_force: str = 'DAY', outside_rth: bool = False) -> OrderDetails:
    """Create a stop-limit order"""
    return OrderDetails(
        action=action,
        quantity=quantity,
        order_type=OrderType.STOP_LIMIT.value,
        limit_price=limit_price,
        stop_price=stop_price,
        time_in_force=time_in_force,
        outside_rth=outside_rth
    )

def create_trailing_stop_order(action: str, quantity: int, trailing_percent: float = 0.0,
                              trail_stop_price: float = 0.0, time_in_force: str = 'DAY',
                              outside_rth: bool = False) -> OrderDetails:
    """Create a trailing stop order"""
    return OrderDetails(
        action=action,
        quantity=quantity,
        order_type=OrderType.TRAILING_STOP.value,
        trailing_percent=trailing_percent,
        trail_stop_price=trail_stop_price,
        time_in_force=time_in_force,
        outside_rth=outside_rth
    )

# Integration Functions
def ibkr_to_eodhd_format(ibkr_data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert IBKR data format to EODHD format for compatibility
    
    Args:
        ibkr_data: DataFrame with IBKR historical data
        
    Returns:
        DataFrame in EODHD format
    """
    if ibkr_data.empty:
        return pd.DataFrame()
    
    try:
        # Create EODHD format DataFrame
        eodhd_data = ibkr_data.copy()
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in eodhd_data.columns:
                eodhd_data[col] = 0.0
        
        # Add adjusted_close (assuming no adjustments for now)
        eodhd_data['adjusted_close'] = eodhd_data['close']
        
        # Reset index if date is the index
        if eodhd_data.index.name == 'date' or isinstance(eodhd_data.index, pd.DatetimeIndex):
            eodhd_data.reset_index(inplace=True)
        
        # Ensure date column exists
        if 'date' not in eodhd_data.columns:
            eodhd_data['date'] = pd.date_range(start='2024-01-01', periods=len(eodhd_data))
        
        # Select and order columns to match EODHD format
        eodhd_columns = ['date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
        eodhd_data = eodhd_data[eodhd_columns]
        
        return eodhd_data
        
    except Exception as e:
        logger.error(f"Error converting IBKR to EODHD format: {str(e)}")
        return pd.DataFrame()

def create_live_trading_bridge(ibkr_instance: IBKR_Functions):
    """
    Create a bridge function for live trading integration
    
    Args:
        ibkr_instance: Connected IBKR_Functions instance
        
    Returns:
        Function that can execute trading signals
    """
    def execute_signal(symbol: str, action: str, quantity: int, order_type: str = 'MKT',
                      limit_price: float = 0.0, stop_price: float = 0.0) -> Optional[int]:
        """
        Execute a trading signal
        
        Args:
            symbol: Trading symbol
            action: BUY or SELL
            quantity: Number of shares
            order_type: Order type (MKT, LMT, STP, etc.)
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            
        Returns:
            Order ID if successful
        """
        try:
            # Create contract
            contract = create_stock_contract(symbol)
            
            # Create order based on type
            if order_type == 'MKT':
                order = create_market_order(action, quantity)
            elif order_type == 'LMT':
                order = create_limit_order(action, quantity, limit_price)
            elif order_type == 'STP':
                order = create_stop_order(action, quantity, stop_price)
            elif order_type == 'STP LMT':
                order = create_stop_limit_order(action, quantity, limit_price, stop_price)
            else:
                logger.error(f"Unsupported order type: {order_type}")
                return None
            
            # Place order
            order_id = ibkr_instance.place_order(contract, order)
            
            logger.info(f"Signal executed: {action} {quantity} {symbol} (Order ID: {order_id})")
            return order_id
            
        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
            return None
    
    return execute_signal

if __name__ == "__main__":
    print("=== IBKR Native API Functions Ready ===")
    print("\nIMPORTANT: Always test with paper trading first!")
    print("Paper trading port: 7497")
    print("Live trading port: 7496")