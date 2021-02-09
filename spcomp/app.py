import base64
import io
import json
import logging
import os
import shutil

import matplotlib
from matplotlib.figure import Figure

import stockmath
from tradier import Tradier

Log = logging.getLogger()
Log.setLevel(logging.INFO)
Log.info("Started!")

# Short-circuit matplotlib's font cache generation, which takes ~10+sec
shutil.copytree(os.curdir + "/matplotlib_cache", "/tmp/mpl_cache")
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_cache"
matplotlib.use("agg")

tradier = Tradier(os.environ["TRADIER_API_TOKEN"])


def get_returns(symbol, days):
    """Return cumulative returns for the given symbol and days

    Note that days are calendar days, not trading days, so '28 days'
    will return around 20 data points. 

    Params:
        symbol: str: Stock symbol to get returns for
        days: int: Number of days of returns to get
    Returns:
        list of cumulative percent returns
    """
    data = tradier.get_for_days(symbol, days)
    pcts = stockmath.get_pcts(data)
    return stockmath.get_cumulative_return(pcts)


def compare_sp(symbol, days=365):
    """Compare a symbol against the S&P index.

    Note that days are calendar days, not trading days, so '28 days'
    will return around 20 data points. 

    Params:
        symbol: str: Stock symbol to compare to the S&P
        days: int: Number of calendar days to run the comparison. Default: 365
    Returns:
        Tuple of the symbol's cumulative percent returns, the S&P's cumulative
        percent returns, and the cumulative difference
    """
    returns = get_returns(symbol, days)
    index = get_returns("VOO", days)
    if len(returns) < len(index):
        # the stock has traded fewer days than requested
        index = index[-len(returns):]
    return returns, index, stockmath.subtract(returns, index)


def plot_returns(symbol, returns, index, diffs):
    """Generate a plot of the returns of a stock, the index, and the difference.

    Params:
        symbol: str: Name of the symbol being graphed
        returns: List[float]: cumulative percent returns over time for the symbol
        index: List[float]: cumulative percent returns over time for the index
        diffs: List[float]: cumulative difference between the symbol and index

    Returns:
        Bytestring of the chart as a PNG
    """
    Log.info("plot: starting")
    fig = Figure(figsize=(8, 6), dpi=100)
    plt = fig.add_subplot(111)
    x = list(range(len(returns)))
    plt.set_title("%s: Returns against the S&P, %d trading days" %
                  (symbol.upper(), len(returns)))
    Log.info("plot: adding Y: Symbol returns")
    plt.plot(x, returns, label="Symbol returns", lw=.5)
    Log.info("plot: adding Y: Index returns")
    plt.plot(x, index, label="Index returns", lw=.5)
    Log.info("plot: adding Y: returns over index")
    plt.plot(x, diffs, label="Returns over index", lw=2)
    Log.info("plot: legend & grid")
    plt.legend()
    plt.grid()
    Log.info("plot: allocating BytesIO")
    pic_bytes = io.BytesIO()
    Log.info("plot: Saving")
    fig.savefig(pic_bytes, format='png')
    Log.info("plot: getValue")
    return pic_bytes.getvalue()


def lambda_handler(event, context):
    """Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        #api-gateway-simple-proxy-for-lambda-input-format
        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html

    context: object, required
        Lambda Context runtime methods and attributes

       Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    Log.info("Lambda Handler Start")

    def fail(message, code=400):
        """Generate a failure body with the given message"""
        return {"statusCode": code, "body": json.dumps({"message": message})}

    if (not event["queryStringParameters"] or
            "symbol" not in event["queryStringParameters"]):
        return fail("Must include 'symbol' query parameter")
    symbol = event["queryStringParameters"]["symbol"]
    days = event["queryStringParameters"].get("days", 365)
    try:
        days = int(days)
        assert(days > 0)
    except (ValueError, AssertionError):
        return fail("'days' parameter must be a positive numeric value")

    try:
        Log.info('Getting returns')
        returns, index, diffs = compare_sp(symbol, days)
        Log.info('Generating Plot')
        plot = plot_returns(symbol, returns, index, diffs)
        Log.info("returning")
    except Exception as err:
        """We've already validated inputs, anything else is our failure"""
        return fail(str(err), code=500)
    else:
        return {
            'headers': {"Content-Type": "image/png"},
            'statusCode': 200,
            'body': base64.b64encode(plot).decode("utf-8"),
            'isBase64Encoded': True
        }
