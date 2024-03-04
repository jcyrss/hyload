---
title: hyload - For HTTP Load Testing 
---

## Introduction

`hyload` is a performance testing framework.

It is used to test Web/HTTP API server, as the following figure shows.

![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/90c0e86d-b7c6-44f1-9580-cc34703f0968)

It provides a high-performance Python library to develop load testing. So you could run your test program on Windows， MacOS and Linux.

Based on gevent, by launching multiple hyload workers, it could reach about tens of thousands of requests per second and hundreds of thousands of concurrent connections on a single machine.

It also provides a VS Code extension to let you observe realtime statistics, remote multi-host deploy and remote launching test. VS Code extension includes a code-helper to facilitate developing.

![Code_ibIhaJDp3d](https://github.com/jcyrss/baiyueheiyu/assets/10496014/10d76802-37b0-4c73-bf12-48432a5720ef)

  
## Installation

Including install hyload library and hyload vscode extension

- hyload library

  Just run `pip3 install hyload` 

   

- hyload VS Code extension
  
  Search `hyload` in VS Code marketplace and install it

  ![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/ef128b00-0870-43a3-8051-36eaafe1b282)
    
  



## Quick Start

<!-- Say we need to test a API server.

Here is a simple test case.


```
Emulate 10 users' behaivor.

Each user performs the same behavior as follows

- call login API

- 3 seconds later，call list products API
``` 

<br>

-->


Assume we already have test cases of load testing, conducting testing with hyload usually includes the following steps:


### create vscode project

Create a project folder with vscode.

If you have multiple Python interpreter environments, create a empty python file so you could choose which Python interpreter you'd like to use in this project.

<br>

Next, open the  `Command Palette`  in VS Code, type  `hyload` 

In the options, select  `Initialize Hyload Project` ,

The hyload extension will create the project's common directories (like  `code_py` ,  `stats_perf` ) and one project configuration file  `hyload-cfg.json` .

It will also install the `hyload`  library in current Python interpreter if not already installed.

![init-project](https://github.com/jcyrss/baiyueheiyu/assets/10496014/4f421e78-3eaf-4eb7-b7d5-55c1025d8bda)


### verify interface

Before writing code for load test cases, usually we need to write simple code to verify HTTP interfaces.

All your Python testing related files are supposed to put in the directory `code_py`.

We could create a code file named like 'tmp.py' in directory `code_py`, and click the following icon on the editor title bar. 

<!-- ![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/8c650c22-f1a7-49f4-84c8-feb5aaa19d03) -->

![show-code-helper](https://github.com/jcyrss/baiyueheiyu/assets/10496014/ab273957-8c64-4a48-8836-b43354ae4f7d)

A code-helper window will popup on the right side.

Click items in the code-helper, the corresponding code snippet will be inserted at where cursor is.

<br>

For interface validation, we could click the first item `Code Template -Interface Test` , it will insert the following code snippet,

```py
from hyload import *

client = HttpClient() 
                   
print('Msg #1 - login >>>')
response = client.post(
    'http://192.168.5.80/api/mgr/signin',
    # HTTP body of x-www-form-urlencoded format
    data={
        'username':'byhy',
        'password':'88888888'
    },
    debug = True # to print HTTP message
)

print('Msg #2 - list_customer >>>')
response = client.get(
    '/api/mgr/customers?action=list_customer',
    debug = True
)
```

The code is easy to understand if you are familiar with Python and Requests.

Modify it as you need to very all kinds of HTTP interfaces according to your API spec.

The key is how to construct HTTP request, that's simliar to do with Requests, you could check the details in the section  `Class hyload.HttpClient` below.


<br>

When finish editing， just click the icon of  `Run Python File` to run as you usually do.

It will run in the terminal and output like the following

<!-- ![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/fbfeee2a-16b7-4be6-a205-70a3c421dbdb) -->

![verify-interface](https://github.com/jcyrss/baiyueheiyu/assets/10496014/52d394b6-4d20-4258-ab01-69572894d995)

Text in green is HTTP request and text in blue is response.



### write code for load test cases

Just create a code file corresponding to the test case, such as  `perf-test-001.py` .

Then click the item `Code Template - Load Test 1`  in code-helper to automatically insert the following code:

```py
from hyload import *

Stats.start() # to show stats on console and GUI.

#  ---------- define testing below   ----------

# User behavior function
def behavior1(username,password): 

    client = HttpClient() 

    # API login
    response = client.post('http://127.0.0.1/api/mgr/signin',
        data={'username':username,'password':password})
        
    sleep(1)

    for i in range(10):
        # send API list customers
        response = client.get('/api/mgr/customers?action=list_customer')
        
        # check response
        try:
            respObj = response.json()
        except:
            # if anything wrong, put it into stats and logs
            Stats.one_error('list_customer response.json() error')
            continue

        if (respObj['ret'] != 0):        
            Stats.one_error('list_customer respObj[ret] error')

        sleep(1)

# emulate 10 user's behavior of the same type
for i in range(10): 
    username=f'byhy_{i:04}'
    # run user behavior function in hyload task (a greenlet)
    run_task(behavior1, username, '88888888')
    sleep(1) 

# wait for all hyload tasks to end
wait_for_tasks_done()
```

<br>

In the above code, it defines the user's behavior into a function  `behavior1`, and invokes it 10 times to emulate 10 users.

The key is to call the behavior function by invoking `run_task`, so it will run in a `hyload task`  which is a  `greenlet` (a coroutine, a light-weight thread) under the hood, so all tasks run in parallel.


<br>

You may notice the following line of code in the above template code 

```py
Stats.start()
```

It will create stats to display during running, and save to file also for later use.

Stats data file is prefixed by string of launching time, and stored in the folder of `stats_perf` in the working directory(usually also the project folder).

The stats file path could be specified mannually by command line argument `statsfile`, like  `statsfile=/my/stats/folder/stats1.sts` .


<br>

The last line is `wait_for_tasks_done()`, that is to make process wait until all hyload tasks are over.


<br>

Modify the template code according to your load test case.

Be sure to remove  `debug = True` from the message sending methods invoking, or it will print a lot and slow down code running.



### execute test


To run load testing code and realtime monitor stats, click the icon of  `hyload - Run This File`

![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/fad79031-6618-465f-9295-dbbecc4a89b6)



<br>

Comparing to regular run，it just adds an extra command line argument  `console`, so hyload library know where to send stats. 



![execute-test-1](https://github.com/jcyrss/baiyueheiyu/assets/10496014/a9df3f71-e6a2-4a12-bb12-f916849bf472)

<br>

Every line of different color in the dynamic chart represents different metrics as defined on top.

Like, the green line represents requests per seconds. 

The blue line represents reponses per seconds. It looks like invisible here, because if it is in the same value of requests-per-seconds, it will be covered by green line. You could click green block to hide green line to make it visible.

Please note that, the black line reprents average reponse time per seconds, the Y value axis of it is on right, instead of left.

<br>

You may notice there is one line under the dynamic chart, like

```
127.0.0.1:53277 Total -- send :110, recv :110, error :100, 0-100ms :110
```

It is overall stats, including total number of the messages sending, receieving, timeout, error and in different response time ranges.


Each line relates to one hyload worker process. We could run multiple hyload workers by executing test code file multiple times.

<br>

The testing process will be over when all hyload tasks are done.

If you want to abort testing, just close the terminal window or press Ctrl+C. 


### create test report charts 


After testing, we get the stats data files, by default they are on the folder  `stats_perf` of the test process working directory.

We could create stats charts from stats data files.

Just click `Plot Load Test Statistics` button on realtime monitor or  `hyload` icon on bottom-right of status bar， and select stats data files on the popup dialog. You could select multiple data files if you run multiple load testing process and create multiple stats files.

![create-load-stats-result](https://github.com/jcyrss/baiyueheiyu/assets/10496014/4258ad89-c448-445a-a7ec-3cfbc4ef61eb)



![Figure_1](https://github.com/jcyrss/baiyueheiyu/assets/10496014/8baf32b0-78e1-425f-9732-dfc04729fdb3)

The top chart is request number per second

The middle chart is response/error/timeout number per second.

The bottom chart is response time on average per second


<br>

In the middle chart, if there were red dots, they indicate errors.

And if there were green dots, they indicate timeouts.

We could click the `save` icon on bottom status bar, to export them as a picture file and put them to the test report.

 

<br>

In the code-helper menu, there is another item called `Code Template -Load Test 2`.

Clicking it will insert the following code template, which is a sample of load testing to a web server.

```py
from hyload import *

Stats.start() # to show stats on console and GUI.

#  ---------- define testing below   ----------

# User behavior class
class VUser:
    def __init__(self,username):
        self.client = HttpClient()
        self.username = username

    # entry method
    def behavior(self):
    
        # open home page
        self.static_resource('http://127.0.0.1', 301)
        self.static_resource('/cdnjs/jquery/jquery.min.js')
        sleep(2)
    
        # open login page
        self.static_resource( '/mgr/sign.html')
        sleep(2)
    
        # login
        response = self.client.post('http://127.0.0.1/api/mgr/signin',
            data={'username':'byhy','password':'88888888'})
        
        # check respose
        if (response.json()['ret'] != 0):            
            Stats.one_error('login error') # put error info into stats and logs
            return
            
        # show the page after login
        self.static_resource( '/mgr/')
        sleep(2)
       
    # method to open static page
    def static_resource(self,url,statusCode=200):
        response = self.client.get(url)
    
        #  check status code
        if (response.status_code != statusCode):
            Stats.one_error(f'{url} error {response.status_code}')
        

# emulate 10 user's behavior of the same type
for i in range(10):
    username = f'user{i:06}'
    vuser = VUser(username)
    
    # run user behavior function in hyload task (a greenlet)
    run_task(vuser.behavior)
    sleep(1) 

# wait for all hyload tasks to end
wait_for_tasks_done()
```

It puts emulation of user's behavior into a class, which is more convenient when user's behaivor is more complicated.




## How-to guides

### Cookies

hyload will save cookies in HTTP response automatically for every HttpClient. 

So you don't have to save it manually and set it in the following requests.

It's convenient for the testing of cookie-session based interfaces.


### Check Points

We often need to check reponse data, like status code, message headers, message body.

It's also convenient by clicking the corresponding code-helper items to get template code first.

<br>

Like, if you want to check the status code of response，click the following item.

![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/514b5f59-b1c3-41d7-a396-7c09ae3081ed)

It will insert the following code

```py
response.status_code
```

So we know  `status_code` is the property of response object we want, without need to check API documentation first.

<br>

If we found something wrong in response, we should report it in realtime stats and stats file.

Just click the code-helper item `Record one error during test`, it will insert the following code snippet


```py   
Stats.one_error("error info")
```

Modify the error info as you need. 


### Logging

Sometimes, we need to write something into log file even nothing wrong happens.

Click the code-helper item `Write something into log file`, it will insert the following code snippet

```py
TestLogger.write('log info')
```

Log files are saved in the folder  `log`.
 
<br>

Put those information helpful to pinpoint the root cause of issues, like error related session id， user name/id, etc.

<br>

If you have your own stats requirements which built-in stats does not cover, put key info into log file for later analysis.

Like, if we want user names in those login requests related response times longer than 1 second. We could write code like this


```py
response = client.send('GET', "/api/mgr/signin")

rt = response.response_time # in millisecond

if rt > 1000: # longer than 1 second
    TestLogger.write(f'API signin >1s|{username}')
```




### Import HAR file

Usually accessing a web site url triggers many resource fetchings, like html/css/js/image files.

If we manually write code to do that, it would be cumbersome.

We could first save those traffics to HAR file in browser <a href='https://support.google.com/admanager/answer/10358597?hl=en' target='_blank'>according to this article</a>.

Next, import that HAR file to generate code automatically by clicking the coder-helper item  `Import HAR file`, and modify it as needed. That will save lot of work.

![import-har](https://github.com/jcyrss/baiyueheiyu/assets/10496014/081f04c2-05fa-491a-882f-d0615dadc407)



### Remote Login Setup

In load testing, we often need to get `CPU/memory/disk IO` usage on SUT (system under test) host.

And we may also need to deploy load testing tools to remote hosts to run.

To do that with hyload, first we need to setup remote login on hyload.

<br>

Create a machine on the dir of  `remotes`  in project, and fill entries of host, SSH Port, User Name, like this

![setup-remote-1](https://github.com/jcyrss/baiyueheiyu/assets/10496014/e9c1deb0-15de-4eae-b377-1f92d87c57f0)

<br>

When hyload performs tasks, like  `Start resource stats`, `Plot resource stats`, many of them need to run Python. So we need to specify the path of Python interpreter.

If default 'python3' does refer to the one you want, specify the path in the last configure item  `Python Executable Path` .

<br>

We recommand to login by SSH keys.

If you don't already have SSH key pair, create one by click the menu item of  `Generate SSH Key Pair`, like this

![setup-remote-2](https://github.com/jcyrss/baiyueheiyu/assets/10496014/9a65bb99-60a2-4df3-86a3-924a9bdc6bfb)

<br>

Then, install the public key onto target machine. 

Just click the menu item of  `Install SSH Public Key`, there will be a file-selection dialog to choose SSH public key file, and a popup terminal to create public key on remote, you need to input password to authenticate. 

Like this

![setup-remote-3](https://github.com/jcyrss/baiyueheiyu/assets/10496014/73bf8fe1-01fb-4547-b49b-ad4ca9b59f64)

On Mac, default location of SSH public key is `/Users/your-user-name/.ssh/id_rsa.pub`.  `.ssh` is a hidden folder, to display it, you need to press Command + Shift + . (period) to make it appear.

On Windows, default location of SSH public key is  `C:\Users\your-user-name\.ssh\id_rsa.pub`.

<br>

When all done, you could login to the machine by clicking the menu `SSH Login`.

![setup-remote-4](https://github.com/jcyrss/baiyueheiyu/assets/10496014/52732e04-8cda-4ccf-830b-0212ae3a4ef1)


### CPU/MEM/DISK Usage Stats

`hyload` provides tools to monitor and report  `CPU/memory/disk IO` usage on the machine where the system under test (SUT) run.

<br>

You need to deploy monitor tool to SUT hosts first.

![resource-mon-1](https://github.com/jcyrss/baiyueheiyu/assets/10496014/8b412f0e-f690-4a89-ad0f-34c0502a4f2a)

It will be put into the remote directory `~/hyload_sysmon`.

<br>

Just before load testing, start resource stats by clicking the menu item  `Start Resource Stats`.

It will run Python resource usage stats program and save data to the file.

![resource-mon-2](https://github.com/jcyrss/baiyueheiyu/assets/10496014/0d9d1664-071c-414c-a1d1-023cb82fcef2)


<br>

After testing, don't forget to stop it by clicking the menu item  `Stop Resource Stats` 

Then you could download stats files by clicking the menu item  `Pull Resource Stats`. The stats file will be download into the project folder  `stats_resource`.

![resource-mon-3](https://github.com/jcyrss/baiyueheiyu/assets/10496014/69c5588e-5d5d-4559-aef8-1040e2c08129)

<br>

Next, you could create report charts by clicking the menu item `Plot System Resource Usage` on Mahine Page or hyload icon menu of status bar.

![resource-mon-4](https://github.com/jcyrss/baiyueheiyu/assets/10496014/bdb4e002-272b-426e-bff4-d2fcdc98eda8)



<br>

During the test, you could view realtime resource usage stats by clicking the menu item  `View Resource Stats`




### Deploy/Run hyload remotely

Sometimes, the system under test (SUT) run on remote machines/clusters, so we should deploy hyload on the test driver machine close to them.

With hyload VS Code extension, we could easily deploy hyload test code package on remote machines running Linux.

Add the test driver machine into project folder  `remotes` and setup remote login as mentioned earlier.

<br>

You need to deploy hyload worker tools to SUT hosts first by clicking the menu item  `Deploy Hyload Worker` 

![test-driver-1](https://github.com/jcyrss/baiyueheiyu/assets/10496014/be741d98-100f-472e-908c-4e54b3f6a941)

It does 2 things.

One is to create a directory  `hyload_worker` on user's home dir.

<!-- , and upload a process-killing script  `kill_hyload_worker.sh`  into it. -->

The second, executes command  `python3 -m pip install hyload`. So if your Linux environment was not ready for that command, do it manually.


<br>

Then, you need to upload load testing Python files by clicking the menu item  `Upload Load Testing Files`. The files will be uploaded on remote directory `~/hyload_worker` 

![test-driver-2](https://github.com/jcyrss/baiyueheiyu/assets/10496014/664e3d00-4849-4c34-abc8-c8d2f367c4dd)

<br>

Next, you could run load testing code file. 


If that remote machine can access monitor machine directly, just login and exeute command like

```shell
python3 your-code.py tag=hyloadtest console=monitor-IP:Port
```

Replace  `your-code.py` with your code file name, replace  `monitor-IP:Port` with the your monitor's IP and Port

![test-driver-3](https://github.com/jcyrss/baiyueheiyu/assets/10496014/4e037335-23a6-46cc-b145-e85708e4a61a)


<br>

Or you could click the menu item  `Start Load Testing`, it will automatically open a terminal, login, enter directory `hyload_worker`, and give you some help info about what to do next. You could just do it as suggested.


<br>

If that remote machine can NOT access monitor machine directly, we need stats messages get relayed by  `stats-hub websocket server`, AKA  `SWS` .

To do that, first ensure open TCP port 28888, UDP port 29999 on the firewall, they are the ports  `SWS`  uses. Like  

```shell
ufw allow 28888/tcp
ufw allow 29999/udp
```


<br>

And then,  run SWS like this

```shell
nohup python3 -m hyload.tools.statshub.py --wsport 28888 --recvport 29999 &
```


28888 is websocket server port waiting for connections from  `hyload monitor`. 

29999 is to receive stats data from  `hyload worker`.

<br>

So, on hyload monitor, add this StatsHub, like,  `ws://192.168.5.33:28888`  , click  `connect` 

![test-driver-4](https://github.com/jcyrss/baiyueheiyu/assets/10496014/9ad43459-c9c9-44ee-ac79-0fa9f83946df)

<br>

Then, run load testing command like this

```shell
python3 your-code.py tag=hyloadtest console=statsHub-IP:29999   
```   

![test-driver-5](https://github.com/jcyrss/baiyueheiyu/assets/10496014/962f6de8-8128-4053-8694-8ca4c424143c)

<br>

During test, you could stop it by clicking the menu item  `Stop Resource Stats`, that's to run the script `kill_hyload_worker.sh` in effect.

<br>

As run it locally, all stats data is saved in files in the folder  `~/hyload_worker/stats_perf`  

Then you could get stats files to local by clicking the menu item  `Pull Load Testing Stats`. All the stats files will be download to local project folder `stats_perf`.

You could then create report charts by clicking the menu item  `Plot Load Testing Stats`.



## API Reference 

Please check <a href='api.html' target='_blank'>API Reference</a> for the detail usage of the hyload library.