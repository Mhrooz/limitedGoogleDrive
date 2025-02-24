import direct_counter_controller

from flask import Flask, request, jsonify
from flask_restful import Api

import threading

app = Flask(__name__)
api = Api(app)

policies = {}
policy_counter = 0

bandwidths_rule = {}
bandwidths_rule_counter = 0

instance = direct_counter_controller.ARPCache()
instance.start()

counter_thread = threading.Thread(
        target = instance.read_direct_counter,
        daemon=True
)

counter_thread.start()


def add_policy_to_switch(instance, policy):
    result = instance.install_policy_rule(policy["src_ip"], policy["dst_ip"], policy["dst_port"], policy["action"])
    return result

def delete_policy_from_switch(instance, policy):
    result = instance.delete_policy_rule(policy["src_ip"], policy["dst_ip"], policy["dst_port"], policy["action"])
    return result

@app.route('/bandwidth', methods=['POST'])
def add_bandwidth_rule():
    global bandwidths_rule_counter
    data = request.get_json()
    required_keys = ["src_ip", "dst_ip", "rates", "dst_port"]

    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields: src_ip, dst_ip, rates, dst_port"}), 400
    if len(data["rates"]) != 2:
        return jsonify({"error": "Rates field must be a list"}), 400

    for entry in bandwidths_rule.values():
        if entry["src_ip"] == data["src_ip"] and entry["dst_ip"] == data["dst_ip"] and entry["dst_port"] == data["dst_port"]:
            return jsonify({"error": "the rules is existed, please use PUT method to update the rule"}), 409
    
    path = instance.set_meter_rules(data["src_ip"], data["dst_ip"], data["rates"], data["dst_port"])
    if path == -1:
        return jsonify({"error": "the IP is not known in the network"}), 404

    results = {
            "id": bandwidths_rule_counter,
            "path": path,
            "src_ip": data["src_ip"],
            "dst_ip": data["dst_ip"],
            "rates": data["rates"],
            "dst_port": data["dst_port"]
    }

    bandwidths_rule[bandwidths_rule_counter] = results
    bandwidths_rule_counter += 1
    return jsonify(results), 201

@app.route('/bandwidth', methods=['GET'])
def get_bandwidth():
    return jsonify(list(bandwidths_rule.values())), 200


@app.route('/bandwidth', methods=['PUT'])
def upsert_bandwidth_rule():
    global bandwidths_rule_counter
    data = request.get_json()
    required_keys = ["src_ip", "dst_ip", "rates", "dst_port"]

    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields: src_ip, dst_ip, rates, dst_port"}), 400
    
    existing_bandwidth_rule = None
    entry_id = None
    for entry in bandwidths_rule.values():
        if entry["src_ip"] == data["src_ip"] and entry["dst_ip"] == data["dst_ip"] and entry["dst_port"] == data["dst_port"]:
            existing_bandwidth_rule = entry
            entry_id = entry["id"]
            break

    if existing_bandwidth_rule is not None:
        path = instance.set_meter_rules(data["src_ip"], data["dst_ip"], data["rates"], data["dst_port"])
        if path == -1:
            return jsonify({"error": "the IP is not known in the network"}), 404
        results = {
                "id": entry_id,
                "path": path,
                "src_ip": data["src_ip"],
                "dst_ip": data["dst_ip"],
                "rates": data["rates"],
                "dst_port": data["dst_port"]
        }
        bandwidths_rule[entry_id] = results
        return jsonify(results), 201
    else:
        path = instance.set_meter_rules(data["src_ip"], data["dst_ip"], data["rates"], data["dst_port"])
        if path == -1:
            return jsonify({"error": "the IP is not known in the network"}), 404
        results = {
                "id": bandwidths_rule_counter,
                "path": path,
                "src_ip": data["src_ip"],
                "dst_ip": data["dst_ip"],
                "rates": data["rates"],
                "dst_port": data["dst_port"]
        }
        bandwidths_rule[bandwidths_rule_counter] = results 
        bandwidths_rule_counter += 1
        return jsonify(results), 201

@app.route('/bandwidth/<int:bandwidths_rule_id>', methods=['DELETE'])
def del_bandwidth_rule(bandwidths_rule_id):
    if bandwidths_rule_id not in bandwidths_rule:
        return jsonify({"error": "bandwidths_rule does not exist"}), 404
    entry = bandwidths_rule[bandwidths_rule_id]
    return_code = instance.delete_bandwidth_rule(entry["src_ip"], entry["dst_ip"], entry["dst_port"])
    if return_code == -1:
        return jsonify({"error": "The IP address is not known in the network"}), 404
    del bandwidths_rule[bandwidths_rule_id]
    return jsonify({"message": "bandwidths_rule deleted"}), 201

