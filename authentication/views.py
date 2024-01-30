import mysql.connector
from django.shortcuts import redirect, render
from django.urls import path, include,reverse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login
# Create your views here.
def index(request):
    userid = request.session.get('userid', None)
    # Your index view logic here
    return render(request, "authentication/index.html", {'userid': userid})

import mysql.connector
from django.contrib import messages
from django.shortcuts import render, redirect

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        # Connect to MySQL database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="crime"  # Replace with your actual database name
        )

        mycursor = mydb.cursor()

        # Check if the email already exists in the database
        check_email_sql = "SELECT * FROM user_db WHERE email = %s"
        check_email_val = (email,)
        mycursor.execute(check_email_sql, check_email_val)
        existing_user = mycursor.fetchone()

        if existing_user:
            # Email already exists, handle this situation (e.g., show an error message)
            messages.error(request, "This email is already registered. Please use a different email.")
            return render(request, "authentication/signup.html")

        # Insert user data into MySQL database
        insert_sql = "INSERT INTO user_db (username, email, password) VALUES (%s, %s, %s)"
        insert_val = (username, email, pass1)
        mycursor.execute(insert_sql, insert_val)

        mydb.commit()

        messages.success(request, "Your account has been successfully created")

        return redirect('signin')

    return render(request, "authentication/signup.html")


def signin(request):
    # print("Hello")

    if request.method == "POST":
        email = request.POST['email']  # Assuming the input field in your form is named 'email'
        pass1 = request.POST['pass1']

        # Connect to MySQL database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="crime"  # Replace with your actual database name
        )

        mycursor = mydb.cursor()

        # Check if the email is present in MySQL database
        check_email_sql = "SELECT * FROM user_db WHERE email = %s"
        check_email_val = (email,)
        mycursor.execute(check_email_sql, check_email_val)
        existing_user = mycursor.fetchone()
        print(existing_user)
        if existing_user:
            # Email exists, continue with the authentication process
            # user = authenticate(request, email=email, password=pass1)
            if pass1 == existing_user[2]:
            #     print(pass1)
            #     print(existing_user[2])
            # if user is not None:
                # login(request, user)
                userid = existing_user[1]  # Assuming you want to use email as the user identifier
                request.session['userid'] = userid
                return redirect('index')
            else:
                # print("hii")
                messages.error(request, "Invalid password")
        else:
            # Email does not exist in the database
            messages.error(request, "Email not found")

    # Clear the fields if there's an error
    return render(request, "authentication/signin.html", {'email': '', 'pass1': ''})

def home(request,userid):
    return render(request,"authentication/home.html",{'userid': userid})

def signout(request):
    pass