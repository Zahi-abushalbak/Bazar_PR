import sqlite3

from flask import Flask, request, jsonify

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('catalog.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/query', methods=['GET'])
def query_catalog_items():
    params = request.args
    if len(params) == 0:
        return jsonify({"message": "No query string found in the request"}), 400
    elif params.keys().__contains__("topic"):
        conn = get_db_connection()
        topic = params["topic"]
        query_res = conn.cursor().execute("SELECT * FROM catalog_item WHERE topic = ?", (topic,))
        rows = query_res.fetchall()
        if rows is None or len(rows) == 0:
            return jsonify({"error": f"Something went wrong,make sure that topic {topic} exists"}), 404
        return jsonify([{"id": row["ItemNumber"], "title": row["Name"]} for row in rows])
    elif params.keys().__contains__("item_number"):
        conn = get_db_connection()
        item_number = params["item_number"]
        query_res = conn.cursor().execute("SELECT * FROM catalog_item WHERE itemnumber = ?", (item_number,))
        rows = query_res.fetchall()
        if rows is None or len(rows) == 0:
            return jsonify({"error": f"Something went wrong,make sure that item {item_number} exists"}), 404
        return jsonify({"title": rows[0]["Name"], "quantity": rows[0]["Count"], "price": rows[0]["Cost"]}), 200

    else:
        return jsonify({"message": "Invalid query parameters"}), 400


@app.route('/update', methods=['PATCH'])
def update_catalog_item():
    data = request.json
    if data is None or not data:
        return jsonify("Invalid request data")
    conn = get_db_connection()
    cursor = conn.cursor()
    if data.keys().__contains__("item_number") and (
            data.keys().__contains__("stock_count") or data.keys().__contains__("cost")):

        if data.keys().__contains__("stock_count"):
            stock_count = data["stock_count"]
            item_number = data["item_number"]

            cursor.execute("UPDATE catalog_item SET count=  count + ? WHERE itemnumber = ?",
                           (stock_count, item_number))
            if cursor.rowcount == 0:
                return jsonify({"error": f"Something went wrong,make sure that item {item_number} exists"}), 404
            conn.commit()
        if data.keys().__contains__("cost"):
            cost = data["cost"]
            item_number = data["item_number"]
            cursor.execute("UPDATE catalog_item SET cost = ? WHERE itemnumber = ?", (cost, item_number))
            if cursor.rowcount == 0:
                return jsonify({"error": f"Something went wrong,make sure that item {item_number} exists"}), 404
            conn.commit()
        return jsonify({"message": f"Updated record {item_number} successfully"}), 200
    else:
        return jsonify({"message": "Invalid request data or missing item number"}), 400


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
