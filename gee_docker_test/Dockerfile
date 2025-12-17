## I made this Dockerfile so I could test running a GEE authentication script in a different environment 
## I didn't end up using GEE in the end, so didn't need this. Leaving it here anyway.

FROM python:3.11-slim

# Install gcloud SDK
RUN apt-get update && apt-get install -y curl gnupg
RUN apt-get install apt-transport-https ca-certificates gnupg curl -y

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && apt-get update -y && apt-get install google-cloud-cli -y
    

# Install Python packages
RUN pip install earthengine-api

WORKDIR /app
COPY . .

CMD ["/bin/bash"]
