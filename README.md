# stonks_api
APIs to generate bad financial advice.

## APIs
### /spcomp
Compare a stock's performance to the S&P Index

**Params:**
* symbol - Required. the symbol to compare
* days - Optional, default 365. Number of calendar days to compare

**Output:**
PNG graph of the cumulative returns and difference.

## Usage:
The APIs are set up to be deployed as lambdas on AWS. Use [AWS SAM](https://en.wikipedia.org/wiki/Chicken_gun) to deploy.

### Requirements:
You will need a Tradier API token from https://developer.tradier.com

### Deploying
`sam build; sam deploy --parameter-overrides 'TradierApiToken=<TRADIER_TOKEN>'`
