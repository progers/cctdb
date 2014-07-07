#!/usr/bin/env python

# Calling Context Tree Comparison

import argparse
import SimpleHTTPServer
import SocketServer
import threading
import time
import webbrowser

PORT = 8001

def main():
    parser = argparse.ArgumentParser(description='Compare two calling context trees.')
    parser.add_argument('-a', required=True, help='First calling context tree (json format)')
    parser.add_argument('-b', required=True, help='First calling context tree (json format)')
    args = parser.parse_args()

    # Open the browser pointing at compare.html
    url = 'http://localhost:' + str(PORT) + '/compare.html?a=' + args.a + '&b=' + args.b;
    webbrowser.open(url, new=2)

    # Start the server.
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(('', PORT), Handler)
    try:
        httpd.serve_forever()
        print "serving at port", PORT
    finally:
        httpd.socket.close()

    # FIXME: This doesn't gracefully handle ctrl+c.

if __name__ == "__main__":
    main()