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
        ['devices', 'ok/ALL'] [['172.16.0.2', '4/5'], ['172.16.0.1', '2/5']]
        Generating individual device report...
        Config generation has been finished!
        ####################
        The email has been sent
