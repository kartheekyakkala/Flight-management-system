from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import hashlib
from datetime import datetime
from bson.objectid import ObjectId
import uuid

from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
app.secret_key = 'samplekey'
db = client['flight_management']
admin_collection = db['admin']
customer_collection = db['customer']
airplane_collection = db['airplane']
airport_collection = db['airport']
flight_collection = db['flights']
reservation_collection = db['reservation']
payment_collection = db['payment']
boardingpass_collection = db['boardingpass']
passanger_collection = db['passanger']



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        print(hashed_password)
        if role == 'admin':
            collection_name = admin_collection
            
        elif role == 'customer':
            collection_name=customer_collection

        else:
            return redirect(url_for('index'))
        user = collection_name.find_one({"email": email, "password": hashed_password})
        if user:
            session['email'] = email
            session['role'] = role
            session['username'] = user['name']
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'customer':
                return redirect(url_for('customer_dashboard'))
        else:
            return redirect(url_for('home'))
        
    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    password = request.form.get('password')
    
    # Hash the password using hashlib
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    user_data = {
        'name': name,
        'email': email,
        'mobile': mobile,
        'password': hashed_password
    }
    customer_collection.insert_one(user_data)
    return redirect(url_for('home'))
    

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html', username=session['username'])
    else:
        return redirect(url_for('home'))
    
@app.route('/customer_dashboard')
def customer_dashboard():
    if 'email' in session and session['role'] == 'customer':
        return render_template('customer_dashboard.html',username=session['username'])
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    session.pop('role', None)      # Remove the role from the session
    return redirect(url_for('home'))  

@app.route('/create_airport', methods=['GET', 'POST'])
def create_airport():
    if request.method == 'POST':
        airport_name = request.form.get('airport_name')
        short_name = request.form.get('short_name')
        location = request.form.get('location')
        description = request.form.get('description')

        # Insert the data into the "airports" collection
        airport_collection.insert_one({
            'airport_name': airport_name,
            'short_name': short_name,
            'location': location,
            'description': description
        })

        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard or appropriate page

    return render_template('create_airports.html')

@app.route('/create_airplane', methods=['GET', 'POST'])
def create_airplane():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        airline = request.form.get('airline')
        seats = request.form.get('seats')

        # Validation (simple example)
        if not name or not airline or not seats:
            flash('All fields are required!')
            return redirect(url_for('create_airplane'))

        # Insert into the database
        airplane = {
            'name': name,
            'airline': airline,
            'seats': seats
        }
        airplane_collection.insert_one(airplane)

        flash('Airplane created successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_airplane.html')

@app.route('/create_flight', methods=['GET', 'POST'])
def create_flight():
    if request.method == 'POST':
        # Get form data
        from_airport = request.form.get('from_airport')
        to_airport = request.form.get('to_airport')
        plane = request.form.get('plane')
        fare = float(request.form.get('fare'))
        seats = int(request.form.get('seats'))
        takeoff = datetime.strptime(request.form.get('takeoff'), '%Y-%m-%dT%H:%M')
        landing = datetime.strptime(request.form.get('landing'), '%Y-%m-%dT%H:%M')

        # Ensure 'from_airport' and 'to_airport' are different
        if from_airport == to_airport:
            return render_template('create_flight.html', error="From and To airports cannot be the same.")

        # Insert into MongoDB
        flight = {
            'from_airport': from_airport,
            'to_airport': to_airport,
            'plane': plane,
            'fare': fare,
            'seats': seats,
            'takeoff': takeoff,
            'landing': landing
        }
        db.flights.insert_one(flight)

        return redirect(url_for('admin_dashboard'))  # Redirect to a suitable page

    # For GET request, render the form
    airports = list(airport_collection.find())
    airplanes = list(airplane_collection.find())
    return render_template('create_flight.html', airports=airports, airplanes=airplanes)


@app.route('/view_airports')
def view_airports():
    airports = list(airport_collection.find())  # Fetch all airports from the database
    return render_template('view_airports.html', airports=airports)


