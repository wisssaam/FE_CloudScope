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
    
    
## 2- Create FunctionGraph
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


## 2bis - Create Function Graph to be notified by mail when new invoice are available
in the function : fgs_send_smn_bills.py

change also those values

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
