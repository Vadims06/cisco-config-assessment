#!/usr/bin/python
import getpass
from netmiko import ConnectHandler
import netmiko
import csv,sys, re
import yaml
import operator
import threading
from Queue import Queue
from mail import send_report
from tabulate import tabulate

LOGIN = raw_input("Login: ")
PASSWORD = getpass.getpass("Password: ")
SECRET = getpass.getpass("Secret pass if any: ")
MAIL_TO = raw_input("Email: ")

# CHECKER FOR FILE EXISTENCE
devices = yaml.load(open('hosts.yaml'))
with open('master-switch.csv') as master_config_csv:
  master_config = csv.reader(master_config_csv, delimiter=';')
  master_config_in_list = list(master_config)
for null_strings in range(master_config_in_list.count([])):
  master_config_in_list.remove([])
#master_config_in_list = [[1.1.1;checking ntp servers;ntp server1], [1.1.2;checking aaa servers; aaa server1]]
#master_config_csv = open('master-switch.csv', 'rb')
#master_config = csv.reader(master_config_csv, delimiter=';')
report = {}
email_report = {}
config_statistic = {}

def connect_ssh(device_dict, command, queue):

  device_dict['username'] = LOGIN
  device_dict['password'] = PASSWORD
  device_dict['secret'] = SECRET
  # this is only one command, isn't it?
  if isinstance(command, list) == True:
    command_count = len(command)
  else:
    command_count = 1
  try:
    print "Connection to device %s, execute %d command %s" % (device_dict['ip'], command_count, command)
    ssh = ConnectHandler(**device_dict)
    ssh.enable()
    #result = ssh.send_command('terminal length 0')
    #device_output = u'Building configuration...\n\n ...'
    device_output = ssh.send_command(command)
    #add result as a dictionary to the queuery
    queue.put({ device_dict['ip']: device_output })
    lookuper_str_in_config({ device_dict['ip']: device_output, 'device_type': device_dict['device_type']})
  except netmiko.ssh_exception.NetMikoAuthenticationException as e:
    print e

def simple_ssh(device_dict, command):
  output = []
  device_output = []
  device_output_temp = []
  device_dict['username'] = LOGIN
  device_dict['password'] = PASSWORD
  device_dict['secret'] = SECRET
  # this is only one command, isn't it?
  if isinstance(command, list) == True:
    command_count = len(command)
  else:
    command_count = 1
  try:
    print "Connection to device %s, execute nested %d command" % (device_dict['ip'], command_count)
    ssh = ConnectHandler(**device_dict)
    ssh.enable()
    #result = ssh.send_command('terminal length 0')
    if command_count > 1:
      for sub_command in command:
        #device_output = u'Building configuration...\n\n ...'
        device_output.append({sub_command : ssh.send_command(sub_command, use_textfsm=True)})
    else:
      device_output.append({command : ssh.send_command(command, use_textfsm=True)})
    #add result as a dictionary to the queuery
    #lookuper_str_in_config({ device_dict['ip']: device_output })
    output.append({ device_dict['ip']: device_output })
    return output
  except netmiko.ssh_exception.NetMikoAuthenticationException as e:
    print e

def filler(device_ip, point, status, not_found):
  # REPORT = {'192.168.0.1': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'fail', 'not found': 'aaa server1'}}, '192.168.0.2': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'ok', 'not found': ''}}}
  #every_point_results = {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'fail', 'not found': 'aaa server1'}}
  every_point_results = {}
  # below is dictionary for '1.1.1' : {}
  if not report.has_key(device_ip):
     report[device_ip] = {}
  # below is dictionary for {'result': 'fail', 'not found': 'aaa server1'}
  report[device_ip][point] = {}
  report[device_ip][point]['result'] = status
  report[device_ip][point]['not found'] = not_found
  #write '192.168.0.1':{'1.1.1':{'result': 'ok'}} to the report {}

