from flask import Flask, request, jsonify
import ray
from ray_backend import core

ray.init(address='auto')
app = Flask(__name__)

@app.route("/api/double", methods=["POST"])
def double():
    data = request.get_json()
    future = core.slow_double.remote(data["value"])
    result = ray.get(future)
    return jsonify({"result": result})

@app.route("/api/sum", methods=["POST"])
def sum_values():
    data = request.get_json()
    future = core.slow_sum.remote(data["values"])
    result = ray.get(future)
    return jsonify({"result": result})
