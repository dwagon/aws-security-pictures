#!/usr/bin/env python
import os
import json
from pprint import pprint
from collections import defaultdict


def get_load_balancers(lookup_filter=''):
    lookup_cmd = "aws elb describe-load-balancers %s" % lookup_filter
    raw_load_balancers = os.popen(lookup_cmd).read()
    load_balancers = json.loads(raw_load_balancers)
    return load_balancers['LoadBalancerDescriptions']


def get_ec2_instances(lookup_filter=''):
    lookup_cmd = "aws ec2 describe-instances %s" % lookup_filter
    raw_ec2_instances = os.popen(lookup_cmd).read()
    ec2_instances = json.loads(raw_ec2_instances)
    return ec2_instances['Reservations']


def get_security_groups(lookup_filter=''):
    if isinstance(lookup_filter, list):
        r = []
        for l in lookup_filter:
            s = get_security_groups("--group-ids %s" % l)
            r += s
        return r

    lookup_cmd = "aws ec2 describe-security-groups %s" % lookup_filter
    raw_security_groups = os.popen(lookup_cmd).read()
    security_groups = json.loads(raw_security_groups)
    return security_groups['SecurityGroups']


def get_routetables(lookup_filter=''):
    lookup_cmd = "aws ec2 describe-route-tables %s" % lookup_filter
    raw_security_groups = os.popen(lookup_cmd).read()
    security_groups = json.loads(raw_security_groups)
    return security_groups['RouteTables']


def get_network_acl(lookup_filter=''):
    if isinstance(lookup_filter, list):
        r = []
        for l in lookup_filter:
            s = get_network_acl("--network-acl-ids %s" % l)
            r += s
        return r
    lookup_cmd = "aws ec2 describe-network-acls %s" % lookup_filter
    raw_security_groups = os.popen(lookup_cmd).read()
    security_groups = json.loads(raw_security_groups)
    return security_groups['NetworkAcls']


def get_elb_rules(_id):
    elb = get_load_balancers("--load-balancer-names %s" % _id)[0]
    elb_node = """
    "%s_rules" [ style = "filled" penwidth = 0 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<
    <table border="1" cellborder="0" cellpadding="3" bgcolor="white">
    <tr>
    <td bgcolor="black" align="center" colspan="2"><font color="white">%s</font></td>
    </tr>
    <tr>
    <td bgcolor="black" align="center"><font color="white">source</font></td>
    <td bgcolor="black" align="center"><font color="white">desitination</font></td>
    </tr>
    """ % (_id, _id)
    for l in elb['ListenerDescriptions']:
        _in = l['Listener']['LoadBalancerPort']
        _out = l['Listener']['InstancePort']
        rule_html = """
        <tr>
        <td align="right">%s</td>
        <td align="right">%s</td>
        </tr>
        """ % ( _in, _out)
        elb_node += rule_html

    elb_node += "</table>>];"
    print elb_node


def get_rtb_rules(_id):
    rtb = get_routetables("--route-table-ids %s" % _id[0])[0]

    rtb_node = """
"%s_rules" [ style = "filled" penwidth = 0 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<<table border="1" cellborder="0" cellpadding="3" bgcolor="white">
  <tr>
      <td bgcolor="black" align="center"><font color="white">source</font></td>
      <td bgcolor="black" align="center"><font color="white">desitination</font></td>
  </tr>
    """ % _id[0]

    for route in rtb['Routes']:
        rule_html = """
        <tr>
        <td align="right">%s</td>
        <td align="right">%s</td>
        </tr>
        """ % ( route["GatewayId"], route["DestinationCidrBlock"])
        rtb_node += rule_html

    rtb_node += "</table>>];"
    print rtb_node