def lookuper_str_in_config(output_from_device_as_a_dictionary, **kwarq):
  #we got keys as a list ['192.168.1.1']
  device_ip = output_from_device_as_a_dictionary.keys()[0]
  print "%s use lookaper" %device_ip
  #output_from_device_as_a_dictionary = 192.168.1.1: 'device output'
  device_output = output_from_device_as_a_dictionary[device_ip]
  every_point_results = {}
  not_found_string = ''
  for row in master_config_in_list:
    # if we have what to check. This command is located on the 3d position in csv
    # row = [point, desciption, command]
    # row[0] = point
    # row[1] = desciption
    # row[2] = command
    if len(row)>2:
     command = row[2]
     # we have 2 semicolon and we have empty string on the 3d position
     if row[2]:
      if re.findall('show\s', command):
        #we found nested command
        device_dict = {}
        second_routine_command_list = []
        nested_command = command.split(',')[0].split('|')[0]
        nested_filter = command.split(',')[0].split('|')[1].strip()
        device_master_command = command.split(',')[1]
        device_dict['ip'] = device_ip
        device_dict['device_type'] = output_from_device_as_a_dictionary['device_type']
        output = simple_ssh(device_dict, nested_command)
        #output = [{'192.168.0.1': [{'show ip ospf int br ': [{'area': '0', 'neighbors_fc': '0/0', 'state': 'LOOP', 'cost': '1', 'interface': 'Lo1', 'ip_address_mask': '1.1.1.1/32'}, {'area': '0', 'neighbors_fc': '1/1', 'state': 'BDR', 'cost': '10', 'interface': 'Gi0/0/0', 'ip_address_mask': '10.1.1.1/29'}]}]}]
        #sub_command_output = [{'area': '0', 'neighbors_fc': '0/0', 'state': 'LOOP', 'cost': '1', 'interface': 'Lo1', 'ip_address_mask': '1.1.1.1/32'}]
        #second_routine_command_list = "show run int Lo1"
        for sub_command_output in output[0][device_ip][0][nested_command]:
          second_routine_command_list.append("show run int " + sub_command_output[nested_filter])
        second_routine_command_output = simple_ssh(device_dict, command=second_routine_command_list)
        # second_routine_command_output = [{'192.168.0.1': [{'show run int Lo1': [u'Building configuration...]}, {'show run int Gi0/0/0': u'Building configuration...'}]
        not_found_string = ""
        for second_routine_command_output_item in second_routine_command_output[0][device_ip]:
          if re.findall(device_master_command, second_routine_command_output_item.values()[0]):
            not_found_string += row[0] + ': [+]' + second_routine_command_output_item.keys()[0].strip() + '\n'
          elif not re.findall(device_master_command, second_routine_command_output_item.values()[0]):
            not_found_string += row[0] + ': [-]' + second_routine_command_output_item.keys()[0].strip() + '\n'
		if not_found_string.count('[+]') == len(not_found_string.split('\n'))-1:
           not_found_string_status = 'ok'
        elif not_found_string.count('[+]') != len(not_found_string.split('\n'))-1:
           not_found_string_status = 'fail'
        filler(device_ip=device_ip, point=row[0], status=not_found_string_status, not_found=not_found_string)

      # if we FOUND the command exactly in device_output
      elif re.findall(row[2].strip(), device_output):
         #save our result to the report dictionary
         filler(device_ip=device_ip, point=row[0], status='ok', not_found='')
         #print "we found", re.findall(row[2].strip(), device_output)[0]
         statistic(row[0], re.findall(row[2].strip(), device_output)[0])
      # IF NOT FOUND a string in config
      # It's not necessesary bad, may be the composit string exists in device config in expected order. For example
      # we are looking 'line con 0\nlogin authentication console', but in config we have:
      # line con 0
      # exec-timeout 0 0
      # privilege level 15
      # logging synchronous
      # login authentication console
      # stopbits 1
      elif not re.findall(row[2].strip(), device_output):
         #check if this command includes multiple commands, like "ntp server1\nntp server2\nntp server3"
         if len(row[2].strip().split('\n'))>1:
            for sub_master_command in row[2].split('\n'):
              #for the case "ntp server1\n" we get ["ntp server1", ""]
              if sub_master_command:
                # print "sub_master_command: ", sub_master_command
                # then we are looking for those command which abcend in device config. That's why if not
                if not re.findall(sub_master_command, device_output):
                       not_found_string += sub_master_command.strip()
                # if 'not_found_string' is not empty, it means that we didn't find some command in device config. That's why status is Fail
            if not_found_string:
              not_found_string = ''
			  not_found_string_status = ''
              for sub_master_command in row[2].split('\n'):
               if sub_master_command:
                if not re.findall(sub_master_command, device_output):
                       not_found_string += row[0] + ': [-]' + sub_master_command.strip() + '\n'
                elif re.findall(sub_master_command, device_output):
                       not_found_string += row[0] + ': [+]' + sub_master_command.strip() + '\n'
			  if not_found_string.count('[+]') == len(not_found_string.split('\n'))-1:
                  not_found_string_status = 'ok'
              elif not_found_string.count('[+]') != len(not_found_string.split('\n'))-1:
                  not_found_string_status = 'fail'
              filler(device_ip=device_ip, point=row[0], status=not_found_string_status, not_found=not_found_string)
            if not not_found_string:
              filler(device_ip=device_ip, point=row[0], status='ok', not_found=not_found_string)
          # if NOT FOUND and it's single command
         if len(row[2].strip().split('\n'))==1:
            filler(device_ip=device_ip, point=row[0], status='fail', not_found=row[0] + ': ' + row[2])
            print "Didn't find %s in %s" %(row[2], device_ip)
    #where is no any commands in CSV which we need to check
     if not row[2]:
      print  "where is no any commands in CSV which we need to check. Fill MASTER CONFIG point %s correctly " %row[0]

