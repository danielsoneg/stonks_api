"""Client library for Tradier API"""
import arrow
import requests
import os

from json import JSONDecodeError


class Tradier:
    """Interface to Tradier's API"""
    class TradierError(Exception):
        """Unspecified API error"""

    class BadRequest(TradierError):
        """We made a bad request to Tradier"""

    class BadResponse(TradierError):
        """Tradier gave us a bad response"""

    def __init__(self, token, sandbox=True):
        """Initiate the client

        Params:
            token: str: Tradier API token
            sandbox: Bool: Use the sandbox API. [True]
        """
        self.token = token
        self.base_url = "https://%s.tradier.com/v1" % "sandbox" if sandbox else "api"

    def make_call(self, url, params):
        """Make a GET call to the Tradier API

        Params:
            url: str: Path to call.
            params: Dict[str:Any]: Query parameters
        Returns:
            Decoded JSON response
        Raises:
            TradierError: For general errors
            BadRequest: For return codes of 400-499
            BadResponse: For return codes of 500+ or unparseable responses
        """
        url = "%s/%s" % (self.base_url, url)
        headers = {"Authorization": "Bearer %s" %
                   self.token, "Accept": "application/json"}
        try:
            resp = requests.get(url, params=params, headers=headers)
        except requests.RequestException as err:
            raise self.TradierError("Error talking to Tradier")
        if resp.status_code >= 500:
            raise self.BadResponse("Tradier returned a %d" % resp.status_code)
        if resp.status_code >= 400:
            raise self.BadRequest("Tradier returned a %d" % resp.status_code)

        try:
            return resp.json()
        except JSONDecodeError as err:
            raise self.BadResponse("Response was invalid json")

    def get_for_days(self, symbol, days):
        """Get returns for a symbol for a number of days

        Params:
            symbol: str: Symbol to query
            days: int: number of days to query
        Returns:
            Parsed returns from Tradier's API
        Raises:
            TradierException: for errors talking to Tradier
            BadRequest: for 400 codes from tradier
            BadResponse: for 500 codes, unparseable responses, and badly formatted responses
        """
        params = {
            "symbol": symbol,
            "interval": "daily",
            "start": arrow.utcnow().shift(days=-days).format("YYYY-MM-DD"),
            "end": arrow.utcnow().format("YYYY-MM-DD"),
        }
        try:
            body = self.make_call("markets/history", params)
            return body["history"]["day"]
        except IndexError:
            raise self.BadResponse("Tradier did not return the expected data")
