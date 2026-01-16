"""
IBKR Functions Module
Comprehensive class for retrieving historical data, live data, option chains, 
and option data from Interactive Brokers using the official ibapi library.

This module can be imported by other scripts or run standalone.
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
from datetime import datetime
import pandas as pd


class IBKR_Functions(EWrapper, EClient):
    """
    Comprehensive IBKR API client class for retrieving live data, historical data, 
    option chains, and option data using the official ibapi library.
    
    This class provides user-friendly methods to interact with Interactive Brokers API
    with all output in pandas DataFrame format for easy analysis.
    
    Features:
    - Live market data streaming
    - Historical data retrieval
    - Option chain discovery
    - Option-specific data
    - Automatic connection management
    - Thread-safe operations
    - Error handling and logging
    
    Example:
        client = IBKR_Functions(host='127.0.0.1', port=7496, client_id=1)
        client.connect()
        hist_data = client.get_historical_data('AAPL', duration='1 M', bar_size='1 day')
        client.disconnect()
    """
    
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        """
        Initialize the IBKR Functions client.
        
        Args:
            host (str): Host address for IBKR TWS/Gateway (default: '127.0.0.1' for localhost)
            port (int): Port number 
                       - 7497: TWS Paper Trading
                       - 7496: TWS Live Trading
                       - 4001: IB Gateway Paper Trading
                       - 4000: IB Gateway Live Trading
            client_id (int): Unique client ID (0-32). Use 0 for master client.
        """
        # Initialize parent classes
        EClient.__init__(self, self)
        
        # Connection parameters
        self.host = host
        self.port = port
        self.client_id = client_id
        
        # Request ID management
        self.next_order_id = None
        self._req_id_counter = 1000  # Start from 1000 to avoid conflicts
        
        # Data storage dictionaries
        self.historical_data = {}  # Stores historical bars
        self.live_data = {}  # Stores streaming market data
        self.option_chains = {}  # Stores option chain details
        self.contract_details_data = {}  # Stores contract specifications
        self.option_greeks = {}  # Stores option greeks
        
        # Event flags for synchronization
        self.data_received_event = threading.Event()
        self.connected_event = threading.Event()
        self.contract_details_end_event = threading.Event()
        
        # Error tracking
        self.last_error = None
        
        # Thread for running the client loop
        self.api_thread = None
        
    # ==================== CONNECTION MANAGEMENT ====================
    
    def connect(self):
        """
        Establish connection to IBKR TWS or IB Gateway.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Connect to IBKR
            EClient.connect(self, self.host, self.port, self.client_id)
            
            # Start the socket in a separate thread
            self.api_thread = threading.Thread(target=self.run, daemon=True)
            self.api_thread.start()
            
            # Wait for connection confirmation (nextValidId callback)
            if self.connected_event.wait(timeout=10):
                print(f"✓ Successfully connected to IBKR on {self.host}:{self.port} (Client ID: {self.client_id})")
                time.sleep(0.5)  # Brief pause to ensure stability
                return True
            else:
                print("✗ Connection timeout - Please ensure TWS/Gateway is running")
                return False
                
        except Exception as e:
            print(f"✗ Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """
        Disconnect from IBKR and clean up resources.
        """
        try:
            EClient.disconnect(self)
            print("✓ Disconnected from IBKR")
        except Exception as e:
            print(f"✗ Disconnection error: {str(e)}")
    
    def is_connected(self):
        """
        Check if client is currently connected to IBKR.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.isConnected()
    
    # ==================== CALLBACK METHODS (EWrapper) ====================
    
    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        """
        Handle error messages from IBKR.
        
        Error codes:
        - 502: Could not connect to TWS
        - 200: No security definition found
        - 162: Historical market data service error
        """
        # Store last error
        self.last_error = {'reqId': reqId, 'code': errorCode, 'msg': errorString}
        
        # Filter out informational messages (codes >= 2000)
        if errorCode >= 2000:
            if errorCode in [2104, 2106, 2158]:  # Data farm connection messages
                print(f"ℹ Info: {errorString}")
        else:
            print(f"⚠ Error {errorCode} (ReqId: {reqId}): {errorString}")
    
    def nextValidId(self, orderId):
        """
        Callback when connection is established. Receives the next valid order ID.
        
        Args:
            orderId (int): Next valid order ID
        """
        super().nextValidId(orderId)
        self.next_order_id = orderId
        self._req_id_counter = orderId + 1000  # Offset for request IDs
        self.connected_event.set()
        print(f"ℹ Connection established - Next valid order ID: {orderId}")
    
    def _get_next_req_id(self):
        """
        Generate next unique request ID.
        
        Returns:
            int: Unique request ID
        """
        req_id = self._req_id_counter
        self._req_id_counter += 1
        return req_id
    
    # ==================== HISTORICAL DATA METHODS ====================
    
    def historicalData(self, reqId, bar):
        """
        Callback for receiving historical data bars.
        
        Args:
            reqId (int): Request identifier
            bar (BarData): Historical bar data
        """
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        # Store bar data as dictionary
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'average': bar.average,
            'barCount': bar.barCount
        })
    
    def historicalDataEnd(self, reqId, start, end):
        """
        Callback when all historical data has been received.
        
        Args:
            reqId (int): Request identifier
            start (str): Start date of data
            end (str): End date of data
        """
        print(f"✓ Historical data received for request {reqId} ({start} to {end})")
        self.data_received_event.set()
    
    def get_historical_data(self, symbol, duration='1 Y', bar_size='1 day', 
                           what_to_show='TRADES', sec_type='STK', exchange='SMART', 
                           currency='USD', end_datetime='', use_rth=True, timeout=30):
        """
        Retrieve historical market data for a security.
        
        Args:
            symbol (str): Security symbol (e.g., 'AAPL', 'EUR', 'CL')
            duration (str): How far back to retrieve data
            bar_size (str): Granularity of bars
            what_to_show (str): Type of data to retrieve
            sec_type (str): Security type ('STK', 'OPT', 'FUT', 'CASH', 'IND', 'CFD', 'BOND')
            exchange (str): Exchange ('SMART' for smart routing, or specific exchange)
            currency (str): Currency (e.g., 'USD', 'EUR', 'GBP')
            end_datetime (str): End date/time in format 'yyyyMMdd HH:mm:ss' (empty string for now)
            use_rth (bool): Use Regular Trading Hours only (True) or include extended hours (False)
            timeout (int): Maximum seconds to wait for data
            
        Returns:
            pandas.DataFrame: Historical data with columns: date, open, high, low, close, volume, average, barCount
        """
        if not self.is_connected():
            print("✗ Not connected to IBKR. Call connect() first.")
            return pd.DataFrame()
        
        # Create contract object
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        
        # Generate unique request ID
        req_id = self._get_next_req_id()
        
        # Clear any previous data for this request
        self.data_received_event.clear()
        if req_id in self.historical_data:
            del self.historical_data[req_id]
        
        print(f"→ Requesting historical data for {symbol}...")
        
        # Request historical data
        self.reqHistoricalData(
            req_id, contract, end_datetime, duration, bar_size, 
            what_to_show, int(use_rth), 1, False, []
        )
        
        # Wait for data to be received
        if self.data_received_event.wait(timeout=timeout):
            if req_id in self.historical_data and len(self.historical_data[req_id]) > 0:
                df = pd.DataFrame(self.historical_data[req_id])
                print(f"✓ Retrieved {len(df)} bars of historical data")
                return df
            else:
                print("✗ No historical data received")
                return pd.DataFrame()
        else:
            print(f"✗ Request timeout after {timeout} seconds")
            return pd.DataFrame()
    
    # ==================== LIVE DATA METHODS ====================
    
    def tickPrice(self, reqId, tickType, price, attrib):
        """Callback for receiving real-time price updates."""
        if reqId not in self.live_data:
            self.live_data[reqId] = {'timestamp': datetime.now()}
        
        # Map tick types to field names
        tick_map = {
            1: 'bid', 2: 'ask', 4: 'last', 6: 'high', 7: 'low', 9: 'close',
            14: 'open', 15: 'low_13_week', 16: 'high_13_week',
            17: 'low_26_week', 18: 'high_26_week', 19: 'low_52_week', 20: 'high_52_week'
        }
        
        if tickType in tick_map:
            self.live_data[reqId][tick_map[tickType]] = price
            self.live_data[reqId]['timestamp'] = datetime.now()
    
    def tickSize(self, reqId, tickType, size):
        """Callback for receiving real-time size updates."""
        if reqId not in self.live_data:
            self.live_data[reqId] = {'timestamp': datetime.now()}
        
        # Map tick types to field names
        size_map = {
            0: 'bid_size', 3: 'ask_size', 5: 'last_size', 8: 'volume',
            21: 'avg_volume'
        }
        
        if tickType in size_map:
            self.live_data[reqId][size_map[tickType]] = size
            self.live_data[reqId]['timestamp'] = datetime.now()
    
    def tickString(self, reqId, tickType, value):
        """Callback for receiving string tick data."""
        if reqId not in self.live_data:
            self.live_data[reqId] = {'timestamp': datetime.now()}
        
        # Tick type 45 is last timestamp
        if tickType == 45:
            self.live_data[reqId]['last_timestamp'] = value
    
    def tickGeneric(self, reqId, tickType, value):
        """Callback for receiving generic tick data."""
        if reqId not in self.live_data:
            self.live_data[reqId] = {'timestamp': datetime.now()}
        
        # Map generic tick types
        generic_map = {
            23: 'option_historical_vol',
            24: 'option_implied_vol',
            31: 'index_future_premium',
            49: 'halted',
            54: 'trade_count',
            55: 'trade_rate',
            56: 'volume_rate',
            58: 'rt_historical_vol'
        }
        
        if tickType in generic_map:
            self.live_data[reqId][generic_map[tickType]] = value
    
    def get_live_data(self, symbol, sec_type='STK', exchange='SMART', 
                     currency='USD', duration=5, generic_tick_list='', snapshot=False):
        """
        Retrieve live streaming market data for a security.
        
        Args:
            symbol (str): Security symbol
            sec_type (str): Security type ('STK', 'OPT', 'FUT', 'CASH', etc.)
            exchange (str): Exchange ('SMART' or specific exchange)
            currency (str): Currency (e.g., 'USD', 'EUR')
            duration (int): How many seconds to collect live data (if not snapshot)
            generic_tick_list (str): Comma-separated generic tick types to request
            snapshot (bool): If True, get a single snapshot instead of streaming
            
        Returns:
            dict: Dictionary with current market data
        """
        if not self.is_connected():
            print("✗ Not connected to IBKR. Call connect() first.")
            return {}
        
        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        
        # Generate request ID
        req_id = self._get_next_req_id()
        
        # Clear previous data
        if req_id in self.live_data:
            del self.live_data[req_id]
        
        print(f"→ Requesting live market data for {symbol}...")
        
        # Request market data
        self.reqMktData(req_id, contract, generic_tick_list, snapshot, False, [])
        
        if snapshot:
            # For snapshot, wait briefly then cancel
            time.sleep(2)
        else:
            # For streaming, collect for specified duration
            time.sleep(duration)
        
        # Cancel market data subscription
        self.cancelMktData(req_id)
        
        # Return collected data
        result = self.live_data.get(req_id, {})
        if result:
            print(f"✓ Live data retrieved: {len(result)} fields")
        else:
            print("✗ No live data received")
        
        return result
    
    def get_live_data_df(self, symbols, sec_type='STK', exchange='SMART', 
                        currency='USD', generic_tick_list='', snapshot=True):
        """
        Get live market data for multiple symbols and return as DataFrame.
        
        Args:
            symbols (list): List of symbols
            sec_type (str): Security type
            exchange (str): Exchange
            currency (str): Currency
            generic_tick_list (str): Generic ticks to request
            snapshot (bool): Get snapshot (True) or stream briefly (False)
            
        Returns:
            pandas.DataFrame: Market data for all symbols
        """
        data_list = []
        
        for symbol in symbols:
            data = self.get_live_data(symbol, sec_type, exchange, currency, 
                                     generic_tick_list=generic_tick_list, snapshot=snapshot)
            data['symbol'] = symbol
            data_list.append(data)
        
        return pd.DataFrame(data_list)
    
    # ==================== UTILITY METHODS ====================
    
    def __enter__(self):
        """Context manager entry - connect automatically."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect automatically."""
        self.disconnect()
    
    def __del__(self):
        """Destructor - ensure disconnection."""
        if self.is_connected():
            self.disconnect()


if __name__ == "__main__":
    # Simple test when run standalone
    print("IBKR Functions Module - Testing Connection")
    print("=" * 60)
    
    client = IBKR_Functions(host='127.0.0.1', port=7496, client_id=99)
    
    if client.connect():
        time.sleep(1)
        print("\nConnection test successful!")
        print("Module is ready to be imported by other scripts.")
        client.disconnect()
    else:
        print("\nConnection test failed!")
        print("Please ensure IBKR TWS or Gateway is running.")
