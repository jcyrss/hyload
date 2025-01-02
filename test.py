from hyload import *

Stats.start() # to show stats on console and GUI.

#  ---------- define testing below   ----------

# User behavior function
def behavior1(username,password): 

    client = HttpClient(ssl_verify=False) 

    # API login
    response = client.post('https://self-signed.badssl.com/',
        data={'username':username,'password':password})
    print(response.text)

    sleep(1)

    # for i in range(1):
    #     # send API list customers
    #     response = client.get('/api/mgr/customers?action=list_customer')

    #     # check response
    #     try:
    #         respObj = response.json()
    #     except:
    #         # if anything wrong, put it into stats and logs
    #         Stats.one_error('list_customer response.json() error')
    #         continue

    #     if (respObj['ret'] != 0):        
    #         Stats.one_error('list_customer respObj[ret] error')

    #     sleep(1)

# emulate 10 user's behavior of the same type
for i in range(2): 
    username=f'byhy_{i:04}'
    print(username)
    # run user behavior function in hyload task (a greenlet)
    run_task(behavior1, username, '88888888')
    sleep(1) 

# wait for all hyload tasks to end
wait_for_tasks_done()