@app.route('/edit_airport/<id>', methods=['GET', 'POST'])
def edit_airport(id):
    # Convert id to ObjectId if necessary
    airport_id = ObjectId(id)
    airport = airport_collection.find_one({"_id": airport_id})
    
    if request.method == 'POST':
        # Get data from the form
        name = request.form['name']
        short_name = request.form['short_name']
        location = request.form['location']
        description = request.form['description']

        # Update the airport in the database
        airport_collection.update_one(
            {"_id": airport_id},
            {"$set": {
                "airport_name": name,
                "short_name": short_name,
                "location": location,
                "description": description
            }}
        )
        return redirect(url_for('view_airports'))
    
    return render_template('edit_airport.html', airport=airport)

@app.route('/delete_airport/<id>')
def delete_airport(id):
    # Convert id to ObjectId if necessary
    airport_id = ObjectId(id)
    airport_collection.delete_one({"_id": airport_id})
    return redirect(url_for('view_airports'))

@app.route('/view_airplanes')
def view_airplanes():
    airplanes = airplane_collection.find()  # Function to fetch all airplanes from the database
    return render_template('view_airplanes.html', airplanes=airplanes)

@app.route('/edit_airplane/<id>', methods=['GET', 'POST'])
def edit_airplane(id):
    # Fetch the airplane by ID
    airplane = airplane_collection.find_one({"_id": ObjectId(id)})
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        airline = request.form['airline']
        seats = request.form['seats']
        
        # Update the airplane details in MongoDB
        airplane_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": name,
                "airline": airline,
                "seats": seats
            }}
        )
        
        return redirect(url_for('view_airplanes'))
    
    return render_template('edit_airplane.html', airplane=airplane)



@app.route('/delete_airplane/<id>', methods=['GET'])
def delete_airplane(id):
    # Delete the airplane document from MongoDB
    airplane_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('view_airplanes'))




from datetime import datetime
@app.route('/view_flights')
def view_flights():
    # Fetch all flights, airports, and airplanes
    flights = list(flight_collection.find())
    airports = list(airport_collection.find())
    airplanes = list(airplane_collection.find())

    # Create dictionaries to map IDs to names
    airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
    airplane_dict = {str(airplane['_id']): airplane['name'] for airplane in airplanes}

    # Format flight details
    formatted_flights = []
    for flight in flights:
        # Convert datetime if needed
        if isinstance(flight['takeoff'], str):
            flight['takeoff'] = datetime.strptime(flight['takeoff'], '%Y-%m-%dT%H:%M')
        if isinstance(flight['landing'], str):
            flight['landing'] = datetime.strptime(flight['landing'], '%Y-%m-%dT%H:%M')

        # Format datetime objects for AM/PM
        flight['takeoff'] = flight['takeoff'].strftime('%Y-%m-%d %I:%M %p')
        flight['landing'] = flight['landing'].strftime('%Y-%m-%d %I:%M %p')

        # Get airport and airplane names
        from_airport_name = airport_dict.get(str(flight['from_airport']), "Unknown")
        to_airport_name = airport_dict.get(str(flight['to_airport']), "Unknown")
        plane_name = airplane_dict.get(str(flight['plane']), "Unknown")

        formatted_flights.append({
            '_id': flight['_id'],
            'from_airport_name': from_airport_name,
            'to_airport_name': to_airport_name,
            'plane_name': plane_name,
            'fare': flight['fare'],
            'seats': flight['seats'],
            'takeoff': flight['takeoff'],
            'landing': flight['landing']
        })

    return render_template('view_flights.html', flights=formatted_flights)


