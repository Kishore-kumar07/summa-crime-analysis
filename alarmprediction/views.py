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
classifier = joblib.load('D:/Downloads/CSM_MODLES/classifier.joblib')
encoder = joblib.load('D:/Downloads/CSM_MODLES/encoder.joblib')

def encrypt(msg):
    cipher = AES.new(key, AES.MODE_EAX, nonce=fixed_iv)
    ciphertext, tag = cipher.encrypt_and_digest(str(msg).encode('utf-8'))
    return f"{ciphertext.hex()}:{tag.hex()}"

def decrypt(encrypted_msg):
    ciphertext, tag = map(bytes.fromhex, encrypted_msg.split(':'))
    cipher = AES.new(key, AES.MODE_EAX, nonce=fixed_iv)
    decrypted_msg = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_msg.decode('utf-8')

def store_results_in_database(month_num, day, hour, district, primary_type,
                               encrypted_month_num, encrypted_day, encrypted_hour,
                               encrypted_district, encrypted_primary_type, decrypted_prediction):
    try:
        # Establish a connection to the MySQL server
        con = mysql.connector.connect(host='localhost', user='root', password='password')

        if con.is_connected():
            # Create a cursor object to execute SQL queries
            cursor = con.cursor()

            # Create a new database if it does not exist
            database_name = 'crime'  # Replace with your desired database name
            create_database_query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
            cursor.execute(create_database_query)
            print(f"Database '{database_name}' created successfully")

            # Switch to the new database
            cursor.execute(f"USE {database_name}")

            # Create a new table for normal results if it does not exist
            normal_table_name = 'normal_results'  # Replace with your desired table name for normal results
            create_normal_table_query = f"CREATE TABLE IF NOT EXISTS {normal_table_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                                          month_num VARCHAR(255), day VARCHAR(255), hour VARCHAR(255), \
                                          district VARCHAR(255), primary_type VARCHAR(255), \
                                          decrypted_prediction VARCHAR(255))"
            cursor.execute(create_normal_table_query)
            print(f"Table '{normal_table_name}' created successfully")

            # Create a new table for encrypted results if it does not exist
            encrypted_table_name = 'encrypted_results'  # Replace with your desired table name for encrypted results
            create_encrypted_table_query = f"CREATE TABLE IF NOT EXISTS {encrypted_table_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                                           encrypted_month_num VARCHAR(255), encrypted_day VARCHAR(255), \
                                           encrypted_hour VARCHAR(255), encrypted_district VARCHAR(255), \
                                           encrypted_primary_type VARCHAR(255), \
                                           decrypted_prediction VARCHAR(255))"
            cursor.execute(create_encrypted_table_query)
            print(f"Table '{encrypted_table_name}' created successfully")

            # Insert data into the normal results table
            insert_normal_query = f"INSERT INTO {normal_table_name} (month_num, day, hour, district, primary_type, \
                                  decrypted_prediction) VALUES (%s, %s, %s, %s, %s, %s)"
            normal_data = (month_num, day, hour, district, primary_type, decrypted_prediction)
            cursor.execute(insert_normal_query, normal_data)

            # Insert data into the encrypted results table
            insert_encrypted_query = f"INSERT INTO {encrypted_table_name} (encrypted_month_num, encrypted_day, encrypted_hour, \
                                     encrypted_district, encrypted_primary_type, decrypted_prediction) \
                                     VALUES (%s, %s, %s, %s, %s, %s)"
            encrypted_data = (encrypted_month_num, encrypted_day, encrypted_hour, encrypted_district,
                              encrypted_primary_type, decrypted_prediction)
            cursor.execute(insert_encrypted_query, encrypted_data)

            # Commit the changes and close the cursor and connection
            con.commit()
            cursor.close()
            con.close()

    except Exception as e:
        print(f"Error storing results in the database: {e}")

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    return render(request, 'alarmpred/index.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkSpam(request):
    if request.method == "POST":
        # Get feature values from the form
        month_num = request.POST.get("month_num")
        day = request.POST.get("day")
        hour = request.POST.get("hour")
        district = request.POST.get("district")
        primary_type = request.POST.get("primary_type")

        # Encrypt each feature value separately
        encrypted_month_num = encrypt(month_num)
        encrypted_day = encrypt(day)
        encrypted_hour = encrypt(hour)
        encrypted_district = encrypt(district)
        encrypted_primary_type = encrypt(primary_type)

        # Create a new instance with the encrypted feature
        new_instance = [[encrypted_month_num, encrypted_day, encrypted_hour, encrypted_district, encrypted_primary_type]]

        # Transform the new instance using the pre-trained encoder
        new_instance_encoded = encoder.transform(new_instance)

        # Predicting the label for the encrypted input
        encrypted_prediction = classifier.predict(new_instance_encoded)

        # Decrypt the result
        decrypted_prediction = decrypt(encrypted_prediction[0])

        # Store the results in the MySQL database
        store_results_in_database(month_num, day, hour, district, primary_type,
                                   encrypted_month_num, encrypted_day, encrypted_hour,
                                   encrypted_district, encrypted_primary_type, decrypted_prediction)

        return render(request, 'alarmpred/output.html', {"answer": int(decrypted_prediction)})
    else:
        return render(request, 'alarmpred/index.html')