def get_sg_rules(_id, direction=None):

    _id = ' '.join(_id)

    sg_list = get_security_groups("--group-ids %s" % _id)

    for sg in sg_list:

        ingress_node = """
        "%s_in_rules" [ style = "filled" penwidth = 0 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<<table border="1" cellborder="0" cellpadding="3" bgcolor="white">
        <tr>
          <td bgcolor="black" align="center"><font color="white">CIDR</font></td> 
          <td bgcolor="black" align="center"><font color="white">Ports</font></td>
        </tr>
    """ % sg['GroupId']

        egress_node = """
        "%s_out_rules" [ style = "filled" penwidth = 0 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<<table border="1" cellborder="0" cellpadding="3" bgcolor="white">
        <tr>
          <td bgcolor="black" align="center"><font color="white">CIDR</font></td>
          <td bgcolor="black" align="center"><font color="white">Ports</font></td>
        </tr>
    """ % sg['GroupId']

        for i in sg['IpPermissions']:
            portrange = "-1"
            if 'FromPort' in i:
                portrange = "%s-%s" % (i['FromPort'], i['ToPort'])
            ips = [x['CidrIp'] for x in i['IpRanges']]
            if not ips:
                ips = [x['GroupId'] for x in i['UserIdGroupPairs']]
            ips = "<Br />".join(ips)

            rule_html = """
            <tr>
            <td bgcolor="green" align="left">%s</td>
            <td align="right">%s</td>
            </tr>
            """ % (ips, portrange)
            ingress_node += rule_html

        for i in sg['IpPermissionsEgress']:
            portrange = "-1"
            if 'FromPort' in i:
                portrange = "%s-%s" % (i['FromPort'], i['ToPort'])
            ips = [x['CidrIp'] for x in i['IpRanges']]
            if not ips:
                ips = [x['GroupId'] for x in i['UserIdGroupPairs']]
            ips = "<Br />".join(ips)
            rule_html = """
            <tr>
            <td bgcolor="green" align="left">%s</td>
            <td align="right">%s</td>
            </tr>
            """ % (ips, portrange)
            egress_node += rule_html
        ingress_node += "</table>>];"
        egress_node += "</table>>];"

        if direction == "ingress":
            print ingress_node
        elif direction == "egress":
            print egress_node
        else:
            print ingress_node
            print egress_node


def get_nacl_rules(_id, direction=None):
    if isinstance(_id, list):
        acl_list = get_network_acl(_id)
    else:
        acl_list = get_network_acl("--network-acl-ids %s" % _id)

    ingress = []
    egress = []

    for acl in acl_list:
        ingress_node = """
"%s_in_rules" [ style = "filled" penwidth = 0 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<<table border="1" cellborder="0" cellpadding="3" bgcolor="white">
  <tr>
      <td bgcolor="black" align="center"><font color="white">Rule #</font></td>
      <td bgcolor="black" align="center"><font color="white">CIDR</font></td>
      <td bgcolor="black" align="center"><font color="white">Ports</font></td>
  </tr>
    """ % _id[0]

        egress_node = """

"%s_out_rules" [ style = "filled" penwidth = 0 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<<table border="1" cellborder="0" cellpadding="3" bgcolor="white">
  <tr>
      <td bgcolor="black" align="center"><font color="white">Rule #</font></td>
      <td bgcolor="black" align="center"><font color="white">CIDR</font></td>
      <td bgcolor="black" align="center"><font color="white">Ports</font></td>
  </tr>
""" % _id[0]
        for e in acl['Entries']:
            portrange = "-1"
            if "PortRange" in e:
                portrange = "%d-%d" %(e['PortRange']['From'], e['PortRange']['To'])
            rule = "%s %s %s %s" % (e['RuleNumber'], e['RuleAction'], e['CidrBlock'], portrange)
            rule_color = "red"
            if e['RuleAction'] == "allow":
                rule_color = "green"
            rule_html = """
  <tr>
      <td bgcolor="%s" align="left">%s</td>
      <td align="right">%s</td>
      <td align="right">%s</td>
   </tr>
""" % ( rule_color, e['RuleNumber'], e['CidrBlock'], portrange)

            if e['Egress']:
                egress.append(rule)
                egress_node += rule_html
            else:
                ingress.append(rule)
                ingress_node += rule_html

        egress_node += "</table>>];"
        ingress_node += "</table>>];"

        if direction == "ingress":
            print ingress_node
        elif direction == "egress":
            print egress_node
        else:
            print ingress_node
            print egress_node

    return ingress_node, egress_node


