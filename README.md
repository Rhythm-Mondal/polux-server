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

# run polux-server
To run this project simply run the following command
```
make run
```

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

## Search Users
```
POST /users/search

body: {
    text: str        [optional][>=3 characters][name prefix or email]
    page: int        [optional][defaults to 1]
    page_size: int   [optional][defaults to 10]
}

```

## List Spaces
```
GET /spaces

params: {
    page: int        [optional][if page_size is give defaults to 1]
    page_size: int   [optional][if page is provided defaults to 10]
}

responses:
400 Bad request
401 Unauthorized
404 Not found
200 Ok
{
    spaces: [
        ...,
        {
            id: uuid
            name: str
            created_at: datetime
            updated_at: datetime
        },
        ...
    ]
}

The omission of page and page_size will indicate no pagination.
This will be assumed for all future paginated queries
```

## Create Spaces
```
POST /spaces

body:{
    name: str  [3-128 characters]
}

responses:
400 Bad Request
401 Unauthorized
409 A space with the same name already exists
201 Ok
```

## List Space Files
```
GET /spaces/me/nodes
GET /spaces/{space_id}/nodes

resposes:
400 Bad Request
401 Unauthorized
404 Not found
200 Ok
{
    nodes: [
        ...,
        {
            id: int
            parent_id: int / null
            space_id: uuid
            type: str              [file or folder]
            name: str
            uploader_id: uuid
            created_at: datetime
            updated_at: datetime
            is_shared: bool
            can: {
                open: bool
                download: bool,
                rename: bool,
                copy: bool,
                move: bool,
                paste: bool,
                trash: bool,
                delete: bool,
                share: bool,
            }
        },
        ...
    ]
}
```

## Delete Space
```
DELETE /spaces/{space_id}

params: {
    delete_content: true
}

responses:
400 Bad Request
401 Unauthorized
403 Can not delete this space
403 Can not delete default space
404 Not found
409 Space contains files/folders do you wish delete those as well
200 Ok
```


