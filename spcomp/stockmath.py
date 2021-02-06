def get_pcts(quotes):
    pcts = []
    prev = quotes[0]["close"]
    for i in range(0, len(quotes)):
        curr = float(quotes[i]["close"])
        pct = (curr - prev) / prev
        pcts.append(pct)
        prev = curr
    return pcts


def get_cumulative_return(pcts):
    cumulative = [0, ]
    for i in range(1, len(pcts)):
        cumulative.append(pcts[i] + cumulative[i-1])
    return cumulative


def subtract(returns, index):
    if len(returns) != len(index):
        return "Can't compare unequal lists"
    return [returns[i] - index[i] for i in range(len(returns))]