@app.route('/edit_flight/<id>', methods=['GET', 'POST'])
def edit_flight(id):
    flight = flight_collection.find_one({'_id': ObjectId(id)})  # Fetch flight by ID
    if request.method == 'POST':
        from_airport = request.form['from_airport']
        to_airport = request.form['to_airport']
        plane = request.form['plane']
        fare = request.form['fare']
        seats = request.form['seats']
        takeoff = request.form['takeoff']
        landing = request.form['landing']
        flight_collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'from_airport': from_airport,
                'to_airport': to_airport,
                'plane': plane,
                'fare': fare,
                'seats': seats,
                'takeoff': takeoff,
                'landing': landing
            }}
        )
        return redirect(url_for('view_flights'))
    airports = airport_collection.find() 
    airports2 = airport_collection.find()  # Fetch all airports for dropdowns
    airplanes = airplane_collection.find()  # Fetch all airplanes for dropdowns
    return render_template('edit_flight.html', flight=flight, airports=airports,airports2=airports2, airplanes=airplanes)


@app.route('/delete_flight/<id>', methods=['GET'])
def delete_flight(id):
    flight_collection.delete_one({'_id': ObjectId(id)})  # Delete flight from MongoDB
    return redirect(url_for('view_flights'))



from datetime import datetime
@app.route('/cust_view_flights')
def cust_view_flights():
    # Fetch all flights, airports, and airplanes
    flights = list(flight_collection.find())
    airports = list(airport_collection.find())
    airplanes = list(airplane_collection.find())

    # Create dictionaries to map IDs to names
    airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
    airplane_dict = {str(airplane['_id']): airplane['name'] for airplane in airplanes}

    # Format flight details
    formatted_flights = []
    for flight in flights:
        # Ensure 'seats' is an integer
        available_seats = int(flight.get('seats', 0))  # Convert seats to integer if it's a string

        # Skip flights with no available seats
        if available_seats <= 0:
            continue

        # Convert datetime if needed
        if isinstance(flight['takeoff'], str):
            flight['takeoff'] = datetime.strptime(flight['takeoff'], '%Y-%m-%dT%H:%M')
        if isinstance(flight['landing'], str):
            flight['landing'] = datetime.strptime(flight['landing'], '%Y-%m-%dT%H:%M')

        # Format datetime objects for AM/PM
        flight['takeoff'] = flight['takeoff'].strftime('%Y-%m-%d %I:%M %p')
        flight['landing'] = flight['landing'].strftime('%Y-%m-%d %I:%M %p')

        # Get airport and airplane names
        from_airport_name = airport_dict.get(str(flight['from_airport']), "Unknown")
        to_airport_name = airport_dict.get(str(flight['to_airport']), "Unknown")
        plane_name = airplane_dict.get(str(flight['plane']), "Unknown")

        formatted_flights.append({
            '_id': flight['_id'],
            'from_airport_name': from_airport_name,
            'to_airport_name': to_airport_name,
            'plane_name': plane_name,
            'fare': flight['fare'],
            'seats': flight['seats'],
            'takeoff': flight['takeoff'],
            'landing': flight['landing']
        })

    return render_template('customer_view_flights.html', flights=formatted_flights)


