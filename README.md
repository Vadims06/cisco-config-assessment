# cisco-config-assessment
This tool allows you to differ your current config on multiple cisco network devices with master config. Then you will get the report about each device on your email.

        
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
