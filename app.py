from datetime import datetime
from twisted.internet import reactor, defer
from twisted.web import server, resource
from twisted.web.server import NOT_DONE_YET
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
import json
from loguru import logger
from utils import CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCOUNT_ID, CTRADER_ACCESS_TOKEN

client = None
current_account_id = None
app_auth_completed = defer.Deferred()
account_auth_completed = defer.Deferred()
symbol_list_deferred = None
is_connected = False

def initialize_client():
    global client, is_connected
    if client is None or not is_connected:
        client = Client("demo.ctraderapi.com", 5035, TcpProtocol)
        client.setConnectedCallback(on_connected)
        client.setDisconnectedCallback(on_disconnected)
        client.setMessageReceivedCallback(on_message_received)
        client.startService()

def on_connected(client):
    global is_connected
    logger.info("Connected to cTrader API")
    is_connected = True
    auth_app()

def on_disconnected(client, reason):
    global current_account_id, app_auth_completed, account_auth_completed, symbol_list_deferred, is_connected
    logger.warning(f"Disconnected from cTrader API: {reason}")
    current_account_id = None
    app_auth_completed = defer.Deferred()
    account_auth_completed = defer.Deferred()
    symbol_list_deferred = None
    is_connected = False
    reactor.callLater(5, initialize_client)

def on_message_received(client, message):
    global current_account_id, app_auth_completed, account_auth_completed, symbol_list_deferred
    msg = Protobuf.extract(message)
    if isinstance(msg, ProtoOAApplicationAuthRes):
        logger.info("Application authenticated successfully")
        if not app_auth_completed.called:
            app_auth_completed.callback(None)
        auth_account()
    elif isinstance(msg, ProtoOAAccountAuthRes):
        current_account_id = CTRADER_ACCOUNT_ID
        logger.info(f"Account {current_account_id} authenticated successfully")
        if not account_auth_completed.called:
            account_auth_completed.callback(None)
    elif isinstance(msg, ProtoOAExecutionEvent):
        logger.info(f"Execution event received: {msg}")
    elif isinstance(msg, ProtoOAErrorRes):
        logger.error(f"Error received: {msg.errorCode} - {msg.description}")
        handle_error(msg)
    elif isinstance(msg, ProtoOASymbolsListRes):
        logger.info(f"Symbols list received: {len(msg.symbol)} symbols")
        if symbol_list_deferred and not symbol_list_deferred.called:
            symbol_list_deferred.callback(msg)
    elif isinstance(msg, ProtoHeartbeatEvent):
        logger.debug("Heartbeat received")
    else:
        logger.info(f"Message received: {type(msg)}")

def handle_error(error_msg):
    global app_auth_completed, account_auth_completed, symbol_list_deferred
    error = Exception(f"{error_msg.errorCode} - {error_msg.description}")
    if not app_auth_completed.called:
        app_auth_completed.errback(error)
    elif not account_auth_completed.called:
        account_auth_completed.errback(error)
    elif symbol_list_deferred and not symbol_list_deferred.called:
        symbol_list_deferred.errback(error)
    else:
        logger.error(f"Unhandled error: {error}")

@defer.inlineCallbacks
def auth_app():
    global client
    logger.info("Starting application authentication")
    request = ProtoOAApplicationAuthReq(clientId=CTRADER_CLIENT_ID, clientSecret=CTRADER_CLIENT_SECRET)
    try:
        yield client.send(request)
        yield app_auth_completed
        logger.info("Application authentication completed")
    except Exception as e:
        logger.error(f"Error in app authentication: {e}")
        raise

@defer.inlineCallbacks
def auth_account():
    global client, current_account_id
    logger.info("Starting account authentication")
    request = ProtoOAAccountAuthReq(ctidTraderAccountId=CTRADER_ACCOUNT_ID, accessToken=CTRADER_ACCESS_TOKEN)
    try:
        yield client.send(request)
        yield account_auth_completed
        logger.info("Account authentication completed")
    except Exception as e:
        logger.error(f"Error in account authentication: {e}")
        raise

