# Build data analyser
## Description:
Scripts for parsing build and test data from csv files and uploading it into MySQL database

## Requirements:
Installed packages:
* Docker CLI and Daemon for running containers with MySQL and Grafana
* Docker-compose utility to run projects using ```docker-compose.yml```
* Python3 for running ```parser.py```

## How-To:
1. Prepare environment:
```
    # cd project root dir
    docker-compose up -d
    # Create python virtualenv
    virtualenv .venv
    # Activate virtualenv
    source ./.venv/bin/activate
    # Install requirements from requirements.txt
    pip install -r requirements.txt
```

2. Create MySQL database and tables for build data:
```
    # Run parser.py with init command
    ./parser.py init
```

3. Parse build data from text files:
```
    # Run parser.py with parse command
    ./parser.py parse 1.txt 2.txt 3.txt 4.txt
```

4. Calculate statistic for build data:
```
    # Run parser.py with stat command
    ./parser.py stat
```

5. Check data in tables:
```
    # Login to MySQL
    mysql -uroot -ppassword -h127.0.0.1 ci_builds
    # Check data in build_history table
    mysql> select * from build_history limit 10;
    # Check data in build_history_stat table
    mysql> select * from build_history_stat limit 10;
```

## Additional information:
User and Passwords:
* MySQL - ```root/password``` - see ```docker-compose.yml```
* Grafana - ```admin/admin``` - see ```docker-compose.yml```