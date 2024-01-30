import mysql.connector
from Cryptodome.Cipher import AES
import pandas as pd
from django.shortcuts import render
from sklearn.preprocessing import OneHotEncoder
from django.views.decorators.cache import cache_control
import joblib
# Assuming key and fixed_iv are defined as mentioned in your code
key = b'Q\xddcq%\x12\x82>\xd0\xdd\xe5\xc5\xb8\t\xbe\x11'
fixed_iv = bytes([0] * 16)

# Load the classifier and encoder
classifier = joblib.load('D:/Downloads/CSM_MODLES/arrest_classifier_1.joblib')
encoder = joblib.load('D:/Downloads/CSM_MODLES/arrest_encoder_1.joblib')

def encrypt(msg):
    cipher = AES.new(key, AES.MODE_EAX, nonce=fixed_iv)
    ciphertext, tag = cipher.encrypt_and_digest(str(msg).encode('utf-8'))
    return f"{ciphertext.hex()}:{tag.hex()}"

def decrypt(encrypted_msg):
    ciphertext, tag = map(bytes.fromhex, encrypted_msg.split(':'))
    cipher = AES.new(key, AES.MODE_EAX, nonce=fixed_iv)
    decrypted_msg = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_msg.decode('utf-8')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    return render(request, 'probprediction/index.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkSpam(request):
    if request.method == "POST":
        # Get feature values from the form
        primary_type = request.POST.get("primary_type")
        year = int(request.POST.get("year"))
        month = int(request.POST.get("month"))
        location_description = request.POST.get("location_description")
        time_of_day = request.POST.get("time_of_day")
        season = request.POST.get("season")

        # Encrypt each feature value separately
        encrypted_primary_type = encrypt(primary_type)
        encrypted_year = encrypt(year)
        encrypted_month = encrypt(month)
        encrypted_location_description = encrypt(location_description)
        encrypted_time_of_day = encrypt(time_of_day)
        encrypted_season = encrypt(season)

        # Create a new instance with the encrypted feature values
        new_instance = [[
            encrypted_primary_type,
            encrypted_year,
            encrypted_month,
            encrypted_location_description,
            encrypted_time_of_day,
            encrypted_season
        ]]

        # Transform the new instance using the pre-trained encoder
        new_instance_encoded = encoder.transform(new_instance)

        # Predicting the label and probability for the encrypted input
        encrypted_prediction_prob = classifier.predict_proba(new_instance_encoded)
        encrypted_prediction = classifier.predict(new_instance_encoded)

        # Decrypt the result
        decrypted_prediction = decrypt(encrypted_prediction[0])

        # Store the results in the MySQL database
        store_results_in_database(primary_type, year, month, location_description, time_of_day, season, decrypted_prediction, encrypted_prediction_prob[0])

        return render(request, 'probprediction/output.html', {"answer": decrypted_prediction, "probability": encrypted_prediction_prob[0]})
    else:
        return render(request, 'probprediction/index.html')
def store_results_in_database(primary_type, year, month, location_description, time_of_day, season, decrypted_prediction, probability):
    try:
        # Convert NumPy float to Python float
        probability_float = float(probability[1])

        # Convert NumPy array to a string for MySQL storage
        probability_str = ",".join(map(str, probability))

        # Establish a connection to the MySQL server
        con = mysql.connector.connect(host='localhost', user='root', password='password')

        if con.is_connected():
            # Create a cursor object to execute SQL queries
            cursor = con.cursor()

            # Create a new database if it does not exist
            database_name = 'crime'
            create_database_query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
            cursor.execute(create_database_query)
            print(f"Database '{database_name}' created successfully")

            # Switch to the new database
            cursor.execute(f"USE {database_name}")

            # Create a new table 'arrest_prob' if it does not exist
            table_name = 'arrest_prob'
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                                  primary_type VARCHAR(255), year INT, month INT, location_description VARCHAR(255), \
                                  time_of_day VARCHAR(255), season VARCHAR(255), \
                                  prediction VARCHAR(255), probability FLOAT)"
            cursor.execute(create_table_query)
            print(f"Table '{table_name}' created successfully")

            # Insert data into the 'arrest_prob' table
            insert_query = "INSERT INTO arrest_prob (primary_type, year, month, location_description, time_of_day, season, prediction, probability) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            data = (primary_type, year, month, location_description, time_of_day, season, decrypted_prediction, probability_float)
            cursor.execute(insert_query, data)

            # Create a new table 'arrest_probs' if it does not exist
            encrypted_table_name = 'arrest_probs_1'
            create_encrypted_table_query = f"CREATE TABLE IF NOT EXISTS {encrypted_table_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                                            primary_type VARCHAR(255), year VARCHAR(255), month VARCHAR(255), \
                                            location_description VARCHAR(255), time_of_day VARCHAR(255), \
                                            season VARCHAR(255), prediction VARCHAR(255), probability VARCHAR(255))"

            cursor.execute(create_encrypted_table_query)
            print(f"Table '{encrypted_table_name}' created successfully")

            # Encrypt the values
            encrypted_primary_type = encrypt(primary_type)
            encrypted_year = encrypt(year)
            encrypted_month = encrypt(month)
            encrypted_location_description = encrypt(location_description)
            encrypted_time_of_day = encrypt(time_of_day)
            encrypted_season = encrypt(season)

            # Convert NumPy array to a string for MySQL storage
            encrypted_probability_str = ",".join(map(str, probability))

            # Insert data into the 'arrest_probs' table
            insert_encrypted_query = "INSERT INTO arrest_probs_1 (primary_type, year, month, location_description, time_of_day, season, prediction, probability) \
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            encrypted_data = (encrypted_primary_type, encrypted_year, encrypted_month, encrypted_location_description,
                              encrypted_time_of_day, encrypted_season, decrypted_prediction, encrypted_probability_str)
            cursor.execute(insert_encrypted_query, encrypted_data)

            # Commit the changes and close the cursor and connection
            con.commit()
            cursor.close()
            con.close()

    except Exception as e:
        print(f"Error storing results in the database: {e}")
