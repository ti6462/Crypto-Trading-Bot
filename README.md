# Crypto Trading Bot

Crypto Trading Bot is a Coinbase Pro (formerly GDAX) trading bot written in Python that uses a series of inputs based on
simple moving averages with the ability to add complexity (triggers, thresholds, candle size, etc).  This project and 
Python are my hobby and as such are under constant development. There may be bugs in the code that could cost you money!


### Prerequisites

To get started you should have the following:
- Coinbase Pro Account
- API Key, secret and password with permissions to view and trade your account.  Transfer permissions not required.
- Money to trade!
 

### Installing

1. Clone the repository.
2. Install necessary PyPI packages
   - gdax
   - yaml
   - numpy
   - pandas
  
2. Create a credentials file: /configuration/credentials/gdax_api_creds.txt
3. Enter Exchange API information into the newly created file, mimicking the example.yaml file.
4. Create trading pair configuration file: /configuration/trading_pairs/'ETH-USD.yaml'. The file name must exactly match
the trading pair you wish the trade.




This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

### Acknowledgments

* Chris Campbell for developing the algo.
* Daniel Paquin for his Coinbase Pro repo.

