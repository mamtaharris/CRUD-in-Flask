from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy 
import os
import jwt 
from functools import wraps
import datetime
from sqlalchemy import desc
from flask_marshmallow import Marshmallow


file_path = os.path.abspath(os.getcwd())+"\sample_customer.db"

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+file_path

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    dob = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name','dob', 'updated_at')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_customer = Customer.query.filter_by(id = data['id']).first()
        except:
            return make_response('Invalid Token', 401)
        return f(current_customer, *args, **kwargs)

    return decorated

# default path 
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD'])
@app.route('/<path:path>')
def catch_all(path):
    return make_response('This URL is incorrect. Please verify the same.', 404)

# get all the customers in the database
@app.route('/customer', methods = ['GET', 'PUT', 'DELETE', 'HEAD'])
@token_required
def get_all_customers(current_customer):
    if request.method == 'GET':
        try:
            # SELECT * 
            # FROM sample_customer;
            customers = Customer.query.all()
            return customers_schema.jsonify(customers)
        except Exception as e:
            return make_response('Bad Request. Cause: ' + str(e), 400)
    else:
        return make_response('Method not allowed. Supported methods : GET, to get all customers; POST, to add a new customer', 405)

# add a new customer
@app.route('/customer', methods = ['POST'])
@token_required
def create_customer(current_customer):
    try:
        # INSERT INTO sample_customer(name, dob)
        # VALUES ('name', '01-01-1990');
        data = request.get_json()

        # Check if the complete body is given
        if 'name' not in data or 'dob' not in data:
            return make_response('Please enter both name and date of birth of the customer to add a new entry.', 400)

        # Check if the datetime entered is in the correct format
        try:
            data_dob = datetime.datetime.strptime(data['dob'], '%d-%m-%Y')
        except ValueError:
            return make_response('Please enter a valid date. Expected format : DD-MM-YYYY', 400)

        customer = Customer(name=data['name'], dob=data_dob, updated_at=datetime.datetime.now())
        db.session.add(customer)
        db.session.commit()
        return make_response('Customer added!', 200)
    except Exception as e:
        return make_response('Bad Request. Cause: ' + str(e), 400)

# get a customer by his/her id
@app.route('/customer/<int:customer_id>', methods = ['GET', 'POST', 'HEAD'])
@token_required
def get_customer_by_id(current_customer, customer_id):
    if request.method == 'GET':
        try:
            # SELECT * 
            # FROM sample_customer 
            # WHERE id = customer_id;
            customer = Customer.query.filter_by(id=customer_id).first()

            if not customer:
                return make_response('Customer does not exist in the database', 200)
                
            return customer_schema.jsonify(customer)
        except Exception as e:
            return make_response('Bad Request. Cause: ' + str(e), 400)
    else:
        return make_response('Method not allowed. Supported methods : GET, to get customer by id; DELETE, to delete customer; PUT, to update timestamp', 405)

# delete the customer whose id is given
@app.route('/customer/<int:customer_id>', methods = ['DELETE'])
@token_required
def delete_customer(current_customer, customer_id):
    try:
        # DELETE FROM sample_customer
        # WHERE id = customer_id;
        customer = Customer.query.filter_by(id=customer_id).first()
        if not customer:
            return make_response('Customer does not exist in the database', 200)

        db.session.delete(customer)
        db.session.commit()
        return make_response('Customer deleted', 200)
    except Exception as e:
        return make_response('Bad Request. Cause: ' + str(e), 400)

# update the updation timestamp. Further requirements if any were unclear, but can be added.
@app.route('/customer/<int:customer_id>', methods = ['PUT'])
@token_required
def update_customer(current_customer, customer_id):
    try:
        # UPDATE table_name
        # SET updated_at = '01-01-1990',
        # WHERE id = customer_id;
        customer = Customer.query.filter_by(id=customer_id).first()

        if not customer:
            return make_response('Customer does not exist in the database', 200)

        customer.updated_at = datetime.datetime.now()
        db.session.commit()
        return make_response('Time updated', 200)
    except Exception as e:
        return make_response('Bad Request. Cause: ' + str(e), 400)

# find the n youngest customers
@app.route('/customer/youngest/<int:n>', methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'])
@token_required
def youngest_n_customers(current_customer, n):
    if request.method == 'GET':
        try:
            # SELECT * 
            # FROM sample_customer
            # ORDER BY dob DESC
            # LIMIT n;
            youngest_customers = Customer.query.order_by(desc(Customer.dob)).limit(n).all()
            return customers_schema.jsonify(youngest_customers)
        except Exception as e:
            return make_response('Bad Request. Cause: ' + str(e), 400)
    else:
        return make_response('Method not allowed. Supported method : GET.', 405)

# login to get a token which can be used for authentication
@app.route('/login', methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'])
def login():
    if request.method == 'GET':
        try:
            first_customer = Customer.query.filter_by(id=0).first()

            if not first_customer:
                first_customer = Customer(id = 0, name='admin', dob=datetime.date(2020, 1, 1), updated_at=datetime.datetime.now())
                db.session.add(first_customer)
                db.session.commit()

            auth = request.authorization
            if not auth or not auth.username or not auth.password:
                return make_response('Could not verify!', 401, {'WWW-Authenticate':'Basic realm="Login required!"'})
            
            customer = Customer.query.filter_by(name=auth.username).first()

            if not customer:
                return make_response('Could not verify.', 401, {'WWW-Authenticate':'Basic realm="Login required!"'})

            if auth.password == customer.dob.strftime("%d%m%Y"):
                token = jwt.encode({'id':customer.id, 'exp' : datetime.datetime.utcnow()+datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return jsonify({'token':token.decode('UTF-8')})
            return make_response('Could not verify..', 401, {'WWW-Authenticate':'Basic realm="Login required!"'})
        except Exception as e:
            return make_response('Bad Request. Cause: ' + str(e), 400)
    else:
        return make_response('Method not allowed. Supported method : GET.', 405)

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
