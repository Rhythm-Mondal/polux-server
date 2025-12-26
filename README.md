# polux-server
**_Polux_** is a hobby web-app project aimed at replicating some of the capabilities of file management software like google-drive. 
The **polux-server** is the back-end component of this project.
The fron-end companion to this can be found here [polux-client github](https://github.com/Rhythm-Mondal/polux-client). 

# setup
The setup **assumes** that the project is going to run on linux machine with python 3.12 and your system can execute Makefiles\
The run the following make command to setup this project\
```
make setup-loacl
```
This will do the following,

- setup virtualenv `.venv`
- install required packages which includes `black` & `pipreqs`
- setup a sample of a local environment file `.env`
- setup local **postgres** if not installed

Then run the following make command
```
make setup-db-local
```
This will create a db and role for the app to access on you locally install postgres. The database-name, role-name and role password will depend on the `.env` file. You are free to modify this file.

# other utilities 
The project's `Makefile` also has other commands.

- to format use `make format`
- to generate **requirement.txt** use `make gen-reqs`


# API definitions
Below is a list of API's used by this system. the `base url` will be omitted in all APIs only `method`, `path`, `body`, `params` will be mentioned. 
This will also assume that all API will require Bearer token authorization in the headers unless specified otherwise.

## User Registration
```
POST /register

headers: ()
body: {
    email: str
    name: str
    password: str
}

responses:
400 Bad request
201 Ok
```

## User Login
```
POST /login

headers: ()
body: {
    email: str
    password: str
}

responses:
400 Bad request
404 Email or Password is Invalid
200 Ok
{
    access_token: str
}
```

