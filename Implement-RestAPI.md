# Implementation of RESTful API for Network Control

This implementation is based on the [`ARPcache`](https://github.com/mnm-team/p4-sdn/tree/main/ARPcache) project, which includes both the **data plane** (P4 code) and the **control plane** (Python code). The system supports two main functionalities:

1. **Allow/Deny Policy**: Controls whether traffic between specific IPs and ports is allowed or denied.
2. **Bandwidth Control**: Regulates traffic bandwidth using P4 meters.

---

## **Data Plane (P4 Code)**

The data plane is implemented in P4 and handles packet processing, including policy enforcement and bandwidth control.

---

### **1. Allow/Deny Policy**

The `policy_table` is used to enforce allow/deny rules based on source IP, destination IP, and destination port. The default action is `NoAction`, and packets are dropped if they match a deny rule.

```p4
table policy_table {
    key = {
        hdr.ipv4.srcAddr: exact;  // Source IP
        hdr.ipv4.dstAddr: exact;  // Destination IP
        meta.meta.tcp_dp: exact;  // Destination port
    }
    actions = {
        NoAction;
        drop_packet;  // Drop packets for deny rules
    }
    size = 256;  // Table size
    default_action = NoAction;
}
```

---

### **2. Bandwidth Control**

Bandwidth control is implemented using P4 meters. The system measures traffic rates and marks packets as **green**, **yellow**, or **red** based on the configured **CIR (Committed Information Rate)** and **PIR (Peak Information Rate)**.

#### **Meter Definition**

A direct meter is defined to measure traffic in bytes.

```p4
direct_meter<bit<32>>(MeterType.bytes) my_meter;
```

#### **Metadata for Metering**

A metadata field `meter_tag` is added to mark packets based on their traffic rate.

```p4
struct metadata {
    @name(".meta")
    meta_t  meta;
    bit<32> meter_tag;  // Used to mark packets (green, yellow, red)
}
```

#### **Meter Actions**

The `m_action` reads the meter and marks packets:

- **Green**: Packet rate is below CIR.
- **Yellow**: Packet rate is between CIR and PIR.
- **Red**: Packet rate exceeds PIR.

```p4
action m_action() {
    my_meter.read(meta.meter_tag);  // Read meter and mark packets
}

table m_read {
    key = {
        meta.meta.ipv4_sa: exact;  // Source IP
        meta.meta.ipv4_da: exact;  // Destination IP
        meta.meta.tcp_dp: exact;   // Destination port
    }
    actions = {
        NoAction;
        m_action;  // Apply meter action
    }
    size = 256;  // Table size
    meters = my_meter;  // Associate with the meter
    default_action = NoAction;
}
```

#### **Filtering Red Packets**

The `m_filter` table drops packets marked as **red**.

```p4
table m_filter {
    key = {
        meta.meter_tag: exact;  // Packet color (green, yellow, red)
    }
    actions = {
        drop_packet;  // Drop red packets
        NoAction;
    }
    default_action = NoAction;
    counters = drop_counter;  // Track dropped packets
    size = 16;
}
```

#### **Packet Processing Logic**

The `apply` block processes packets in the following order:

1. Measure traffic and mark packets (green, yellow, or red).
2. Forward packets based on source and destination MAC addresses.
3. Drop packets if they match a deny policy.
4. Drop packets marked as **red**.

```p4
apply {
    if (hdr.packet_out.isValid()) {
        standard_metadata.egress_spec = hdr.packet_out.egress_port;
        hdr.packet_out.setInvalid();
        exit;
    }
    m_read.apply();  // Measure traffic and mark packets
    if (smac.apply().hit) {
        dmac.apply();  // Forward packets
    }
    policy_table.apply();  // Apply allow/deny policy
    m_filter.apply();  // Drop red packets
}
```

---

## **Control Plane (Python Code)**

The control plane is implemented using **Flask**, a lightweight Python web framework. It provides RESTful APIs to manage policies and bandwidth rules.

---

### **1. Bandwidth Control APIs**

These APIs allow adding, retrieving, updating, and deleting bandwidth control rules.

```python
@app.route('/bandwidth', methods=['POST'])
def add_bandwidth_rule():
    ...

@app.route('/bandwidth', methods=['GET'])
def get_bandwidth_rule():
    ...

@app.route('/bandwidth/<int:bandwidths_rule_id>', methods=['DELETE'])
def del_bandwidth_rule(bandwidths_rule_id):
    ...

@app.route('/bandwidth', methods=['PUT'])
def upsert_bandwidth_rule():
    ...
```

---

### **2. Policy Management APIs**

These APIs allow adding, retrieving, updating, and deleting allow/deny policies.

```python
@app.route('/policy', methods=['POST'])
def add_policy():
    ...

@app.route('/policy', methods=['GET'])
def get_policy():
    ...

@app.route('/policy/<int:policy_id>', methods=['DELETE'])
def del_policy(policy_id):
    ...

@app.route('/policy', methods=['PUT'])
def upsert_policy():
    ...
```

---

### **3. State Management**

To optimize resource usage, a Python dictionary is used to maintain the state of policies and bandwidth rules. This avoids redundant lookups for invalid parameters.

---

## **Design Considerations**

Since the system is designed for **NAS** especially **WebDAV** servers, which typically use fixed ports, we implemented **exact port matching** instead of port ranges. This simplifies the design and aligns with the use case.

The RESTful APIs document is at https://github.com/Mhrooz/limitedGoogleDrive/blob/network-control/RESTful-APIs.md 
