/*
__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'
__version__ = '1.0' 202401
*/

/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//compile the packetinout.p4 file by: p4c-bm2-ss --p4v 16 --p4runtime-files build/packetinout.p4info.txt -o build/packetinout.json packetinout.p4

#define CPU_PORT 255
// then start p4_switch by: sudo simple_switch_grpc -i 1@eth1 -i 2@eth2 -i 3@eth3 --pcap pcaps --nanolog ipc:///tmp/s1-log.ipc --device-id 1 build/packetout.json --log-console --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255  (the cpu-port in the start command must be the same, as it is the parse value in the function MyParser below)

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_ARP = 0x806;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

struct meta_t {
    bit<32> ipv4_sa;
    bit<32> ipv4_da;
    bit<16> tcp_sp;
    bit<16> tcp_dp;
    bit<32> nhop_ipv4;
    bit<32> if_ipv4_addr;
    bit<48> if_mac_addr;
    bit<1>  is_ext_if;
    bit<16> l4Length; // Layer 4's length
    bit<8>  if_index;
}

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

//ref: http://csie.nqu.edu.tw/smallko/sdn/LBP4.htm
header arp_t {
    bit<16> htype;
    bit<16> ptype;
    bit<8>  hlen;
    bit<8>  plen;
    bit<16> opcode;
    bit<48> hwSrcAddr;
    bit<32> protoSrcAddr;
    bit<48> hwDstAddr;
    bit<32> protoDstAddr;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<8>  flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length_;
    bit<16> checksum;
}

/*
header user_meta_t{
    bit<1> reinject;
    bit<2> user_type;
}
*/

struct metadata {
    /* empty */
    @name(".meta")
    meta_t  meta;
    bit<32> meter_tag;
}

@controller_header("packet_in")
header packet_in_header_t {
    bit<9>  ingress_port;
    bit<7>      _pad;
//source: https://github.com/opennetworkinglab/ngsdn-tutorial/blob/advanced/solution/p4src/main.p4
}

@controller_header("packet_out")
header packet_out_header_t {
    bit<9> egress_port; // egress_port is 9-bit wide
    //bit<16> egress_port;
    bit<7>      _pad; //padding
//source: https://github.com/opennetworkinglab/ngsdn-tutorial/blob/advanced/solution/p4src/main.p4
}


struct headers {
    //user_meta_t user_meta;
    packet_out_header_t packet_out;
    packet_in_header_t packet_in;
    @name(".ethernet")
    ethernet_t   ethernet;
    @name(".arp")
    arp_t arp;
    @name(".ipv4")
    ipv4_t     ipv4;
    @name(".tcp")
    tcp_t      tcp;
    @name(".udp")
    udp_t      udp;

}


