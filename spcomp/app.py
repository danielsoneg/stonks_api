import matplotlib
from tradier import Tradier
import base64
import io
import json
import os
import shutil
import stockmath
import logging

shutil.copytree(os.curdir + "/matplotlib_cache", "/tmp/mpl_cache")
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_cache"

matplotlib.use("agg")


Log = logging.getLogger()
Log.setLevel(logging.INFO)
Log.info("Started")
# import requests
tradier = Tradier(os.environ["TRADIER_API_TOKEN"])


def get_returns(symbol, days):
    data = tradier.get_for_days(symbol, days)
    pcts = stockmath.get_pcts(data)
    return stockmath.get_cumulative_return(pcts)


def compare_sp(symbol, days=365):
    returns = get_returns(symbol, days)
    index = get_returns("VOO", days)
    if len(returns) < len(index):
        # the stock has traded fewer days than requested
        index = index[-len(returns):]
    return returns, index, stockmath.subtract(returns, index)


def plot_returns(symbol, returns, index, diffs):
    from matplotlib import pyplot as plt
    Log.info("plot: starting")
    plt.rcParams['figure.figsize'] = [8, 6]
    plt.ioff()
    x = list(range(len(returns)))
    try:
        plt.clf()
        plt.cla()
        plt.title("%s: Returns against the S&P, %d trading days" %
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
        plt.savefig(pic_bytes, format='png')
    finally:
        Log.info("plot: closing")
        plt.close()
        plt.clf()
        plt.cla()
    Log.info("plot: getValue")
    return pic_bytes.getvalue()


def lambda_handler(event, context):
    """Sample pure Lambda function

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

    Log.info('Getting returns')
    returns, index, diffs = compare_sp(symbol, days)
    Log.info('Generating Plot')
    plot = plot_returns(symbol, returns, index, diffs)
    if "font" in event["queryStringParameters"]:
        from matplotlib.font_manager import _fmcache
        with open(_fmcache) as fh:
            fonts = fh.read()
        return {
            'headers': {"Content-Type": "application/json"},
            "statusCode": 200,
            "body": fonts
        }
    Log.info(os.listdir())
    Log.info("returning")
    return {
        'headers': {"Content-Type": "image/png"},
        'statusCode': 200,
        'body': base64.b64encode(plot).decode("utf-8"),
        'isBase64Encoded': True
    }
