# Bertrand_powered_by_Spock
A classical first-order predical logic calculator with set theory.

You can view the operation of this application at https://bertrand.euclidpanopolis.com.

Excuse my "newbie" first publication of a GitHub repository.

1. Install the package and its subdirectories into a root directory named
"bertrand" and point your URI server to it.

2. Create a WSGI server and configure it.

3. Create an application file in the same directory that contains
bertrand and make sure it has the following import statement:
"from bertrand import create_app".

4. Make sure your application file has the following statements:
app = create_app() 
application = app

5. The application file does not need to be named "app" or "application" but a
WSGI server will need them in order to operate.

6. Start up the server and you are ready to log-in to your URI.  Instructions
for using the system are in the input window of the user interface and available
by way of links on the interface.

0.1.0 First operational usage. 2025-10-05

0.1.1 Operation of substitution. 2025-10-08

0.1.2 Set containers and value binding. 2025-10-11
