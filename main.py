"""
Script runs to upload online sales from cs-cart platform to balance server.
"""
import requests
from datetime import datetime as dt, timedelta as td
import logging
from requests.exceptions import HTTPError
import json

# log file
logging.basicConfig(filename='info.txt', encoding='utf-8', level=logging.INFO)
logging.basicConfig(filename='error.txt', encoding='utf-8', level=logging.ERROR)

# previous day
prev_day = (dt.today() - td(days=1)).date().strftime('%m/%d/%Y')

# last 30 days / not completely sure this going to be useful, but we'll see
prev_30_days = (dt.today() - td(days=30)).date().strftime('%m/%d/%Y')

# list of cs-cart order statuses: "open", "completed", "accepted", "picked up"
status_list = ["O", "C", "A", "P"]

# for authentication on cs-cart
payload = {}
headers = {
    'Authorization': 'Basic X'
}

# for balance, used in return_total_items() and list_orderIds() functions
url_balance = "https://cloud.balance.ge/sm/o/Balance/1550/hs/Exchange/Sale"

balance_headers = {
    'Authorization': 'Y'
}

logging.info('upload date - ' + str(dt.today()))


# return number of total items from orders

def return_total_items(current_date=prev_day, retrieve_last_30_days=False):
    """
    @param: current_date - will be day before of code execution. By default, is day before.
    @param: retrieve_last_30_days - does what the name says. By default, it's False.
    """
    logging.info("started retrieving total items")
    url_total_items = ""
    if not retrieve_last_30_days:
        url_total_items = "http://nido.ge/api/orders?period=C&time_from=" + str(current_date) + "&time_to=" + \
                          str(current_date) + "&status[]=O&status[]=C&status[]=A&status[]=P&items_per_page=1"

    else:
        url_total_items = "http://nido.ge/api/orders?period=C&time_from=" + str(prev_30_days) + "&time_to=" + \
                          str(current_date) + "&status[]=O&status[]=C&status[]=A&status[]=Pstatus[]=O&status[]=C&status[]=A&status[]=P&items_per_page=1"

    try:
        responses = requests.request("GET", url_total_items, headers=headers, data=payload).json()

    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')

    except Exception as err:
        logging.error(f'Other error occurred: {err}')

    else:
        logging.info('total items - ' + str(responses['params']['total_items']))
        return responses['params']['total_items']


# make list of order_id-s
def list_orderIds(items_per_page=return_total_items(), current_date=prev_day, retrieve_last_30_days=False):
    """
    @param: current_date - will be day before of code execution. By default, its day before.
    @param: retrieve_last_30_days - does what the name says. By default, it's False.
    @param: status - will be empty here, but needs to run for each item in status_list
    """
    logging.info('Getting list of order ids')
    url = ""
    if not retrieve_last_30_days:
        url = "http://nido.ge/api/orders?period=C&time_from=" + str(current_date) + "&time_to=" + \
              str(current_date) + "&status[]=O&status[]=C&status[]=A&status[]=P&items_per_page=" + items_per_page

    else:
        url = "http://nido.ge/api/orders?period=C&time_from=" + str(prev_30_days) + "&time_to=" + \
              str(current_date) + "&status[]=O&status[]=C&status[]=A&status[]=P&items_per_page=" + items_per_page

    try:
        responses = requests.request("GET", url, headers=headers, data=payload).json()

    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')

    except Exception as err:
        logging.error(f'Other error occurred: {err}')

    else:
        for order in responses['orders']:
            logging.info(f'order #: {order["order_id"]}')
        return responses['orders']


# check full name in balance clients, if name exists keep it, if not add to database

