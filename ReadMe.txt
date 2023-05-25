Issue:
  * Organization asked to automate transfer of online sales from CS-cart platform to Balance ERP/Accounting system
  
The script:
  * Retrieves sales of previous date from cs-cart
  * Checks if the client is new or already exists
    > If exists don't change anything
    > If doesn't exist, create new client in Balance database
  * json objects are created, saved as an array in a json file
  * json objects are itterated from json file and uploaded to Balance system.
