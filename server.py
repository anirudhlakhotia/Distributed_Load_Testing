from flask import Flask, jsonify

app = Flask(__name__)

# Counter for requests and responses
request_counter = 0
response_counter = 0


@app.route("/ping", methods=["GET"])
def ping():
    global request_counter
    request_counter += 1
    return jsonify({"message": "pong"})


@app.route("/metrics", methods=["GET"])
def metrics():
    global request_counter, response_counter
    return jsonify(
        {"requests_sent": request_counter, "responses_sent": response_counter}
    )


if __name__ == "__main__":
    app.run(debug=True, port=5003)
