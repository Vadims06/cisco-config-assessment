# cisco-config-assessment
This tool allows you to differ your current config on multiple cisco network devices with master config. Then you will get the report about each device on your email.
![config assessment](https://user-images.githubusercontent.com/20796986/41838356-e1c7cc46-7868-11e8-9e80-5ce02b23fb33.png)
        
    # python assess.py
    Login: logindevice
    Password:
    Secret pass if any:
    Email: some-email@test.com
        Connection to device 172.16.0.1, execute 1 command show run
        Connection to device 172.16.0.2, execute 1 command show run
        172.16.0.1 use lookaper
        Didn't find aaa authentication login default local in 172.16.0.1
        Didn't find ntp source [vV]lan\s?\d+ in 172.16.0.1
        172.16.0.2 use lookaper
        Config processing for all devices has been finished!
        ['devices', 'ok/ALL'] [['172.16.0.2', '5/6'], ['172.16.0.1', '2/6']]
        Generating individual device report...
        Config generation has been finished!
        ####################
        The email has been sent

![report](https://user-images.githubusercontent.com/20796986/41652818-e74fb5f0-748c-11e8-83bd-3b10674bc07b.png)

##### ## "Suggested config" logic

I use statistic dictionary which save actual device config into it and keep count how many times the following command was found in devices. For example, we specify **"ntp source [vV]lan\s?\d+"** in *master config*, so we don't care about the Vlan number and eventually we can get the following statistics

    {'1.1.6':{'ntp sourse vlan1': 12, 'ntp sourse vlan112': 1}}
Twelve devices have vlan1 as the ntp sourse and only single device has vlan112 as sourse for ntp. So we can suggest to apply most common configuration ('ntp sourse vlan1' in our case) for that device which failed at '1.1.6' checking point.

##### ## Iteration over interfaces
You may want to check some specific interface configuration. For example look for all ospf interfaces, keep this information in memory and find out what you want against these interfaces through 'show run interface {interface name}'. This logic is based on TextFSM templates which you can kindly find following this link [TextFSM templates](https://github.com/networktocode/ntc-templates/blob/master/templates/index?__s=81e68ymd1xgrmdzspw9f "TextFSM templates") 
![image](https://user-images.githubusercontent.com/20796986/41654736-144b806a-7493-11e8-9072-e195ba788560.png)
Device output with used template you can find below:

    {'area': '0', 'neighbors_fc': '0/0', 'state': 'LOOP', 'cost': '1', 'interface': 'Lo1', 'ip_address_mask': '1.1.1.1/32'}
In order to iterate over all ospf interfaces and check md5 password you need specify the following command in *master-config file*
```rst
"show ip ospf int br | interface, ip ospf message-digest-key [\d]+ md5 7 .*"
```
It means that we take 'interface' key in the dictionary and send additional command to cisco device. We make only single SSH connection, but send multiple commands.

##### Where you can find full config assessment check list?
You can find quite full check list with Cisco commands here in "CIS Cisco IOS 12 Benchmark"
```
BOTH CIS SECURITY BENCHMARKS DIVISION MEMBERS AND NON-MEMBERS MAY:
Print one or more copies of any SB Product that is in a .txt, .pdf, .doc, .mcw, or .rtf format, but only if each such copy is printed in
its entirety and is kept intact, including without limitation the text of these CIS Security Benchmarks Terms of Use.
```
[CIS Cisco IOS 12 Benchmark.pdf](http://www.itsecure.hu/library/image/CIS_Cisco_IOS_12_Benchmark_v4.0.0.pdf "Check List")
```
1 Management Plane
1.1 Local Authentication, Authorization and Accounting (AAA) Rules
1.1.1 Enable 'aaa new-model' (Scored)  
1.1.2 Enable 'aaa authentication login' (Scored)  
1.1.3 Enable 'aaa authentication enable default' (Scored)  
1.1.4 Set 'login authentication for 'line con 0' (Scored)  
1.1.5 Set 'login authentication for 'line tty' (Scored)  
1.1.6 Set 'login authentication for 'line vty' (Scored)  
1.1.7 Set 'aaa accounting' to log all privileged use commands using 'commands 15' (Scored)  
<omited>
```
##### Before using
Pls kindly specify SMTP settings in mail.py script.
```
msg['From'] = 'pythontest@some_domain.com'
s = smtplib.SMTP('IP address of SMTP server', port=25)
```
