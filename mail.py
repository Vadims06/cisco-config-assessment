#!/usr/bin/python
# Import smtplib for the actual sending function
import smtplib
import csv
from tabulate import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sys import argv
import argparse
# Import the email modules we'll need
from email.mime.text import MIMEText

def send_report(tables, **kwargs):
  text = """
  Hello, Friend.

  Here is your data on plainttext format:

  {table}

  Regards,

  Me"""

  #tables = {'mail_to': "test", headers_sum: [], rows_sum: [], devices: ['192.168.1.1':{headers: [], rows: [], device_fqdn : ''}, '192.168.1.2': {headers: [], rows: []}]}
  # headers_summary_report = ['devices', 'FQDN', 'ok/ALL', 'Fails']
  headers_summary_report = tables['headers_summary_report']
  rows_summary_html_report = []
  for each_row in tables['rows_summary_report']:
    color_for_href = 'blue'
    rows_summary_html_report_temp = []
    row_string = '<a href=' + '"#%s">' %each_row[0] + each_row[0] + '</a>'
    rows_summary_html_report_temp.append(row_string)
    for each_columns in each_row[1:]:
        rows_summary_html_report_temp.append(each_columns)
    # Fail column is the last!
    if each_row[-1] != 0:
      color_for_href = 'red'
    rows_summary_html_report.append(rows_summary_html_report_temp)
  rows_summary_report = rows_summary_html_report

  html = """
  <html><body><p>Hello, Friend.</p>
  <p>Here is your report</p>
  <font color="cc263c">
  <h3 style=color: #cc263c;> Please open this letter in a browser </h3></font>
  <p>It's needed in order to links start to work. Press on the following message what you can find below To subject of this email </p>
  <p>"if there are problems with how this message is displayed click here to view it in a web browser". But unfortunately color is not supported by brows$  <style>
    table, th, td {{border: 1px solid black; border-collapse: collapse;background-color: #AAD373; }}
    table, th, td {{background-color: #AAD373; }}
    th, td {{ padding: 5px; }}
    a {{color: %s;}}
  </style>
  <p id="summary"></p>
  {table}
  """%color_for_href
  skip_this = """"""
  html_summary_report = html.format(table=tabulate(rows_summary_report, headers_summary_report, tablefmt="html"))
  # make header for our mail
  report = ""
  report += html_summary_report
  report += "<br><br>"
  # we are ready generate individual table for each device
  suggested_config = ""
  print "#"*20
  i = len(tables['devices'][0].keys())
  for device in tables['devices'][0].keys():
#   print "ROW", device, tables['devices'][0][device]['rows']
#   print "HEADER", device, tables['devices'][0][device]['headers']
#   print "Building report for device: ", device, tables['devices'][0][device]
#tables = {'mail_to': "test", headers_sum: [], rows_sum: [], devices: ['192.168.1.1':{headers: [], rows: []}, '192.168.1.2': {headers: [], rows: []}]}
    report += "<h2 id=" +'"%s">' %device + device + ", " + tables['devices'][0][device]['device_fqdn'] + "</h2>"
    individ_html = """
    <details>
    <style>
    table, th, td {{border: 1px solid black; border-collapse: collapse;background-color: #AAD373; }}
    table, th, td {{background-color: #AAD373; }}
    th, td {{ padding: 5px; }}
    </style>
    {table}
    </details>
    <br>
    <a href="#summary">Summary table</a>
    """
    individ_table_html = individ_html.format(table=tabulate(tables['devices'][0][device]['rows'], tables['devices'][0][device]['headers'], tablefmt="html"))
    report += individ_table_html
    if 'Suggested config' in tables['devices'][0][device]['headers']:
      sug_conf = """
      <details><summary> Individual table </summary>
      <style>
      table, th, td {{border: 1px solid black; border-collapse: collapse;background-color: #cecdcb; }}
      table, th, td {{background-color: #cecdcb; }}
      th, td {{ padding: 5px; }}
      </style>
      {table}
      </details>
      <br>
      <a href="#summary">Summary table</a>
     """
      for each_row in tables['devices'][0][device]['rows']:
        if len(each_row[-1])>2:
          #['\n0 devices have', '']
            suggested_config += each_row[-1].split(':')[-1]
      header = ['suggested config']
      sug_conf_html = sug_conf.format(table=tabulate([[suggested_config]], header, tablefmt="html"))
      report += "<br><br>"
      report += sug_conf_html
  report +="</body></html>"

  msg = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(report, 'html')])
  msg['Subject'] = 'Mail from Python'
  msg['From'] = 'pythontest@some_domain.com'
  msg['To'] = tables['mail_to']

  s = smtplib.SMTP('IP address of SMTP server', port=25)
  s.sendmail(msg['From'], msg['To'], msg.as_string())
  s.quit()
  print "The email has been sent"

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='send email with report as a payload')
  parser.add_argument('-r', action='store', dest="mail_to", required=True)
  parser.add_argument('-rows', action='store', dest="rows", default = [['row1'],['row2']])
  parser.add_argument('-headers', action='store', dest="headers", default = ['header1', 'header2'])
  args = parser.parse_args()
  send_report(args.mail_to, args.headers, args.rows)