def conn_threads(function, devices, command):
  threads = []
  #Create Queue
  q = Queue()
  for device in devices:
    # pass the queue as an argument to the function "connect_ssh", this function return NOTHING, it puts the result to queue.
    th = threading.Thread(target = function, args = (device, command, q))
    th.start()
    threads.append(th)
  # we will wait until every function finishes working
  for th in threads:
    th.join()

  print "Config processing for all devices has been finished!"
  #return [{'192.168.1.1': 'output from device'}, {'192.168.1.2': 'output from device'}]

def to_table(report):
  # REPORT = {'192.168.0.1': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'fail', 'not found': 'aaa server1'}}, '192.168.0.2': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'ok', 'not found': ''}}}
 rows = []
 headers = []

 for point_of_checking in master_config_in_list:
   if len(point_of_checking)>2:
     # we fight against empty config string
     if point_of_checking[2]:
        headers.append(point_of_checking[0])

 headers.insert(0, 'devices')
 headers.append('not found')

 for devices in report.keys():
  temp_row = []
  temp_tuple_list = []
  not_found_string = ''
  just_list = []
  #email_report_temp = {'192.168.1.1': {'headers': [], 'rows': []}}
  #rows_headers = {'headers': [], 'rows': []}
  email_report_temp = {}
  rows_headers = {}
  temp_row.append(devices)
  for point_of_checking in master_config_in_list:
# for point_of_checking in report[devices].keys():
   # for the case when there wasn't command on the 3d position in csv file
   if len(point_of_checking)>2:
    if point_of_checking[2]:
      temp_row.append(report[devices][point_of_checking[0]]['result'])
      if report[devices][point_of_checking[0]]['result']=='fail':
         not_found_string += report[devices][point_of_checking[0]]['not found'] + "\n"
  temp_row.append(not_found_string)
  rows.append(temp_row)
  rows_headers['rows']= html_converter(rows)
  rows_headers['headers']= headers
  email_report_temp[devices] = rows_headers
  if not email_report.has_key('devices'):
     email_report['devices'] = []
  email_report['devices'].append(email_report_temp)

 rows_for_html = html_converter(rows)

 return rows, headers, rows_for_html

def html_converter(rows):
   # HTML converter
 row_for_html, rows_for_html = [], []
 if any(isinstance(i, list) for i in rows) == True:
   for row in rows:
      for each_elem_in_row in row:
        row_for_html.append(each_elem_in_row.replace('\n', '<br>'))
      rows_for_html.append(row_for_html)
      row_for_html = []
 else:
   rows_for_html = rows.replace('\n', '<br>')
   #rows_for_html.append(row_for_html)
 return rows_for_html

