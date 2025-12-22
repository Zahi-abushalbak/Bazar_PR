import sqlite3

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('catalog.db')
    conn.row_factory = sqlite3.Row
    return conn


# Simulate replication
other_replicas = ["http://localhost:5052"]  # Adjust for other replica instances

@app.route('/query', methods=['GET'])
def query_catalog_items():
    params = request.args
    if "item_number" in params:
        conn = get_db_connection()
        item_number = params["item_number"]
        query_res = conn.execute("SELECT * FROM catalog_item WHERE itemnumber = ?", (item_number,))
        row = query_res.fetchone()
        conn.close()
        if row:
            return jsonify({"title": row["Name"], "quantity": row["Count"], "price": row["Cost"]})
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"error": "Invalid query parameters"}), 400


@app.route('/update', methods=['PATCH'])
def update_catalog_item():
    data = request.json
    if not data or "item_number" not in data:
        return jsonify({"error": "Invalid data"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    item_number = data["item_number"]

    if "stock_count" in data:
        cursor.execute("UPDATE catalog_item SET count = count + ? WHERE itemnumber = ?",
                       (data["stock_count"], item_number))

    if "cost" in data:
        cursor.execute("UPDATE catalog_item SET cost = ? WHERE itemnumber = ?",
                       (data["cost"], item_number))

    if cursor.rowcount > 0:
        conn.commit()
        conn.close()

        # Propagate changes to replicas
        for replica in other_replicas:
            try:
                requests.patch(replica + "/update", json=data)
            except requests.RequestException as e:
                print(f"Failed to update replica {replica}: {e}")

        return jsonify({"message": f"Updated record {item_number} successfully"}), 200

    conn.close()
    return jsonify({"error": f"Item {item_number} not found"}), 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5050)
