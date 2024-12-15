from flask import Flask, jsonify, render_template, request
import requests
import uuid
import threading
import time
import os
from dotenv import load_dotenv
# Placeholder for web3 library functionality
# Since 'web3' is unavailable, mock its usage or suggest installation

class MockWeb3:
    def __init__(self, provider):
        self.provider = provider
        self.connected = True

    def is_connected(self):
        return self.connected

    def eth(self):
        class Eth:
            @staticmethod
            def get_transaction_count(address):
                return 0

            @staticmethod
            def send_raw_transaction(transaction):
                return b"mock_tx_hash"

            @staticmethod
            def wait_for_transaction_receipt(tx_hash):
                return {"contractAddress": "0xMockContractAddress"}

        return Eth()

    def to_wei(self, value, unit):
        return int(value * 10**18)

web3 = MockWeb3("mock_provider")

# Load environment variables
load_dotenv()

INFURA_URL = os.getenv('INFURA_URL')  # Infura Project URL
API_KEY = os.getenv('API_KEY')  # CoinMarketCap API Key
DEPLOYER_ADDRESS = os.getenv('DEPLOYER_ADDRESS')  # Ethereum Wallet Address
DEPLOYER_PRIVATE_KEY = os.getenv('DEPLOYER_PRIVATE_KEY')  # Wallet Private Key

# Initialize Flask app
app = Flask(__name__)

# Solidity contract template
CONTRACT_TEMPLATE = """
pragma solidity ^0.8.0;

contract MemeCoin {
    string public name;
    string public symbol;
    uint256 public totalSupply;
    address public owner;

    mapping(address => uint256) public balanceOf;

    constructor(string memory _name, string memory _symbol, uint256 _totalSupply) {
        name = _name;
        symbol = _symbol;
        totalSupply = _totalSupply;
        owner = msg.sender;
        balanceOf[msg.sender] = _totalSupply;
    }
}
"""

# Global variables for real-time prices and meme coins
crypto_prices = {"tether": 0, "solana": 0}
meme_coins = []

# Function to fetch real-time prices from CoinMarketCap
def fetch_realtime_prices():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"symbol": "USDT,SOL", "convert": "USD"}

    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                crypto_prices["tether"] = data["data"]["USDT"]["quote"]["USD"]["price"]
                crypto_prices["solana"] = data["data"]["SOL"]["quote"]["USD"]["price"]
            else:
                print("Error fetching prices: ", response.status_code)
        except Exception as e:
            print("Exception during price fetch: ", str(e))

        time.sleep(5)  # Fetch every 5 seconds

# Start a background thread for fetching real-time prices
price_thread = threading.Thread(target=fetch_realtime_prices, daemon=True)
price_thread.start()

# Function to deploy a smart contract
def deploy_contract(name, symbol, total_supply):
    transaction = {
        'chainId': 1,
        'gas': 2000000,
        'gasPrice': web3.to_wei(50, 'gwei'),
        'nonce': web3.eth().get_transaction_count(DEPLOYER_ADDRESS)
    }

    tx_hash = web3.eth().send_raw_transaction(transaction)
    tx_receipt = web3.eth().wait_for_transaction_receipt(tx_hash)
    return tx_receipt["contractAddress"]

# Function to fetch cryptocurrency data
def fetch_crypto_data():
    return crypto_prices

# Route to render the home page
@app.route('/')
def home():
    data = fetch_crypto_data()
    return render_template('index.html', data=data, meme_coins=meme_coins)

# API route for cryptocurrency data
@app.route('/api/crypto')
def api():
    data = fetch_crypto_data()
    return jsonify(data)

# Route to handle wallet connections
@app.route('/connect-wallet')
def connect_wallet():
    return render_template('connect_wallet.html')

# Route to create a new meme coin
@app.route('/create-meme-coin', methods=['GET', 'POST'])
def create_meme_coin():
    if request.method == 'POST':
        name = request.form.get('name')
        symbol = request.form.get('symbol')
        description = request.form.get('description')
        image = request.files.get('image')
        website = request.form.get('website')
        twitter = request.form.get('twitter')
        telegram = request.form.get('telegram')
        total_supply = int(request.form.get('total_supply'))

        # Deploy the contract on Ethereum
        contract_address = deploy_contract(name, symbol, total_supply)

        # Add the new meme coin to the global list
        meme_coin = {
            "name": name,
            "symbol": symbol,
            "description": description,
            "image": image.filename if image else None,
            "website": website,
            "twitter": twitter,
            "telegram": telegram,
            "total_supply": total_supply,
            "contract_address": contract_address,
            "platform": "Ethereum"
        }
        meme_coins.insert(0, meme_coin)
        if len(meme_coins) > 200:
            meme_coins.pop()

        return jsonify(meme_coin)

    return render_template('create_meme_coin.html')

# Route to display the latest meme coins (new address)
@app.route('/latest-meme-coins')
def latest_meme_coins():
    return render_template('새로운_코인.html', meme_coins=meme_coins)

# Legacy route for latest meme coins
@app.route('/새로운-코인')
def legacy_latest_meme_coins():
    return render_template('새로운_코인.html', meme_coins=meme_coins)

# Route to handle transactions
@app.route('/process-transaction', methods=['POST'])
def process_transaction():
    amount = float(request.form.get('amount'))
    sender_wallet = request.form.get('sender_wallet')
    receiver_wallet = request.form.get('receiver_wallet')

    # Calculate transaction fee (0.1% of the transaction amount)
    fee = amount * 0.001
    fee_wallet = "58rqTniEZzRNkrD2Mq4ur4thW7PNKW3DtquYfdwup6M5"
    final_amount = amount - fee

    transaction_status = {
        "sender_wallet": sender_wallet,
        "receiver_wallet": receiver_wallet,
        "amount_sent": final_amount,
        "fee_collected": fee,
        "fee_wallet": fee_wallet,
        "status": "Transaction processed successfully."
    }

    return jsonify(transaction_status)

if __name__ == '__main__':
    app.run(debug=True)