def balance_clients_update(fullName, ID, email):
    """
    @param: fullName - full name of the client
    @param: ID - should be filled with mobile number
    @param: email - email of the user
    """
    clients_url = 'https://cloud.balance.ge/sm/o/Balance/1550/hs/Exchange/Clients'
    logging.info('Update client info')
    try:
        response = requests.request('GET', url=clients_url + '?Name=' + fullName, headers=balance_headers, data=payload,
                                    verify=False)

    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')

    except Exception as err:
        logging.error(f'Other error occurred: {err}')

    else:
        if response.reason.lower() == "ok":
            logging.info(f'{fullName} already existts')
            return ID
        elif response.reason.lower() == "not found":
            logging.info(f'{fullName} is being added')
            balance_payload = \
                [
                    {
                        "uid": "",
                        "Name": fullName,
                        "Group": "00000000-0000-0000-0000-000000000000",
                        "IsGroup": "false",
                        "FullName": fullName,
                        "ID": ID,
                        "LegalForm": "ფიზიკური პირი",
                        "Currency": "GEL",
                        "VATType": "არ არის დღგ-ს გადამხდელი",
                        "ByAgreements": "true",
                        "MainAgreement": "43e6b238-6a46-11e8-80c2-0050569d8876",
                        "ReceivablesAccount": "1410.01",
                        "CashFlowArticle": "9c947788-1ad8-11e7-9657-2c4138014f0e",
                        "AdvancesAccount": "3120",
                        "SettlementByDocuments": "false",
                        "IsPlannedAccruals": "false",
                        "VATArticle": "9c947776-1ad8-11e7-9657-2c4138014f0e",
                        "LegalAddress": "",
                        "PhysicalAddress": "",
                        "Phone": ID,
                        "Fax": "",
                        "Email": email,
                        "PostAddress": "",
                        "AdditionalInformation": "",
                        "Country": "9c947673-1ad8-11e7-9657-2c4138014f0e",
                        "ExtCode": "",
                        "BankAccount": "",
                        "PriceType": "00000000-0000-0000-0000-000000000000",
                        "Code": "001690",
                        "Plannedaccruals": "ТаблицаЗначений",
                        "ContactInformation": [
                        ],
                        "SettlementConditions": [
                        ]
                    }
                ]

            try:
                logging.info('adding the client to database.')
                rsp = requests.request('PUT', url=clients_url, json=balance_payload, headers=balance_headers,
                                       verify=False)

            except HTTPError as http_err:
                logging.error(f'2 HTTP error occurred: {http_err}')

            except Exception as err:
                logging.error(f'2 Other error occurred: {err}')

            else:
                logging.info(f'{fullName} added')
                return ID


# generate JSON file to upload to balance

