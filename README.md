# Bertrand_powered_by_Spock
A classical first-order predical logic calculator with set theory.

You can view the operation of this application at https://bertrand.euclidpanopolis.com.

This is a python project set up in the flask framework with a javascript/html frontend (entirely designed by me; please note that web design is not my forte).  It was a learning project on how to write a programming language (which is really only a calculator at this time).  I wrote the scanner, parser, and lexer/evaluator entirely on my own.  Eventually, the core Spock language will be written entirely in webassembler.  Bertrand is the API and Spock is the language engine/JIT interpreter.

Here is the latest release: https://github.com/epanopolis/Bertrand_powered_by_Spock/releases/tag/first_order_logic_calculator

Here are some basic installation instructions:

1. Install the package release and its subdirectories into a root package directory named "bertrand" and point your URI server to the folder containing the package where you can install your wsgi server code.

2. Create a WSGI server and configure it.

3. Create an application file in the same directory that contains bertrand and make sure it has the following import statement:

"from bertrand import create_app".

4. Make sure your application file has the following statements:

app = create_app() 

application = app

5. The application file does not need to be named "app" or "application" but a WSGI server will probably need those names in order to operate.

6. Start up the server and you are ready to log-in to your URI.  Instructions for using the system are in the left window of the user interface and available by way of link called "Lexicon".

0.1.0 First operational usage. 2025-10-05

0.1.1 Operation of substitution. 2025-10-08

0.1.2 Set containers and value binding. 2025-10-11
