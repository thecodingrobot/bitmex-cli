import cmd
import sys
import requests
from pprint import pprint

from terminaltables import SingleTable

from bitmex import BitMEX
from bitmex_websocket import BitMEXWebsocket

BASE_URL = "https://testnet.bitmex.com/api/v1/"
# BASE_URL = "https://www.bitmex.com/api/v1/" # Once you're ready, uncomment this.

API_KEY = None
API_SECRET = None

# remove the following two lines after setting the API keys
print('Set the API keys first. Exiting.')
exit(1)


class BitmexShell(cmd.Cmd):
    intro = 'Welcome to the Bitmex shell. Type help or ? to list commands.\n'
    file = None

    settings = {'symbol': 'XBTUSD'}
    orderIDPrefix = 'cli'

    def __init__(self, symbol):
        super().__init__()
        self.settings['symbol'] = symbol
        if 'testnet' in BASE_URL:
            self.prompt = '(testnet {symbol}) '.format(**self.settings)
        else:
            self.prompt = '(live {symbol}) '.format(**self.settings)
        self.ws = BitMEXWebsocket(endpoint=BASE_URL, symbol=symbol, api_key=API_KEY, api_secret=API_SECRET)
        self.mex = BitMEX(base_url=BASE_URL, symbol=symbol, apiKey=API_KEY, apiSecret=API_SECRET)

    def _set_prompt(self, symbol=None):
        if symbol:
            self.settings['symbol'] = symbol

    def do_funds(self, arg):
        """Print funds"""
        data = self.ws.funds()
        table_data = [
            ['Wallet Balance', data['walletBalance'] / (10 ** 8)],
            ['Unrealised PNL', data['unrealisedPnl'] / (10 ** 8)],
            ['Margin Balance', data['marginBalance'] / (10 ** 8)],
            ['Position Margin', data['maintMargin'] / (10 ** 8)],
            ['Order Margin', 'row3 column2'],
            ['Available Balance', data['availableMargin'] / (10 ** 8)],
        ]
        table = SingleTable(table_data, title='Funds')
        table.inner_heading_row_border = False

        print(table.table)

    def do_set(self, args):
        """Set internal parameters"""

        param, *value = args.split(' ')
        print(value)

        if param == 'symbol':
            self._set_prompt(*value)

    def do_buy(self, args):
        quantity, price = map(lambda x: int(x), args.split(' '))

        try:
            self.mex.buy(quantity, price)
        except requests.exceptions.HTTPError as e:
            print(e)

    def do_b(self, args):
        self.do_buy(args)

    def do_mbuy(self, args):
        quantity = int(args.strip())
        try:
            resp = self.mex.market_buy(quantity)
            pprint(resp)
        except requests.exceptions.HTTPError as e:
            print(e)

    def do_mb(self, args):
        self.do_mbuy(args)

    def do_sell(self, args):
        quantity, price = map(lambda x: int(x), args.split(' '))

        try:
            self.mex.sell(quantity, price)
        except requests.exceptions.HTTPError as e:
            print(e)

    def do_s(self, args):
        self.do_sell(args)

    def do_msell(self, args):
        quantity = int(args.strip())
        try:
            resp = self.mex.market_sell(quantity)
            pprint(resp)
        except requests.exceptions.HTTPError as e:
            print(e)

    def do_ms(self, args):
        self.do_msell(args)

    def do_orders(self, args):
        data = self.ws.open_orders('')
        pprint(data)

    def do_o(self, args):
        self.do_orders(args)

    def do_positions(self, args):
        data = self.ws.positions()
        table_data = [
            ['Symbol', 'Sz', 'AvgEntry', 'Val', 'LiqPx', 'UnPNL', 'rPNL']
        ]
        for d in data:
            table_data.append(
                [
                    d['symbol'],
                    d['currentQty'],
                    d['avgEntryPrice'],
                    "{0:.4f}".format(d['currentQty'] / d['avgEntryPrice']),
                    d['liquidationPrice'],
                    "{0:.4f}".format(d['unrealisedPnl'] / (10 ** 8)),
                    "{0:.4f}".format(d['realisedPnl'] / (10 ** 8))
                ]
            )

        table = SingleTable(table_data, title='Positions')
        print(table.table)

    def do_p(self, args):
        self.do_positions(args)

    def do_exit(self, arg):
        self.close()
        return True

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        return line

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    def __del__(self):
        self.ws.exit()


def parse(arg):
    """Convert a series of zero or more numbers to an argument tuple"""
    return tuple(map(int, arg.split()))


if __name__ == '__main__':
    symbol = 'XBTUSD'
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    try:
        BitmexShell(symbol).cmdloop()
    except KeyboardInterrupt as e:
        print('Exit...')
