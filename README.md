CRUD operations for a customer database, along with an API to find the n youngest customers.

Execute this app with 'python app.py' command.

1) Login:
Before you can perform any operation, you must first authenticate yourself. 

http://127.0.0.1:5000/login
Under the authorization tab of postman, you can enter your credentials.
Username: <name in database>
Password: <date of birth in DDMMYYYY format>

A new user can use the default credentials.
Username: admin
Password: 01012020

Once you are authenticated, you will receive a token which has to be provided for every API call.
This can be passed from the header column.
Key: x-access-token
Value: <generated token>

2) Get all customers

http://127.0.0.1:5000/customer
GET call with the token in headers will fetch all the customers in the database

3) Get customer by id

http://127.0.0.1:5000/customer/<id>
GET call with the id specified in the URL along with the authorization token will fetch the customer whose id matches the given id.

4) Add a customer

http://127.0.0.1:5000/customer
POST call with headers and a body will add that customer to the database. The body should contain:
{
	"name":"demo",
	"dob":"01-01-1824"
} 
note that date of birth should be in DD-MM-YYYY format

5) Delete a customer

http://127.0.0.1:5000/customer/<id>
DELETE call with authorization header will delete the customer with given id from the database.

6) Update customer

http://127.0.0.1:5000/customer/<id>
PUT call with authorization will update the updated_at timestamp of the given customer.

7) n youngest customers

http://127.0.0.1:5000/customer/youngest/<n>
GET call will fetch the youngest n customers from the database