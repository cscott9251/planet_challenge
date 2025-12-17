# Planet Technical Assessment - Imaging scheduler Python tool
## Brief instructions

!NOTE!
Program will not run without Postgres database username, password, and the public IP of the VM on which the container containing the Postgres database is running. 
I have omitted these from find_best_opportunity.py in line with security best practices. I can provide these if required, please just ask.

```bash
git clone https://github.com/cscott9251/planet_challenge.git
```

From the root of the cloned directory
```bash
pip install -r requirements.txt
```
```bash
pip install -e .
```
To run the program, simply run type:
```bash
$ planet
```
This will run the opportunity selection pipelines for the period 2024-11-07 - 2024-11-13 by default.
Or, the start date can be specified:
```bash
$ planet ["start date in YYYY-MM-DD format"]
```
Or, from the src/planet_challenge directory:
```bash
$ python __main__.py
```

!NOTE!
Program will not run without Postgres database username, password, and the public IP of the VM on which the container containing the Postgres database is running. 
I have omitted these from find_best_opportunity.py in line with security best practices. I can provide these if required, please just ask.
