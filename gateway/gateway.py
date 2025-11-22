import requests
from flask import Flask

app = Flask(__name__)


@app.route('/search/<topic>', methods=['GET'])
def search_by_topic(topic):
    if topic is None:
        return 'No topic specified'
    response = requests.get(f"http://172.17.0.1:5050/query?topic={topic}")
    return response.json()


@app.route('/info/<item_number>', methods=['GET'])
def get_item_info(item_number):
    if item_number is None:
        return 'No item number specified'

    response = requests.get(f"http://172.17.0.1:5050/query?item_number={item_number}")
    return response.json()


@app.route('/purchase/<item_number>', methods=['POST'])
def purchase_item(item_number):
    if item_number is None:
        return 'No item number specified'

    response = requests.post(f"http://172.17.0.1:5060/purchase/{item_number}")
    return response.json()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
