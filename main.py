import requests
import json

url_oc = "https://www.nseindia.com/option-chain"
url_bn = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
url_nf = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8',
            'accept-encoding': 'gzip, deflate, br'}

sess = requests.Session()

request = sess.get(url_oc, headers=headers, timeout=5)
cookies = dict(request.cookies)
response = sess.get(url_nf, headers=headers, timeout=5, cookies=cookies)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This code can be used when same cookie is used for frequent calls to option chanin API.
# if status code is 401 then cookie needs to be refreshed
# (Not needed every time)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# if(response.status_code==401):
#     print("reset cookies")
#     request = sess.get(url_oc, headers=headers, timeout=5)
#     cookies = dict(request.cookies)
#     response = sess.get(url_nf, headers=headers, timeout=5, cookies=cookies)


if(response.status_code==200):
    #print(response.text)
    data = json.loads(response.text)
    print(data['records']['data'])
    # for item in data['records']['data']:
    #     if(item['expiryDate']=='20-May-2021'):
    #         print(item)