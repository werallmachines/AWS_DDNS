import os
import boto3

ec2 = boto3.client('ec2')
route53 = boto3.client('route53')

ints = ec2.describe_network_interfaces()['NetworkInterfaces']
zones = route53.list_hosted_zones()['HostedZones']
current_xlb_ips = []
current_hz_ips = []
zoneid = ''

def get_xlb_ips():
    global current_xlb_ips
    l = []
    for n in range(0, len(ints)):
        l.append(ints[n]['Description'].split('/'))
        if len(l[n]) >= 3:
            if l[n][1] == os.environ.get('elb_name'):
                current_xlb_ips.append(ints[n]['PrivateIpAddress'])

def get_hz_records():
    global zoneid
    global current_hz_ips
    # get the proper hosted zone
    for n in range(0, len(zones)):
        if zones[n]['Name'] == os.environ.get('ZONE_NAME'):
            zoneid = zones[n]['Id'][12:]
            # parse the resource record sets for the proper one
            rrecordsets = route53.list_resource_record_sets(HostedZoneId=zoneid)['ResourceRecordSets']
            for n in range(0, len(rrecordsets)):
                if rrecordsets[n]['Name'] == os.environ.get('RECORD_NAME'):
                    if rrecordsets[n]['Type'] == os.environ.get('RECORD_TYPE'):
                        if 'AliasTarget' in rrecordsets[n]:
                            break
                        else:
                            current_hz_ips = [d['Value'] for d in rrecordsets[n]['ResourceRecords']]

def update_hz():
    # check if there are IPs on the XLB not currently in
    # resource record and update the resource record if so
    new_rrecord = []
    for ip in current_xlb_ips:
        if ip not in current_hz_ips:
            for val in current_xlb_ips:
                new_rrecord.append({'Value': val})
            
            update = route53.change_resource_record_sets(
            HostedZoneId=zoneid,
            ChangeBatch={
                'Comment': 'Private IPs of XLB changed - updated record set',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': os.environ.get('RECORD_NAME'),
                            'Type': os.environ.get('RECORD_TYPE'),
                            'TTL': int(os.environ.get('TTL')),
                            'ResourceRecords': new_rrecord,
                            }
                        },
                    ]
                }
            )
            print('Updated DNS')
            return
        continue
    print('Did not update DNS')

def lambda_handler(event, context):
    global current_xlb_ips
    global current_hz_ips
    global zoneid

    try:
        get_xlb_ips()
        get_hz_records()
        update_hz()

        current_xlb_ips = []
        current_hz_ips = []
        zoneid = ''

        return 'Executed successfully.'
    except:
        return 'Something went wrong.'