def main():
    load_balancers = get_load_balancers()

    layer_1 = defaultdict(list)
    layer_2 = defaultdict(list)

    for elb in load_balancers:
        if not elb['Scheme'] == 'internet-facing':
            continue
        subnets = elb['Subnets']
        instances = [x['InstanceId'] for x in elb['Instances']]
        securitygroups = elb['SecurityGroups']
        mappings = []
        for l in elb['ListenerDescriptions']:
            m = "%s:%s" % (l['Listener']['LoadBalancerPort'], l['Listener']['InstancePort'])
            mappings.append(m)

        elbname = elb['LoadBalancerName']

        layer_1['subnets'] = subnets
        layer_1['securitygroups'] = securitygroups
        layer_1['mappings'] = mappings
        layer_1['endpoint'] = elbname
        subnets_csv = ",".join(subnets)

        # Route table
        routetables = get_routetables("--filters Name=association.subnet-id,Values=%s" % subnets_csv)
        layer_1['routetable_raw'] = routetables
        layer_1['routetable'] = [x['RouteTableId'] for x in routetables]

        # Network ACL
        nacl = get_network_acl("--filters Name=association.subnet-id,Values=%s" % subnets_csv)
        layer_1['nacl_raw'] = nacl
        layer_1['nacl'] = [x['NetworkAclId'] for x in nacl]
        
        # Instances
        layer_2['instances'] = instances
        break

    instance_filter = "--instance-ids %s" % ",".join(layer_2['instances'])
    instances = get_ec2_instances(instance_filter)

    for i in instances:
        i = i['Instances'][0]
        #pprint(i)
        securitygroups = [x['GroupId'] for x in i['SecurityGroups']]
        subnets = [i['SubnetId']]

        layer_2['subnets'] += subnets
        layer_2['securitygroups'] += securitygroups
        layer_2['instances'] = i['InstanceId']
        layer_2['instances_raw'] = instances

        # Network ACL
        subnets_csv = ",".join(subnets)
        nacl = get_network_acl("--filters Name=association.subnet-id,Values=%s" % subnets_csv)
        layer_2['nacl_raw'] = nacl
        layer_2['nacl'] = [x['NetworkAclId'] for x in nacl]

    rule_map = [
        "%s_in"  % "_".join(layer_1["nacl"]),
        #"%s_in"  % "_".join(layer_1["securitygroups"]),
        "%s"     % layer_1["endpoint"],
        #"%s_out" % "_".join(layer_1["securitygroups"]),
        "%s_out" % "_".join(layer_1["nacl"]),
    ]

    print "digraph g {"
    print "subgraph cluster_1 {"
    #print '"l1_%s_in" -> "l1_%s_in";' % ("_".join(layer_1["nacl"]),
    #                                 "_".join(layer_1["securitygroups"]))

    for sg in layer_1["securitygroups"]:
        print '"l1_%s_in" -> "l1_%s_in";' % ("_".join(layer_1["nacl"]), sg)
        print '"l1_%s_in" -> "l1_%s";' % (sg, layer_1["endpoint"])
        rule_map.append("%s_in" % sg)
        rule_map.append("%s_out" % sg)

        print '"l1_%s" -> "l1_%s_out";' % (layer_1["endpoint"], sg)
        print '"l1_%s_out" -> "l1_%s_out";' % (sg, "_".join(layer_1["nacl"]))

    print '"l1_%s";' % layer_1["endpoint"]



    for item in rule_map:
        print '"l1_%s" -> "%s_rules";' % (item, item)
        print '{rank=same; "l1_%s" "%s_rules"};' % (item, item)
    
    print "label = \"public\""
    print "}"


    print "subgraph cluster_2 {"
    print '"l1_%s_out" -> "%s";' % (
        "_".join(layer_1["nacl"]), 
        "_".join(layer_1["routetable"]),
    )
    print '"%s" -> "%s_rules";' % (
        "_".join(layer_1["routetable"]), 
        "_".join(layer_1["routetable"])
    )
    print '{rank=same; "%s" "%s_rules"};' % (
        "_".join(layer_1["routetable"]), 
        "_".join(layer_1["routetable"])
    )

    print "}"

    print "subgraph cluster_3 {"

    print '"%s" -> "l2_%s_in";' % (
        "_".join(layer_1["routetable"]),
        "_".join(layer_2["nacl"]), 
    )

    print 
    print 
    print 
    print 

    rule_map = [
        '%s_in'  % '_'.join(layer_2['nacl']),
        #'%s'     % layer_2['instances'],
        '%s_out' % '_'.join(layer_2['nacl']),
    ]

    #print '"l2_%s_in" -> "l2_%s_in";' % ('_'.join(layer_2['nacl']),
    #                                 '_'.join(layer_2['securitygroups']))
    #print '"l2_%s_in" -> "l2_%s";' % ('_'.join(layer_2['securitygroups']),
    #                              layer_2['instances'])
    print '"l2_%s";' % layer_2['instances']

    #print '"l2_%s" -> "l2_%s_out";' % (
    #    layer_2['instances'],
    #    '_'.join(layer_2['securitygroups']),
    #)
    #print '"l2_%s_out" -> "l2_%s_out";' % (
    #    '_'.join(layer_2['securitygroups']),
    #    '_'.join(layer_2['nacl']), 
    #)


    for sg in layer_2["securitygroups"]:
        print '"l2_%s_in" -> "l2_%s_in";' % ("_".join(layer_2["nacl"]), sg)
        print '"l2_%s_in" -> "l2_%s";' % (sg, layer_2["instances"])
        rule_map.append("%s_in" % sg)
        #rule_map.append("%s_out" % sg)

        #print '"l2_%s" -> "l2_%s_out";' % (layer_2["instances"], sg)
        #print '"l2_%s_out" -> "l2_%s_out";' % (sg, "_".join(layer_2["nacl"]))

    print '"l1_%s";' % layer_2["instances"]

    for item in rule_map:
        print '"l2_%s" -> "%s_rules";' % (item, item)
        print '{rank=same; "l2_%s" "%s_rules"};' % (item, item)
    
    print "label = \"public\""
    print "}"

    get_sg_rules(layer_1["securitygroups"])
    get_sg_rules(layer_2["securitygroups"])

    get_rtb_rules(layer_1["routetable"])
    get_nacl_rules(layer_1["nacl"])
    get_nacl_rules(layer_2["nacl"])

    get_elb_rules(layer_1["endpoint"])

    print "}"
    #get_nacl_rules(layer_1["nacl"] + layer_2["nacl"])
    return

    print 
    print 
    print "------ LAYER 1 -----------"

    print "nacl - in  ", " ".join(layer_1["nacl"])
    print "sg   - in  ", " ".join(layer_1["securitygroups"])
    print "elb        ", layer_1["endpoint"]
    print "ip map     ", " ".join(layer_1["mappings"])
    print "sg   - out ", " ".join(layer_1["securitygroups"])
    print "nacl - out ", " ".join(layer_1["nacl"])

    print 
    print "---------------------------"
    print
    print
    print "--------- RTB -------------"
    print "routetable  ", " ".join(layer_1['routetable'])

    #for i in layer_1['routetable_raw']:
    #    for r in i['Routes']:
    #        print "%-15s %-10s"% (r['GatewayId'], r['DestinationCidrBlock'])
    
    print "---------------------------"

    print
    print
    print "------- LAYER 2 -----------"
    print "nacl - in  ", " ".join(layer_2["nacl"])
    print "sg   - in  ", " ".join(layer_2["securitygroups"])
    print "instance   ", layer_2["instances"]
    print "sg   - out ", " ".join(layer_2["securitygroups"])
    print "nacl - out ", " ".join(layer_2["nacl"])

    print "-----------------------------"

if __name__ == '__main__':
    main()