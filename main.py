import direct_counter_controller

from flask import Flask, request, jsonify
from flask_restful import Api

import threading

app = Flask(__name__)
api = Api(app)

policies = {}
policy_counter = 0

instance = direct_counter_controller.ARPCache()
instance.start()

counter_thread = threading.Thread(
        target = instance.read_direct_counter,
        daemon=True
)

counter_thread.start()

meter_thread = threading.Thread(
        target = instance.read_meter_stats,
        args = (1, "smac"),
        daemon=True
)

meter_thread.start()

# instance.read_direct_counter()

def add_policy_to_switch(instance, policy):
    instance.install_policy_rule(policy["src_ip"], policy["dst_ip"], policy["action"])

def delete_policy_from_switch(instance, policy):
    instance.delete_policy_rule(policy["src_ip"], policy["dst_ip"], policy["action"])

@app.route('/policies', methods=['GET'])
def get_policies():
    return jsonify(list(policies.values())), 200

@app.route('/policies', methods=['POST'])
def add_policy():
    global policy_counter
    data = request.get_json()
    required_keys = ["src_ip", "dst_ip", "action"]

    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields: src_ip, dst_ip, action"}), 400

    if data["action"] not in ["allow", "deny"]:
        return jsonify({"error": "action filed must be allow or deny"})
    
    policy = {
            "id": policy_counter,
            "src_ip": data["src_ip"],
            "dst_ip": data["dst_ip"],
            "action": data["action"]
    }
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
    delete_policy_from_switch(instance, policies[policy_id])
    print("============================================================")

    policy = policies[policy_id]
    if "src_ip" in data:
        policy["src_ip"] = data["src_ip"]
    if "dst_ip" in data:
        policy["dst_ip"] = data["dst_ip"]
    if "action" in data:
        if data["action"] not in ["allow", "deny"]:
            return jsonify({"error": "action field must be allow or deny"}), 400
        policy["action"] = data["action"]
    policies[policy_id] = policy

    add_policy_to_switch(instance, policy)
    return jsonify(policy), 200

@app.route('/policies', methods=['PUT'])
def upsert_policy():
    global policy_counter
    data = request.get_json()
    required_keys = ["src_ip", "dst_ip", "action"]

    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields: src_ip, dst_ip, action"}), 400

    if data["action"] not in ["allow", "deny"]:
        return jsonify({"error": "action filed must be allow or deny"})
    
    existing_policy = None
    for policy in policies.values():
        if policy["src_ip"] == data["src_ip"] and policy["dst_ip"] == data["dst_ip"]:
            existing_policy = policy
            break

    if existing_policy is not None:
        delete_policy_from_switch(instance, existing_policy)
        existing_policy["action"] = data["action"]
        add_policy_to_switch(instance, existing_policy)
        return jsonify(existing_policy), 200
    else:
        policy = {
                "id": policy_counter,
                "src_ip": data["src_ip"],
                "dst_ip": data["dst_ip"],
                "action": data["action"],
        }
        policies[policy_counter] = policy
        policy_counter += 1
        add_policy_to_switch(instance, policy)

        return jsonify(policy), 201
@app.route('/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    if policy_id not in policies:
        return jsonify({"error": "policy does not exist"}, 404)

    delete_policy_from_switch(instance, policies[policy_id])
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