@app.route('/book_flight/<flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    if request.method == 'POST':
        # Retrieve form data
        num_passengers = int(request.form['numPassengers'])
        flight_details = request.form['flightDetails']
        passenger_details = []

        for i in range(num_passengers):
            passenger_name = request.form[f'passenger{i + 1}Name']
            passenger_id = request.form[f'passenger{i + 1}Id']
            passenger_details.append({'name': passenger_name, 'id_number': passenger_id})

        card_name = request.form['cardName']
        card_number = request.form['cardNumber']
        card_cvv = request.form['cardCvv']
        card_exp = request.form['cardExp']
        


        # Calculate total amount
        flight_fare = db.flights.find_one({'_id': ObjectId(flight_id)})['fare']
        total_amount = num_passengers * flight_fare
        tax = total_amount * 0.08
        final_amount = total_amount + tax

        # Save booking to the database
        booking_data = {
            'flight_id': ObjectId(flight_id),
            'passengers': passenger_details,
            'card_name': card_name,
            'card_number': card_number,
            'card_cvv': card_cvv,
            'card_exp': card_exp,
            'amount': final_amount,
            'booking_date': datetime.datetime.now()
        }

        reservation_collection.insert_one(booking_data)

        flash('Flight booked successfully!', 'success')
        return redirect(url_for('customer_dashboard'))

    else:
        flight=flight_collection.find_one({'_id': ObjectId(flight_id)})  # Delete flight from MongoDB
        airports = list(airport_collection.find())
        airplanes = list(airplane_collection.find())

        # Create dictionaries to map IDs to names
        airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
        airplane_dict = {str(airplane['_id']): airplane['name'] for airplane in airplanes}

        # Format flight details
        formatted_flights = []
        if isinstance(flight['takeoff'], str):
            flight['takeoff'] = datetime.strptime(flight['takeoff'], '%Y-%m-%dT%H:%M')
        if isinstance(flight['landing'], str):
            flight['landing'] = datetime.strptime(flight['landing'], '%Y-%m-%dT%H:%M')

            # Format datetime objects for AM/PM
        flight['takeoff'] = flight['takeoff'].strftime('%Y-%m-%d %I:%M %p')
        flight['landing'] = flight['landing'].strftime('%Y-%m-%d %I:%M %p')


        from_airport_name = airport_dict.get(str(flight['from_airport']), "Unknown")
        to_airport_name = airport_dict.get(str(flight['to_airport']), "Unknown")
        plane_name = airplane_dict.get(str(flight['plane']), "Unknown")

        formatted_flights.append({
                '_id': flight['_id'],
                'from_airport_name': from_airport_name,
                'to_airport_name': to_airport_name,
                'plane_name': plane_name,
                'fare': flight['fare'],
                'seats': flight['seats'],
                'takeoff': flight['takeoff'],
                'landing': flight['landing']
            })
        print(formatted_flights)
        return render_template('book_flight.html', flight=formatted_flights[0],flightFare=flight['fare'] )
import random 
def generate_seat_numbers(num_passengers):
    rows = 10  # Number of rows in the plane
    seats_per_row = 6  # Number of seats per row
    available_seats = [f"{chr(row + 65)}{seat + 1}" for row in range(rows) for seat in range(seats_per_row)]
    
    if num_passengers > len(available_seats):
        raise ValueError("Not enough seats available")

    return random.sample(available_seats, num_passengers)


@app.route('/make_payment', methods=['POST'])
def make_payment():
    flight_id = request.form.get('flight_id')
    print(flight_id)
    num_passengers = int(request.form.get('numPassengers', 0))
    card_name = request.form.get('cardName')
    card_number = request.form.get('cardNumber')
    card_cvv = request.form.get('cardCvv')
    card_exp = request.form.get('cardExp')
        # Print form data to console
    # Get the user email from session
    user_email = session['email']
    if not user_email:
        print('User not logged in.')
        return redirect(url_for('home'))  # Redirect to login if user is not authenticated
    print(flight_id)
    flight = flight_collection.find_one({'_id': ObjectId(flight_id)})
    if not flight:
        print('Flight not found.')
        return redirect(url_for('customer_dashboard'))  # Redirect to home if flight is not found

    flight_fare = float(flight['fare'])
    total_amount = num_passengers * flight_fare
    tax = total_amount * 0.08
    final_amount = total_amount + tax

    # Generate payment ID
    payment_id = str(uuid.uuid4())
    payment_data = {
        'id': payment_id,
        'amount': final_amount,
        'card_name': card_name,
        'card_number': hashlib.sha256(card_number.encode()).hexdigest(),  # Hash card number for security
        'card_cvv': hashlib.sha256(card_cvv.encode()).hexdigest(),  # Hash CVV for security
        'card_exp': card_exp,
        'status': 'Completed',


    }

    flight = flight_collection.find_one({'_id': ObjectId(flight_id)})

    # Ensure seats is an integer
    if flight:
        current_seats = int(flight.get('seats', 0))  # Convert seats to integer if it's a string
        new_seats = current_seats - num_passengers
        
        flight_collection.update_one(
            {'_id': ObjectId(flight_id)},
            {'$set': {'seats': new_seats}}
        )
    payment_collection.insert_one(payment_data)
    seat_numbers = generate_seat_numbers(num_passengers)

    # Gather passenger details
    passengers = []
    for i in range(num_passengers):
        passenger_name = request.form.get(f'passenger{i + 1}Name')
        passenger_id = request.form.get(f'passenger{i + 1}Id')
        passengers.append({
            'name': passenger_name,
            'id_number': passenger_id,
            'seat_number': seat_numbers[i]
        })
    print(passengers)
    # Create reservation record
    reservation_data = {
        'flight_id': flight_id,
        'user_email': user_email,
        'payment_id': payment_id,
        'passengers': passengers,
        'status': 'Confirmed',
    }
    reservation_id = reservation_collection.insert_one(reservation_data).inserted_id
    passenger_data = {
        'user_email': user_email,
        'reservation_id': reservation_id,
        'passengers': passengers
    }
    passanger_collection.insert_one(passenger_data)
    flash('Flight booked sdfsdfsdfsdfsdf!')
    return redirect(url_for('customer_dashboard')) 


@app.route('/reservations')
def view_reservations():
    # Fetch all reservations from the database
    user_email=session['email']
    reservations = list(reservation_collection.find({'user_email': user_email}))
    
    # Create dictionaries for quick lookups
    airports = list(airport_collection.find())
    planes = list(airplane_collection.find())
    airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
    plane_dict = {str(plane['_id']): plane['name'] for plane in planes}
    
    # Process each reservation
    for reservation in reservations:
        # Fetch flight details
        flight = flight_collection.find_one({'_id': ObjectId(reservation['flight_id'])})
        if flight:
            # Fetch airport and plane details
            from_airport_name = airport_dict.get(str(flight['from_airport']), 'Unknown Airport')
            to_airport_name = airport_dict.get(str(flight['to_airport']), 'Unknown Airport')
            plane_name = plane_dict.get(str(flight['plane']), 'Unknown Plane')
            takeoff_time = flight.get('takeoff', 'Unknown Time')

            # Calculate number of passengers
            num_passengers = len(reservation.get('passengers', []))
            
            # Add details to reservation
            reservation['from_airport_name'] = from_airport_name
            reservation['to_airport_name'] = to_airport_name
            reservation['plane_name'] = plane_name
            reservation['takeoff_time'] = takeoff_time
            reservation['num_passengers'] = num_passengers
        else:
            reservation['from_airport_name'] = 'Unknown Airport'
            reservation['to_airport_name'] = 'Unknown Airport'
            reservation['plane_name'] = 'Unknown Plane'
            reservation['takeoff_time'] = 'Unknown Time'
            reservation['num_passengers'] = 0
    
    return render_template('view_reservations.html', reservations=reservations)
        
@app.route('/generate_pass/<reservation_id>')
def generate_pass(reservation_id):
    # Example session email, replace with actual session handling
    airports = list(airport_collection.find())
    planes = list(airplane_collection.find())
    airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
    plane_dict = {str(plane['_id']): plane['name'] for plane in planes}
    
    # Process each reservation
    reservation=reservation_collection.find_one({'_id': ObjectId(reservation_id)})
    flight = flight_collection.find_one({'_id': ObjectId(reservation['flight_id'])})
    if flight:
            # Fetch airport and plane details
        from_airport_name = airport_dict.get(str(flight['from_airport']), 'Unknown Airport')
        to_airport_name = airport_dict.get(str(flight['to_airport']), 'Unknown Airport')
        plane_name = plane_dict.get(str(flight['plane']), 'Unknown Plane')
        takeoff_time = flight.get('takeoff', 'Unknown Time')
        arrival = flight.get('landing', 'Unknown Time')
        takeoff_time = datetime.strptime(str(takeoff_time), '%Y-%m-%d %H:%M:%S')
        arrival_time = datetime.strptime(str(arrival), '%Y-%m-%d %H:%M:%S')

        print(takeoff_time)
        print(type(takeoff_time))

            # Calculate number of passengers
        num_passengers = len(reservation.get('passengers', []))
            
        # Add details to reservation
        reservation['from_airport_name'] = from_airport_name
        reservation['to_airport_name'] = to_airport_name
        reservation['plane_name'] = plane_name
        reservation['takeoff_time'] = takeoff_time
        reservation['arrival'] = arrival_time
        reservation['num_passengers'] = num_passengers
    return render_template('pass.html', reservation=reservation)


@app.route('/payment_history')
def payment_history():
    # Fetch all reservations from the database
    user_email=session['email']
    reservations = list(reservation_collection.find({'user_email': user_email}))
    
    # Create dictionaries for quick lookups
    airports = list(airport_collection.find())
    planes = list(airplane_collection.find())
    airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
    plane_dict = {str(plane['_id']): plane['name'] for plane in planes}
    
    # Process each reservation
    for reservation in reservations:
        # Fetch flight details
        flight = flight_collection.find_one({'_id': ObjectId(reservation['flight_id'])})
        payment= payment_collection.find_one({'id': reservation['payment_id']})
        amount=payment['amount']
        print(flight)
        if flight:
            # Fetch airport and plane details
            from_airport_name = airport_dict.get(str(flight['from_airport']), 'Unknown Airport')
            to_airport_name = airport_dict.get(str(flight['to_airport']), 'Unknown Airport')
            plane_name = plane_dict.get(str(flight['plane']), 'Unknown Plane')
            takeoff_time = flight.get('takeoff', 'Unknown Time')

            # Calculate number of passengers
            num_passengers = len(reservation.get('passengers', []))
            
            # Add details to reservation
            reservation['from_airport_name'] = from_airport_name
            reservation['to_airport_name'] = to_airport_name
            reservation['plane_name'] = plane_name
            reservation['takeoff_time'] = takeoff_time
            reservation['num_passengers'] = num_passengers
            reservation['amount'] = amount
        else:
            reservation['from_airport_name'] = 'Unknown Airport'
            reservation['to_airport_name'] = 'Unknown Airport'
            reservation['plane_name'] = 'Unknown Plane'
            reservation['takeoff_time'] = 'Unknown Time'
            reservation['num_passengers'] = 0
    
    return render_template('cust_view_payments.html', reservations=reservations)



@app.route('/adm_payment_history')
def adm_payment_history():
    # Fetch all reservations from the database

    reservations = list(reservation_collection.find())
    
    # Create dictionaries for quick lookups
    airports = list(airport_collection.find())
    planes = list(airplane_collection.find())
    airport_dict = {str(airport['_id']): airport['airport_name'] for airport in airports}
    plane_dict = {str(plane['_id']): plane['name'] for plane in planes}
    
    # Process each reservation
    for reservation in reservations:
        # Fetch flight details
        flight = flight_collection.find_one({'_id': ObjectId(reservation['flight_id'])})
        payment= payment_collection.find_one({'id': reservation['payment_id']})
        amount=payment['amount']
        print(flight)
        if flight:
            # Fetch airport and plane details
            from_airport_name = airport_dict.get(str(flight['from_airport']), 'Unknown Airport')
            to_airport_name = airport_dict.get(str(flight['to_airport']), 'Unknown Airport')
            plane_name = plane_dict.get(str(flight['plane']), 'Unknown Plane')
            takeoff_time = flight.get('takeoff', 'Unknown Time')

            # Calculate number of passengers
            num_passengers = len(reservation.get('passengers', []))
            
            # Add details to reservation
            reservation['from_airport_name'] = from_airport_name
            reservation['to_airport_name'] = to_airport_name
            reservation['plane_name'] = plane_name
            reservation['takeoff_time'] = takeoff_time
            reservation['num_passengers'] = num_passengers
            reservation['amount'] = amount
        else:
            reservation['from_airport_name'] = 'Unknown Airport'
            reservation['to_airport_name'] = 'Unknown Airport'
            reservation['plane_name'] = 'Unknown Plane'
            reservation['takeoff_time'] = 'Unknown Time'
            reservation['num_passengers'] = 0
    
    return render_template('adm_view_cust.html', reservations=reservations)
if __name__ == '__main__':
    app.run(debug=True)


