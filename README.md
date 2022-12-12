# Create a FunctionGraph to download Flexible Engine bills in a specific Bucket 
## 1- Create Orange Developer Account

Orange Developer : https://developer.orange.com/signin?r=/apis/cloudstorecustomerspace/overview </br>
Use API: Cloud Customer Space API </br>

change this varible in the code : cloudstore_credentials = 
```json
{
            "auth_header":"Basic WWczTF ...", 
            "api_key": "P+AuA5qT3UGLC+eQXgCZg ...",
            "client": {"id" : "Yg3LXR ...", "secret" : "QTCHs ..."
            }
}
```
    
    
## 2- Create FunctionGraph (fgs_download_fe_bills.py)
### Code:
Copy/Paste the code in the "Edit code inline" field</br>
Dependencies=select the dependency named "esdk_obs_python-3x". This dependency is necesary to interact with fE Object storage (OBS)</br>

### Configuration:
Memory (MB)=1024Mo
Agency=Create and use an agency
Environment variables:
- objBucket=NameOfTheBucket
- obsAddress=oss.eu-west-0.prod-cloud-ocb.orange-business.com	
- contract_id=OCB000XXX
- document_type=bills
- document_type=3

document_type [ bills, invoices, reports, partialBills, partialConsumptionRatedReports, comsumptionRatedReports ]


## 2bis - Create FunctionGraph (fgs_send_smn_bills.py)

To be notified by mail when new invoice are available

Change "cloudstore_credentials" and those values :

```{
        "identity": {
        "methods": [
            "password"
        ],
        "password": {
            "user": {
            "name": "first.lasname",
            "password": "yourApiPassword",
            "domain": {
                "name": "OCB000XXX"
            }
            }
        }
        },
        "scope": {
        "project": {
            "id": "fa742 ... Your Project ID"
        }
        }
    }
 ```
 
 ### SMN
 You have to create SMN on FE and use it
 
In the function "send_smn_msg"
Change the URL value with you SMN value (URN ID) <br>
     url = "https://smn.eu-west-0.prod-cloud-ocb.orange-business.com/v2/fa7426a17fe246698cf9a475f4254099/notifications/topics/urn:smn:eu-west-0:fa7426a17fe246698cf9a475f4254099:9469994203fa42f5b51cba3b78b55549_dedicated_queue_dli_topic/publish"

