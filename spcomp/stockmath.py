"""Functions for operating on stock quotes"""


def get_pcts(quotes):
    """Take quotes from Tradier and return daily percent returns

    Params:
        quotes: List[Dict]: Tradier quote data
    Returns:
        List of daily percent returns
    """
    pcts = []
    prev = quotes[0]["close"]
    for i in range(0, len(quotes)):
        curr = float(quotes[i]["close"])
        pct = (curr - prev) / prev
        pcts.append(pct)
        prev = curr
    return pcts


def get_cumulative_return(pcts):
    """Take a set of daily percent returns and sum them into cumulative percent returns

    Params:
        pcts: List[float]: List of daily returns
    Returns:
        List[float]: List of cumulative returns
    """
    cumulative = [0, ]
    for i in range(1, len(pcts)):
        cumulative.append(pcts[i] + cumulative[i-1])
    return cumulative


def subtract(returns, index):
    """Subtract one set of cumulative returns from another

    Params:
        returns: List[float]: List of cumulative returns for the reference symbol
        index: List[float]: List of cumulative returns for the S&P index

    Returns:
        List[float]: Each entry in returns, with its corresponding entry in index subtracted.
    """
    if len(returns) != len(index):
        return "Can't compare unequal lists"
    return [returns[i] - index[i] for i in range(len(returns))]
