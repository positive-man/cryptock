# noinspection SpellCheckingInspection
__author__ = 'wookjae.jo'

import time

from margin import load_active_symbol_list, calculate_margins, eat_margin, Margin

holding_quote_assets = ['BTC', 'BNB', 'ETH']


def run():
    active_symbol_list = load_active_symbol_list()
    margins = [m for m in calculate_margins(active_symbol_list) if m.symbol_from.quote_asset]
    margins.sort(key=lambda m: m.percentage, reverse=True)
    top_margin = margins[0]
    print(margins[0])
    print(margins[1])
    print(margins[2])
    print(margins[3])
    print(margins[4])

    Margin.of(
        symbol_from=top_margin.symbol_from,
        symbol_bridge=top_margin.symbol_bridge,
        symbol_to=top_margin.symbol_to

              )


    if top_margin.percentage < 1.5:
        print('Skipping...')
        return

    eat_margin(
        active_symbol_list=active_symbol_list,
        symbol_from=top_margin.symbol_from,
        symbol_to=top_margin.symbol_to
    )


def main():
    while True:
        run()
        time.sleep(5)


if __name__ == '__main__':
    main()