@app.route('/policies', methods=['GET'])
def get_policies():
    return jsonify(list(policies.values())), 200

@app.route('/policies', methods=['POST'])
def add_policy():
    global policy_counter
    data = request.get_json()
    required_keys = ["src_ip", "dst_ip", "dst_port", "action"]

    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields: src_ip, dst_ip, action"}), 400

    if data["action"] not in ["allow", "deny"]:
        return jsonify({"error": "action filed must be allow or deny"}), 400

    policy = {
            "id": policy_counter,
            "src_ip": data["src_ip"],
            "dst_ip": data["dst_ip"],
            "dst_port": data["dst_port"],
            "action": data["action"]
    }

    for entry in policies:
        if entry["src_ip"] == policy["src_ip"] and entry["dst_ip"] == policy["dst_ip"] and entry["dst_port"] == policy["dst_port"]:
            return jsonify({"error": "the rules is existed, please use PUT method to update the rule"}), 409
    policies[policy_counter] = policy
    policy_counter += 1

    add_policy_to_switch(instance, policy)
    return jsonify(policy), 201

@app.route('/policies/<int:policy_id>', methods=['PUT'])
def update_policy_by_id(policy_id):
    data = request.get_json()
    if policy_id not in policies:
           return jsonify({"error": "policy does not exist"})
    print("=================start del==================================")
    result_code = delete_policy_from_switch(instance, policies[policy_id])
    if result_code == -1:
        return jsonify({"error": "The IP address is not known by the network"}), 404
    print("============================================================")

    policy = policies[policy_id]
    if "src_ip" in data:
        policy["src_ip"] = data["src_ip"]
    if "dst_ip" in data:
        policy["dst_ip"] = data["dst_ip"]
    if "dst_port" in data:
        policy["dst_port"] = data["dst_port"]
    if "action" in data:
        if data["action"] not in ["allow", "deny"]:
            return jsonify({"error": "action field must be allow or deny"}), 400
        policy["action"] = data["action"]
    policies[policy_id] = policy

    result_code = add_policy_to_switch(instance, policy)
    if result_code == -1:
        return jsonify({"error": "The IP address is not known by the network"}), 404
    return jsonify(policy), 200

@app.route('/policies', methods=['PUT'])
def upsert_policy():
    global policy_counter
    data = request.get_json()
    required_keys = ["src_ip", "dst_ip", "dst_port", "action"]

    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields: src_ip, dst_ip, action"}), 400

    if data["action"] not in ["allow", "deny"]:
        return jsonify({"error": "action filed must be allow or deny"})
    
    existing_policy = None
    for policy in policies.values():
        if policy["src_ip"] == data["src_ip"] and policy["dst_ip"] == data["dst_ip"] and policy["dst_port"] == data["dst_port"]:
            existing_policy = policy
            break

    if existing_policy is not None:
        result_code = delete_policy_from_switch(instance, existing_policy)
        if result_code == -1:
            return jsonify({"error": "The IP address is not known by the network"}), 404
        existing_policy["action"] = data["action"]
        result_code = add_policy_to_switch(instance, existing_policy)
        if result_code == -1:
            return jsonify({"error": "The IP address is not known by the network"}), 404
        return jsonify(existing_policy), 200
    else:
        policy = {
                "id": policy_counter,
                "src_ip": data["src_ip"],
                "dst_ip": data["dst_ip"],
                "dst_port": data["dst_port"],
                "action": data["action"],
        }
        policies[policy_counter] = policy
        policy_counter += 1
        result_code = add_policy_to_switch(instance, policy)
        if result_code == -1:
            return jsonify({"error": "The IP address is not known by the network"}), 404

        return jsonify(policy), 201
@app.route('/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    if policy_id not in policies:
        return jsonify({"error": "policy does not exist"}, 404)

    result_code = delete_policy_from_switch(instance, policies[policy_id])
    if result_code == -1:
        return jsonify({"error": "The IP address is not known by the network"}), 404
    del policies[policy_id]
    return jsonify({"message": "policies deleted"}), 200

if __name__ == '__main__':
    print("main thread!")
    app.run(host='0.0.0.0', port=8080, debug=True,
            threaded=True, use_reloader=False)


# try:
#     print("Starting REST API service...")
#     app.run(debug=True)
# except KeyboardInterrupt:
#     print("exit...")
# finally:
#     ShutdownAllSwitchConnections()

