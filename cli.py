import cmd
import sys
from pprint import pprint

from terminaltables import SingleTable

from bitmex import BitMEX

from utils import bcolors
BASE_URL = "https://testnet.bitmex.com/api/v1/"
# BASE_URL = "https://www.bitmex.com/api/v1/" # Once you're ready, uncomment this.

API_KEY = None
API_SECRET = None

# remove the following two lines after setting the API keys
print('Set the API keys first. Exiting.')
exit(1)

def confirm(msg):
    def confirm_decorator(func):
        def func_wrapper(instance, name):
            if BitmexShell.query_yes_no('Confirm {}?'.format(msg), default="no"):
                func(instance, name)

        return func_wrapper

    return confirm_decorator


class BitmexShell(cmd.Cmd):
    intro = 'Welcome to the Bitmex shell. Type help or ? to list commands.\n'
    file = None

    _symbol = 'XBTUSD'
    orderIDPrefix = 'cli'
    mex = None

    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value: str):
        value = value.upper()
        self._symbol = value
        if 'testnet' in BASE_URL:
            self.prompt = '({}testnet{} {}{}{}) $ '.format(bcolors.LIGHT_GREEN, bcolors.ENDC, bcolors.UNDERLINE,
                                                           self.symbol, bcolors.ENDC)
        else:
            self.prompt = '({}live{} {}{}{}) $ '.format(bcolors.LIGHT_RED, bcolors.ENDC, bcolors.UNDERLINE, self.symbol,
                                                        bcolors.ENDC)
        self.mex = BitMEX(base_url=BASE_URL, symbol=symbol, apiKey=API_KEY, apiSecret=API_SECRET, postOnly=True)

    def do_symbol(self, args):
        if len(args) == 0:
            print('Current symbol: {}'.format(self.symbol))
        else:
            self.symbol = args.strip()

    def complete_symbol(self, text, line, begidx, endidx):
        symbols = filter(lambda x: '_' not in x, map(lambda x: x['symbol'], self.mex.get_symbols()))
        if text:
            return list(filter(lambda x: x.startswith(text), symbols))
        return list(symbols)

    def do_funds(self, arg):
        """Print funds"""
        data = self.mex.get_user_margin()
        table_data = [
            ['Wallet Balance', data['walletBalance'] / (10 ** 8)],
            ['Unrealised PNL', data['unrealisedPnl'] / (10 ** 8)],
            ['Margin Balance', data['marginBalance'] / (10 ** 8)],
            ['Position Margin', data['maintMargin'] / (10 ** 8)],
            ['Order Margin', '???'],
            ['Available Balance', data['availableMargin'] / (10 ** 8)],
        ]
        table = SingleTable(table_data, title='Funds')
        table.inner_heading_row_border = False

        print(table.table)

    def do_positions(self, args):
        data = self.mex.get_position()
        table_data = [
            ['Symbol', 'Sz', 'AvgEntry', 'Val', 'LiqPx', 'UnPNL', 'rPNL']
        ]

        # print empty table
        if len(data) == 1:
            table_data.append([])
        else:
            for d in data:
                if d['currentQty'] == 0:
                    continue
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

        for i in range(0, len(table_data[0])):
            table.justify_columns[i] = 'right'

        print(table.table)

    def do_p(self, args):
        self.do_positions(args)

    @confirm('BUY order')
    def do_b(self, args):
        quantity, price = map(lambda x: int(x), args.split(' '))

        try:
            self.mex.buy(quantity, price)
        except Exception as e:
            print(e)

    @confirm('MARKET BUY')
    def do_mb(self, args):
        quantity = int(args.strip())
        try:
            resp = self.mex.market_buy(quantity)
            pprint(resp)
        except Exception as e:
            print(e)

    @confirm('SELL order')
    def do_s(self, args):
        quantity, price = map(lambda x: int(x), args.split(' '))

        try:
            self.mex.sell(quantity, price)
        except Exception as e:
            print(e)

    @confirm('MARKET SELL')
    def do_ms(self, args):
        quantity = int(args.strip())
        try:
            resp = self.mex.market_sell(quantity)
            pprint(resp)
        except Exception as e:
            print(e)

    def do_orders(self, args):
        data = self.mex.get_open_order()

        table_data = [
            ['Id', 'Sym', 'Side', 'Px', 'Qty', 'Status']
        ]

        for d in data:
            table_data.append([
                d['orderID'].split('-')[0],
                d['symbol'],
                d['side'],
                d['price'],
                d['orderQty'],
                d['ordStatus'],
            ])

        table = SingleTable(table_data, title='Positions')
        print(table.table)

    def do_o(self, args):
        self.do_orders(args)

    @confirm("CANCEL order")
    def do_cancelorder(self, args):
        result = self.mex.cancel(args)
        print(result)

    def complete_cancelorder(self, text, line, begidx, endidx):
        ids = map(lambda x: x['orderID'], self.mex.get_open_order())
        if text:
            return list(filter(lambda x: x.startswith(text), ids))
        return list(ids)

    def do_exit(self, arg):
        pass

    def __del__(self):
        self.mex.close()

    @staticmethod
    def query_yes_no(question, default="yes"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")


if __name__ == '__main__':
    symbol = 'XBTUSD'
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    try:
        BitmexShell(symbol).cmdloop()
    except KeyboardInterrupt as e:
        print('Exit...')
