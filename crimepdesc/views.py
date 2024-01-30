from Cryptodome.Cipher import AES
import pandas as pd
from django.shortcuts import render
# from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from django.views.decorators.cache import cache_control
from secrets import token_bytes
import mysql.connector
# Generate a random key
key = b'Q\xddcq%\x12\x82>\xd0\xdd\xe5\xc5\xb8\t\xbe\x11'
# Use a fixed IV for encryption and decryption
fixed_iv = bytes([0] * 16)

def encrypt(msg):
    cipher = AES.new(key, AES.MODE_EAX, nonce=fixed_iv)
    ciphertext, tag = cipher.encrypt_and_digest(str(msg).encode('utf-8'))
    return f"{ciphertext.hex()}:{tag.hex()}"

def decrypt(encrypted_msg):
    ciphertext, tag = map(bytes.fromhex, encrypted_msg.split(':'))
    cipher = AES.new(key, AES.MODE_EAX, nonce=fixed_iv)
    decrypted_msg = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_msg.decode('utf-8')


import mysql.connector

def store_results_in_database(rawdata, result, normal_table_name, encrypted_input, encrypted_result, encrypted_table_name):
    try:
        # Establish a connection to the MySQL server
        con = mysql.connector.connect(host='localhost', user='root', password='password', database='crime')  # Replace 'your_password' and 'your_database_name' with your MySQL password and database name

        if con.is_connected():
            # Create a cursor object to execute SQL queries
            cursor = con.cursor()

            # Create normal results table if it does not exist
            create_normal_table_query = f"CREATE TABLE IF NOT EXISTS {normal_table_name} (id INT AUTO_INCREMENT PRIMARY KEY, rawdata VARCHAR(255), result VARCHAR(255))"
            cursor.execute(create_normal_table_query)

            # Insert data into the normal results table
            insert_normal_query = f"INSERT INTO {normal_table_name} (rawdata, result) VALUES (%s, %s)"
            normal_data = (rawdata, result)
            cursor.execute(insert_normal_query, normal_data)

            # Create encrypted results table if it does not exist
            create_encrypted_table_query = f"CREATE TABLE IF NOT EXISTS {encrypted_table_name} (id INT AUTO_INCREMENT PRIMARY KEY, encrypted_input VARCHAR(255), result VARCHAR(255))"
            cursor.execute(create_encrypted_table_query)

            # Insert data into the encrypted results table
            insert_encrypted_query = f"INSERT INTO {encrypted_table_name} (encrypted_input, result) VALUES (%s, %s)"
            encrypted_data = (encrypted_input, encrypted_result)
            cursor.execute(insert_encrypted_query, encrypted_data)

            # Commit the changes and close the cursor and connection
            con.commit()
            cursor.close()
            con.close()

    except Exception as e:
        print(f"Error storing results in the database: {e}")


# Load your machine learning models
# model1 = pickle.load(open('C:/Users/Dhanush/Documents/prot/telusko/log.sav', 'rb'))
model2 = pickle.load(open('D:/Downloads/CSM_MODLES/random.sav', 'rb'))
# model3 = pickle.load(open('C:/Users/Dhanush/Documents/prot/telusko/SVC.sav', 'rb'))

def index(request):
    return render(request, 'crimepdesc/index.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkSpam(request):
    if request.method == "POST":
        algo = request.POST.get("algo")
        rawData = request.POST.get("rawdata")

        # Encrypt user input before passing it to the model
        encrypted_input = encrypt(rawData)

        if algo == "RANDOM CLASSIFIER":
            # Decrypt the user input before passing it to the model
        
            # Encrypt the model output before rendering the template
            result = model2.predict([encrypted_input])[0]
            
            return render(request, 'crimepdesc/output.html', {"answer": result})
        elif algo == "SUPPORT VECTOR MACHINE":
            result = model2.predict([encrypted_input])[0]
            res = decrypt(result)
            normal_table_name='text_class_norm'
            encrypted_table_name='text_class_encrypt'
            store_results_in_database(rawData, res, normal_table_name, encrypted_input, result, encrypted_table_name)
            return render(request, 'crimepdesc/output.html', {"answer": res})
        elif algo == "LOGISTIC REGRESSION":
            decrypted_input = decrypt(encrypted_input)
            result = model2.predict([encrypted_input])[0]
            return render(request, 'crimepdesc/output.html', {"answer": result})
    else:
        return render(request, 'crimepdesc/index.html')