def get_json_sales(order_ID):
    """
    order_ID: individual order ID, which is iterated through available order ids
    """
    logging.info('Generating JSON file.')
    # url for getting orders by ID
    url_ids = "http://nido.ge/api/orders/"

    # template json formats for main body seperately and items seperately, should get joined
    main_payload = \
        [
            {
                "uid": "",
                "Date": "",
                "VATTaxable": "იბეგრება დღგ-ით",
                "OperationType": "მიწოდება კომფენსაციით",
                "CashRegister": "",
                "TheMarketPriceShouldAppearInTheInvoice": "",
                "PaymentDate": "",
                "Branch": "a2abac1b-1ad8-11e7-9657-2c4138014f0e",
                "Department": "BT - ონლაინ გაყიდვები",
                "Warehouse": "MW",
                "Client": "",
                "Agreement": "",
                "AmountIncludesVAT": "",
                "PriceType": "",
                "Currency": "GEL",
                "CurrencyRate": "",
                "ReceivablesAccount": "1410.01",
                "AdvancesAccount": "",
                "Comments": "",
                "VATExpenseAccount": "",
                "DifferenceAccount": "",
                "ReceivablesWriteoffAccount": "",
                "VATArticle": "",
                "DoesNotAffectReceivables": "",
                "PrimaryDocument": "",
                "RevenuesAndExpensesAnalytics": "",
                "AdditionalDetails": [
                    {
                        "AmPropertyount": "",
                        "Importance": "",
                        "TextField": ""
                    }
                ],
                "Payment": [
                ],
                "PaidDownPayments": [
                ],
                "GiftCertificates": [
                ],
                "Others": [
                ],
                "Items": [
                ]
            }
        ]

    # items payload that will be appended to main json body
    items_payload = \
        {
            "SalesOrder": "",
            "StringCode": "",
            "Consultant": "",
            "Price": "",
            "Quantity": "",
            "Unit": "ცალი",
            "Item": "",
            "DiscountedPrice": "",
            "Discount": "",
            "Amount": "",
            "AccountNumber": "",
            "VATPayableAccount": "",
            "IncomeAccount": "",
            "ExpensesAccount": "",
            "RevenuesAndExpensesAnalytics": ""
        }

    # get order details
    orders = requests.request("GET", url_ids + order_ID, headers=headers, data=payload).json()

    # change values in main body, set different variable which will return the json to default
    main_payload_copy = main_payload.copy()
    main_payload_copy[0]["Date"] = dt.fromtimestamp(int(orders["timestamp"])).isoformat()
    main_payload_copy[0]["Client"] = balance_clients_update(fullName=(orders['firstname'] + " " + orders['lastname']),
                                                            ID=orders['phone'],
                                                            email=orders['email'])
    main_payload_copy[0]["Comments"] = str(orders['order_id'])
    main_payload_copy[0]["PrimaryDocument"] = str(orders['order_id'])

    # iterate through individual products in each order and add items to main body
    for product in orders["products"]:

        # set copy of items json for returning to default easily
        items_payload_copy = items_payload.copy()

        # if product price is zero then output should be zero, else actual spent price
        if str(orders['products'][product]['price']) == "0.00":
            items_payload_copy["Price"] = '0.00'
        else:
            # should take into consideration the discount, if `keyerror` is returned then just fetch price
            print(orders['order_id'] + " " + orders['promotion_ids'])
            if orders['promotion_ids'] == '':
                logging.info(f'{orders["order_id"]} without discount')
                items_payload_copy["Price"] = str(float(orders['products'][product]['price']))
            else:
                prom_id = orders['promotion_ids']
                discount = 1 - float(orders['promotions'][prom_id]['bonuses'][0]['discount_value']) / 100
                items_payload_copy["Price"] = str(float(orders['products'][product]['price']) * discount)

        items_payload_copy["Quantity"] = str(orders['products'][product]['amount'])
        items_payload_copy["Item"] = orders['products'][product]['product_code']
        items_payload_copy["Amount"] = str(float(orders['products'][product]['amount']) *
                                           float(items_payload_copy["Price"]))

        # append the products to json main body
        main_payload_copy[0]["Items"].append(items_payload_copy)

    # extra "if" to check if shipment was paid, if it was, create extra item
    if orders["shipping_cost"] != "0.00":
        # clean up inputs first
        items_payload_copy = items_payload.copy()

        # add input
        main_payload_copy[0]["OperationType"] = "მიწოდება კომფენსაციის გარეშე"
        items_payload_copy["Price"] = str(orders["shipping_cost"])
        items_payload_copy["Quantity"] = "1"
        items_payload_copy["Item"] = "TRSX-5"
        items_payload_copy["Amount"] = str(orders["shipping_cost"])
        main_payload_copy[0]["Items"].append(items_payload_copy)

        print("shipping added")

    logging.info('JSON generated.')
    return main_payload_copy


# to the actual uploading to balance server
logging.info('Uploading to Balance server')

# save to json object and create an array
json_objects = []

# clear everything in json file
with open("objects.json", 'w') as j:
    pass

for i in list_orderIds():

    to_json = get_json_sales(str(i['order_id']))
    json_objects.append(to_json)

with open("objects.json", "w") as j:
    json.dump(json_objects, j)

# open json file, iterate through json objects and upload them one by one
with open("objects.json", 'r') as f:
    objects = json.load(f)

for obj in objects:
    try:
        logging.info('uploading sales')
        response = requests.request("PUT", url_balance, headers=balance_headers, json=obj, verify=False)

    except HTTPError as http_err:
        logging.error(f'2 HTTP error occurred: {http_err}')

    except Exception as err:
        logging.error(f'2 Other error occurred: {err} - {obj[0]["Comments"]}')

    else:
        logging.info(f"{response.status_code} - {response.reason} - {obj[0]['Comments']}")

logging.info('Upload finished - ' + str(dt.today()))
# the end
