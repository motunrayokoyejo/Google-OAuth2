### Google OAuth using Python FastAPI 


## Requirements
To run this app on your local machine, you need to meet these base requirements:
- Docker
- Google OAuth client credentials. 

## Getting Started
# Set up
- Go to https://console.cloud.google.com/ 
- Register a service with Google > create a new project 
- Within the new project, go to APIs + Services -> Create credentials -> Configure Consent Screen -> External Users > Name the project again -> Enter support email
- Go back to dashboard > Credentials > Create Creds > OAuth Client ID > web app > define your redirect url of your web app (http://localhost/callback
- Download your credentials as a json file
- copy credentials into the secret.json file
- Clone this repository
- Create an .env file by running cp .env.example .env
- Update your env with the client ID and secret key in the secret.json file
- run `docker compose build` and then `docker compose up`
- navigate to http://localhost/ on your browser