def statistic(point, config):
  if not config_statistic.has_key(point):
    config_statistic[point] = {}
  config_statistic[point][config] = config_statistic[point].get(config, 0) + 1

def get_most_common_config(point):
  if not config_statistic.has_key(point):
    most_common_config = ""
    hit_count = 0
  else:
    most_common_config = max(config_statistic[point].iteritems(), key=operator.itemgetter(1))[0]
    hit_count = config_statistic[point][most_common_config]
  return most_common_config, hit_count

def summary_table(report):
  # REPORT = {'192.168.0.1': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'fail', 'not found': 'aaa server1'}}, '192.168.0.2': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'ok', 'not found': ''}}}
  headers_summary_report = ['devices', 'ok/ALL']
  rows_summary_report = []
  all_checks = 0
  all_ok = 0
  for point_of_checking in master_config_in_list:
   if len(point_of_checking)>2:
     if point_of_checking[2]:
       all_checks += 1

  for devices in report.keys():
    all_ok = 0
    for point_of_checking in master_config_in_list:
      if len(point_of_checking)>2:
        if point_of_checking[2]:
          if report[devices][point_of_checking[0]]['result']=='ok':
            all_ok += 1
    rows_summary_report.append([devices, '%d/%d' %(all_ok,all_checks)])
  print headers_summary_report, rows_summary_report
  email_report['headers_summary_report'] = headers_summary_report
  email_report['rows_summary_report'] = rows_summary_report

def individual_table(report, with_config):
  # REPORT = {'192.168.0.1': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'fail', 'not found': 'aaa server1'}}, '192.168.0.2': {'1.1.1': {'result': 'fail', 'not found': 'ntp server1'}, '1.1.2': {'result': 'ok', 'not found': ''}}}
  #master_config_in_list = [[1.1.1,checking ntp servers,ntp server1], [1.1.2,checking aaa servers, aaa server1]]
  rows = []
  rows_headers = {}
  print "Generating individual device report..."
  temp_rows = []
  headers = ['point', 'result', 'command', 'not found', 'description']
  if with_config == True:
    headers = ['point', 'result', 'command', 'not found', 'description', 'Suggested config']
  rows_headers['headers'] = headers
  email_report_temp = {}
  for point_of_checking in master_config_in_list:
    if len(point_of_checking)>2:
      if point_of_checking[2]:
        for ip in report.keys():
          temp_rows = []
          temp_rows.append(point_of_checking[0])
          temp_rows.append(report[ip][str(point_of_checking[0])]['result'])
          temp_rows.append(html_converter(point_of_checking[2]))
          temp_rows.append(html_converter(report[ip][str(point_of_checking[0])]['not found']))
          temp_rows.append(point_of_checking[1])
          if not email_report_temp.has_key(ip):
            email_report_temp[ip] = {}
          if not email_report_temp[ip].has_key('rows'):
            email_report_temp[ip]['rows'] = []
          if with_config == True:
            if report[ip][str(point_of_checking[0])]['result'] == 'fail':
              config, hit_count = get_most_common_config(point_of_checking[0])
              if config:
                config_string = '%d devices have: \n %s' %(hit_count, config)
                temp_rows.append(html_converter(config_string))
              elif not config:
                temp_rows.append('')
            else:
              temp_rows.append('-')
          email_report_temp[ip]['rows'].append(temp_rows)
          if not email_report_temp[ip].has_key('headers'):
             email_report_temp[ip]['headers'] = headers

        if not email_report.has_key('devices'):
          email_report['devices'] = []
        email_report['devices'].append(email_report_temp)
  print "Config generation has been finished!"

if __name__ == '__main__':
  conn_threads(connect_ssh, devices['switches'], 'show run')
#  print tabulate(rows, headers, tablefmt='grid')
  summary_table(report)
  individual_table(report, with_config=True)
  email_report['mail_to'] = MAIL_TO
  send_report(email_report)
