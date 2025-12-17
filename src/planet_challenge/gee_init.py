import ee 

# ee.Authenticate()
# ee.Initialize(project="uhi-postgis-proj3")

# print("Authorisation and initialisation successful")

def gee_init():

    credentials = ee.ServiceAccountCredentials(
        "planet@uhi-postgis-proj3.iam.gserviceaccount.com",
        "uhi-postgis-proj3-214e01e3433e.json")

    print("Authenticating ee...")
    ee.Authenticate()
    print("Initialising ee with Service Account...")
    ee.Initialize(credentials, project="uhi-postgis-proj3")

    print("Authorisation and initialisation successful")