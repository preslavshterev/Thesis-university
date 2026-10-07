CURRENCY_SYMBOL = "€"


def format_money(value):
    return f"{CURRENCY_SYMBOL}{value:,.2f}"