import sqlite3
from flask import Flask, request, jsonify
import requests
from collections import OrderedDict

app = Flask(__name__)
# In-memory LRU Cache
class LRUCache:
    def __init__(self, capacity=5):
        self.cache = OrderedDict()  # OrderedDict to maintain insertion order
        self.capacity = capacity  # Max number of items the cache can hold

    def get(self, key):
        """Get item from cache."""
        if key in self.cache:
            self.cache.move_to_end(key)  # Move the accessed item to the end (most recently used)
            return self.cache[key]
        return None  # Return None if the key is not in cache

    def put(self, key, value):
        """Put item in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)  # Move to end if already in cache
        self.cache[key] = value
        if len(self.cache) > self.capacity:  # If cache exceeds capacity, remove the oldest item
            self.cache.popitem(last=False)

    def invalidate(self, key):
        """Invalidate (remove) an item from cache."""
        if key in self.cache:
            del self.cache[key]
# Initialize cache with a capacity of 10 items
cache = LRUCache(capacity=10)
# Load balancing state for catalog and order servers
catalog_replicas = ["http://localhost:5050", "http://localhost:5052"]
order_replicas = ["http://localhost:5061", "http://localhost:5062"]
catalog_index = 0
order_index = 0

# Load balancing function to get the next replica URL
def get_replica_url(replica_list):
    global catalog_index, order_index
    if replica_list == catalog_replicas:
        url = replica_list[catalog_index]
        catalog_index = (catalog_index + 1) % len(replica_list)
    else:
        url = replica_list[order_index]
        order_index = (order_index + 1) % len(replica_list)
    return url

# Route to query catalog items
@app.route('/query', methods=['GET'])
def query_catalog_items():
    params = request.args
    if len(params) == 0:
        return jsonify({"message": "No query string found in the request"}), 400

    # Check if the item is already in cache
    if "item_number" in params:
        item_number = params["item_number"]
        cached_result = cache.get(item_number)
        if cached_result:
            print(f"Cache hit for item_number {item_number}")
            return jsonify(cached_result)

    # If not in cache, fetch from catalog replica
    replica_url = get_replica_url(catalog_replicas)
    response = requests.get(replica_url + "/query", params=params)
    if response.ok:
        result = response.json()
        if "item_number" in params:
            cache.put(params["item_number"], result)  # Save the result to cache
        return jsonify(result)
    return jsonify({"error": "Request to catalog server failed"}), response.status_code

# Route to update catalog item and invalidate cache
@app.route('/update', methods=['PATCH'])
def update_catalog_item():
    data = request.json
    if not data or "item_number" not in data:
        return jsonify({"message": "Invalid request data or missing item_number"}), 400

    # Invalidate the cache for the updated item
    item_number = data["item_number"]
    cache.invalidate(item_number)

    # Forward the update request to the catalog replica
    replica_url = get_replica_url(catalog_replicas)
    response = requests.patch(replica_url + "/update", json=data)
    if response.ok:
        return jsonify(response.json()), response.status_code
    return jsonify({"error": "Failed to update item"}), response.status_code

# Route to purchase an item
@app.route('/purchase/<item_number>', methods=['POST'])
def purchase_item(item_number):
    # Forward the purchase request to one of the order replicas
    replica_url = get_replica_url(order_replicas)
    response = requests.post(replica_url + f"/purchase/{item_number}")
    if response.ok:
        return jsonify(response.json()), response.status_code
    return jsonify({"error": "Purchase failed"}), response.status_code

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