@defer.inlineCallbacks
def get_symbol_id(symbol_name):
    global client, current_account_id, symbol_list_deferred
    logger.info(f"Getting symbol ID for {symbol_name}")
    request = ProtoOASymbolsListReq(ctidTraderAccountId=current_account_id)
    try:
        symbol_list_deferred = defer.Deferred()
        yield client.send(request)
        
        def on_timeout():
            global symbol_list_deferred
            if symbol_list_deferred and not symbol_list_deferred.called:
                logger.error("Timeout while waiting for symbols list")
                d = symbol_list_deferred
                symbol_list_deferred = None
                d.errback(Exception("Timeout while waiting for symbols list"))
        
        timeout_call = reactor.callLater(10, on_timeout)  # 10 seconds timeout
        
        try:
            response = yield symbol_list_deferred
        finally:
            if timeout_call.active():
                timeout_call.cancel()
        
        if response is None:
            logger.error("Received None response for symbols list")
            raise ValueError("Symbols list response is None")
        
        if not hasattr(response, 'symbol'):
            logger.error(f"Unexpected response structure: {response}")
            raise ValueError("Response does not have 'symbol' attribute")
        
        symbol = next((s for s in response.symbol if s.symbolName == symbol_name), None)
        if symbol:
            logger.info(f"Symbol ID for {symbol_name}: {symbol.symbolId}")
            defer.returnValue(symbol.symbolId)
        else:
            logger.warning(f"Symbol {symbol_name} not found in the list")
            raise ValueError(f"Symbol {symbol_name} not found")
    except Exception as e:
        logger.error(f"Error getting symbol ID: {str(e)}")
        raise
    finally:
        symbol_list_deferred = None

@defer.inlineCallbacks
def execute_trade(data):
    global client, current_account_id, app_auth_completed, account_auth_completed, is_connected
    logger.info("Starting trade execution")
    logger.info(f"Connection status: {'Connected' if is_connected else 'Disconnected'}")
    logger.info(f"Current account ID: {current_account_id}")
    logger.info(f"App auth completed: {app_auth_completed.called}")
    logger.info(f"Account auth completed: {account_auth_completed.called}")
    
    if not is_connected:
        logger.error("Client is not connected")
        raise ValueError("Client is not connected. Please ensure the client is initialized and connected.")

    try:
        yield app_auth_completed
        yield account_auth_completed
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise ValueError(f"Authentication failed: {str(e)}")

    if current_account_id is None:
        logger.error("Account not authenticated, current_account_id is None")
        raise ValueError("Account not authenticated, current_account_id is None")

    symbol_id = yield get_symbol_id(data['symbol'])

    if data['operation'].lower() == "buy":
        trade_side = ProtoOATradeSide.BUY
    elif data['operation'].lower() == "sell":
        trade_side = ProtoOATradeSide.SELL
    else:
        raise ValueError(f"Invalid operation: {data['operation']}")

    volume = int(float(data['amount']) * 100000)  # Convert to cTrader volume

    request = ProtoOANewOrderReq(
        ctidTraderAccountId=current_account_id,
        symbolId=symbol_id,
        orderType=ProtoOAOrderType.MARKET,
        tradeSide=trade_side,
        volume=volume,
        comment=f"Trade executed via TradingView alert: {data['name']}"
    )

    try:
        yield client.send(request)
        logger.info("Trade order sent successfully")
        defer.returnValue({"message": "Trade order sent successfully"})
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise

class WebhookHandler(resource.Resource):
    isLeaf = True

    def render_POST(self, request):
        content_length = int(request.getHeader(b'content-length'))
        raw_data = request.content.read(content_length)
        data = json.loads(raw_data.decode('utf-8'))
        logger.info(f"Received webhook data: {data}")
        
        d = execute_trade(data)
        d.addCallback(self.send_response, request)
        d.addErrback(self.send_error, request)
        
        return NOT_DONE_YET

    def send_response(self, result, request):
        request.setResponseCode(200)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps(result).encode('utf-8'))
        request.finish()
        logger.info("Webhook request processed successfully")

    def send_error(self, failure, request):
        request.setResponseCode(500)
        request.setHeader(b"Content-Type", b"application/json")
        error_message = str(failure.value)
        request.write(json.dumps({"error": error_message}).encode('utf-8'))
        request.finish()
        logger.error(f"Error processing webhook request: {error_message}")

def main():
    initialize_client()
    site = server.Site(WebhookHandler())
    reactor.listenTCP(8000, site)
    logger.info("Server running on http://localhost:8000")
    reactor.run()

if __name__ == "__main__":
    main()