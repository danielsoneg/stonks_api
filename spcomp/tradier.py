import arrow
import requests
import os

from json import JSONDecodeError


class Tradier:
    class TradierError(Exception):
        pass

    class BadRequest(TradierError):
        pass

    class BadResponse(TradierError):
        pass

    def __init__(self, token, sandbox=True):
        self.token = token
        self.base_url = "https://%s.tradier.com/v1" % "sandbox" if sandbox else "api"

    def make_call(self, url, params):
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
