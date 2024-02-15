#! /usr/bin/env python3
#
# forked from https://github.com/zkmkarlsruhe/baton


# check websockets installation
import os,sys
try:
    import websockets
except:
    print('\nwebsockets not installed, install it\n')
    cmd = f'"{sys.executable}" -m pip install websockets'
    print(cmd,'\n')
    ret = os.system(cmd)
    if ret != 0:
        print('install websockets faild !\n')
        exit(2)
    else:
        print('install websockets succeed.\n\n')

import asyncio
import websockets
import signal
import argparse

##### parser

parser = argparse.ArgumentParser(description="udp <-> websocket relay server")
parser.add_argument(
    "--wshost", action="store", dest="wshost",
    default="0.0.0.0", help="websocket host ie. ws://####:8081 default: 0.0.0.0")
parser.add_argument(
    "--wsport", action="store", dest="wsport",
    default=8081, type=int, help="websocket port ie. ws://0.0.0.0:####, default: 8081")
parser.add_argument(
    "--recvaddr", action="store", dest="recvaddr",
    default="0.0.0.0", help="udp receive addr, default: 0.0.0.0")
parser.add_argument(
    "--recvport", action="store", dest="recvport",
    default=9999, type=int, help="udp receive port, default: 9999")
# parser.add_argument(
#     "--sendaddr", action="store", dest="sendaddr",
#     default="0.0.0.0", help="udp send addr, default: 0.0.0.0")
# parser.add_argument(
#     "--sendport", action="store", dest="sendport",
#     default=8888, type=int, help="udp send port, default: 8888")
parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
    help="enable verbose printing")

##### UDP

# simple UDP sender asyncio protocol
class UDPSender:

    @staticmethod
    def create(loop, remote_addr, verbose):
        coro = loop.create_datagram_endpoint(
            lambda: UDPSender(verbose=verbose),
            remote_addr=remote_addr, allow_broadcast=True)
            
        task = asyncio.Task(coro,loop=loop)
        _, udpsender = loop.run_until_complete(task)
        return udpsender

    def __init__(self, verbose=True):
        self.transport = None
        self.verbose = verbose # verbosity

    def close(self):
        self.transport.close()

    def send(self, data):
        self.transport.sendto(data)
        if self.verbose:
            print(f"udp sender: sent {data}")

    def connection_made(self, transport):
        self.transport = transport
        if self.verbose:
            print(f"udp sender: connected")

    def connection_lost(self, exc):
        if self.verbose:
            print("udp sender: disconnected, error:", exc)

# simple UDP receiver asyncio protocol
class UDPReceiver:

    @staticmethod
    def create(loop, local_addr, server, verbose):
        coro = loop.create_datagram_endpoint(
            lambda: UDPReceiver(server=server, verbose=verbose),
            local_addr=local_addr, allow_broadcast=True)
            
        task = loop.create_task(coro)
        #task = asyncio.Task(coro,loop=loop)
        
        
        #_, udpreceiver = loop.run_until_complete(task)
        #print(2)
        #return udpreceiver

    def __init__(self, loop=None, server=None, verbose=True):
        self.transport = None
        self.server = server   # websocket server
        self.verbose = verbose # verbosity

    def close(self):
        self.transport.close()

    def connection_made(self, transport):
        self.transport = transport
        if self.verbose:
            sockname = transport.get_extra_info("sockname")
            print(f"udp receiver: connected {sockname}")

    # relay raw datagrams to websocket clients
    def datagram_received(self, data, addr):
        #print('.', end = ' ')
        if self.verbose:
            print(f"udp receiver: received {data} from {addr}")
        
        msgBytes = f'{addr[0]}:{addr[1]}|'.encode('ascii') + data
        for websocket in WebSocketRelayServer.clients:
            asyncio.create_task(websocket.send(msgBytes))  

    def connection_lost(self, exc):
        if self.verbose:
            print(f"udp receiver: disconnected, error: {exc}")

##### websocket

# lazy static class wrapper as websockets.serve only takes a function for ws_handler,
# quicker than figuring out how to implement a custom WebSocketServerProtocol
class WebSocketRelayServer:

    clients = set() # connected clients
    sender = None   # udp sender
    verbose = False # verbosity

    @staticmethod
    def create(loop, addr, sender, verbose=False):
        host, port = addr
        task = websockets.serve(ws_handler=WebSocketRelayServer.relay, host=host, port=port)
        
        server = loop.run_until_complete(task)
        WebSocketRelayServer.sender = sender
        WebSocketRelayServer.verbose = verbose
        if verbose:
            print(f"websocket: connected {addr}")
        return server

    @staticmethod
    async def register(websocket):
        WebSocketRelayServer.clients.add(websocket)
        if WebSocketRelayServer.verbose:
            print("websocket: client connected", websocket)

    @staticmethod
    async def unregister(websocket):
        WebSocketRelayServer.clients.remove(websocket)
        if WebSocketRelayServer.verbose:
            print("websocket: client disconnected", websocket)
                 
               

    # relay raw websocket messages to UDP sender
    @staticmethod
    async def relay(websocket, path):
        await WebSocketRelayServer.register(websocket)
        try:
            async for data in websocket:
                if WebSocketRelayServer.verbose:
                    print(f"websocket: received {data}")
                if WebSocketRelayServer.sender is not None:
                    WebSocketRelayServer.sender.send(data)
        except Exception as exc:
            # ignore "normal" disconnects, from websockets/exceptions.py:
            # 1000 "OK"
            # 1006 "connection closed abnormally [internal]"
            if exc.code != 1000 and exc.code != 1006:
                print(f"websocket: read error: {exc.code} {exc}")
        finally:
            await WebSocketRelayServer.unregister(websocket)

##### signal

# signal handler for nice exit
def sigint_handler():
    asyncio.get_running_loop().stop()

##### GO

# parse
args = parser.parse_args()
print(f"data -> udp {args.recvaddr}:{args.recvport} -> ws://{args.wshost}:{args.wsport} -> all ws clients")
#print(f"recv <- udp {args.sendaddr}:{args.sendport} <- ws://{args.wshost}:{args.wsport}")

# set up event loop
# loop = asyncio.get_event_loop()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.add_signal_handler(signal.SIGINT, sigint_handler)

# udp sender
# udpsender = UDPSender.create(loop, remote_addr=(args.sendaddr, args.sendport), verbose=args.verbose)

# websocket server
#relayserver = WebSocketRelayServer.create(loop, addr=(args.wshost, args.wsport), sender=udpsender, verbose=args.verbose)
relayserver = WebSocketRelayServer.create(loop, addr=(args.wshost, args.wsport), sender=None, verbose=args.verbose)

# udp receiver
udpreceiver = UDPReceiver.create(loop, local_addr=(args.recvaddr, args.recvport), server=relayserver, verbose=args.verbose)

# run forever
try:
    loop.run_forever()
finally:...
    #udpsender.close()
    #udpreceiver.close()
    #relayserver.close()