/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        //transition parse_ethernet;
        transition select(standard_metadata.ingress_port) {
            CPU_PORT: parse_packet_out;
            default: parse_ethernet;
        }
    }

    state parse_packet_out {
        packet.extract(hdr.packet_out);
        transition parse_ethernet;
    }


    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_ARP: parse_arp;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    @name(".parse_arp") state parse_arp {
        packet.extract(hdr.arp);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.meta.ipv4_sa = hdr.ipv4.srcAddr;
        meta.meta.ipv4_da = hdr.ipv4.dstAddr;
        meta.meta.l4Length = hdr.ipv4.totalLen - 16w20;
        transition select(hdr.ipv4.protocol) {
            8w6: parse_tcp;
            8w17: parse_udp;
            default: accept;
        }
        //transition accept;
    }

    @name(".parse_tcp") state parse_tcp {
        packet.extract(hdr.tcp);
        meta.meta.tcp_sp = hdr.tcp.srcPort;
        meta.meta.tcp_dp = hdr.tcp.dstPort;
        transition accept;
    }
    @name(".parse_udp") state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }
}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    direct_counter(CounterType.packets_and_bytes) rule_counter;
    direct_counter(CounterType.packets_and_bytes) drop_counter;

    direct_meter<bit<32>>(MeterType.bytes) my_meter;
    bit<9>drop_port = 0;
    action send_to_cpu() {
        standard_metadata.egress_spec = CPU_PORT;
    }

    action m_action(){
        my_meter.read(meta.meter_tag);
    }

    action queue_packet(){
        send_to_cpu();
    }

    action forward(bit<9> egress_port) {
        standard_metadata.egress_spec = egress_port;
    }

    action drop_packet(){
        standard_metadata.egress_spec = drop_port;
    }

    table m_read{
        key = {
            meta.meta.ipv4_sa: exact;
            meta.meta.ipv4_da: exact;
            meta.meta.tcp_dp: exact;
        }

        actions = {
            NoAction;
            m_action;
        }
        size = 256;
        meters = my_meter;
        default_action = NoAction;
    }
    table smac {
        key = {
            hdr.ethernet.srcAddr: exact;
        }
        actions = {
            send_to_cpu;
            NoAction;
        }
        size = 256;
        default_action = send_to_cpu;
    }

    table dmac {
        key = {
            hdr.ethernet.dstAddr: exact;
        }
        actions = {
            forward;
            send_to_cpu;
            NoAction;
        }
        size = 256;
        counters = rule_counter;
        default_action = send_to_cpu;
    }

    table policy_table{
        key = {
            hdr.ipv4.srcAddr: exact;
            hdr.ipv4.dstAddr: exact;
            meta.meta.tcp_dp: exact;
        }
        actions = {
            NoAction;
            drop_packet;
        }
        size = 256;
        default_action = NoAction;
    }
    table m_filter{
        key = {
            meta.meter_tag: exact;
        }
        actions = {
            drop_packet;
            NoAction;
        }
        default_action = NoAction;
        counters = drop_counter;
        size = 16;
    }
    apply {
        if (hdr.packet_out.isValid()) {
           standard_metadata.egress_spec = hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
            exit;
        }
        m_read.apply();
        if (smac.apply().hit){
            dmac.apply();
        } 
        policy_table.apply();
        m_filter.apply();
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    apply { 
        if (standard_metadata.egress_port == CPU_PORT) {
            // Implement logic such that if the packet is to be forwarded to the
            // CPU port, e.g., if in ingress we matched on the ACL table with
            // action send/clone_to_cpu...
            // 1. Set cpu_in header as valid
            // 2. Set the cpu_in.ingress_port field to the original packet's
            //    ingress port (standard_metadata.ingress_port).
            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;
            exit;
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
        //update_checksum_with_payload(true, { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 8w0, hdr.ipv4.protocol, meta.meta.l4Length, hdr.tcp.srcPort, hdr.tcp.dstPort, hdr.tcp.seqNo, hdr.tcp.ackNo, hdr.tcp.dataOffset, hdr.tcp.res, hdr.tcp.flags, hdr.tcp.window, hdr.tcp.urgentPtr }, hdr.tcp.checksum, HashAlgorithm.csum16);
        update_checksum_with_payload(hdr.tcp.isValid(), { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 8w0, hdr.ipv4.protocol, meta.meta.l4Length, hdr.tcp.srcPort, hdr.tcp.dstPort, hdr.tcp.seqNo, hdr.tcp.ackNo, hdr.tcp.dataOffset, hdr.tcp.res, hdr.tcp.flags, hdr.tcp.window, hdr.tcp.urgentPtr }, hdr.tcp.checksum, HashAlgorithm.csum16);
        update_checksum_with_payload(hdr.udp.isValid(), { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 8w0, hdr.ipv4.protocol, meta.meta.l4Length, hdr.udp.srcPort, hdr.udp.dstPort, hdr.udp.length_ }, hdr.udp.checksum, HashAlgorithm.csum16);
    }
}


/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        //parsed headers have to be added again into the packet.
        packet.emit(hdr.packet_in);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.arp);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;

