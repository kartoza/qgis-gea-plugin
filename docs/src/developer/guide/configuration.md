---
title: EPAL-Eligible Project Area Locator
summary: Visualize historical imagery, access different landscape maps and generate reports for potential afforestation sites.
    - Ketan Bamniya
date: 19-06-2024
some_url: https://github.com/kartoza/qgis-gea-plugin
copyright: Copyright 2024
contact: marketing@geoterra360.pt
license: the reforestation tool is made available to Global Evergreening Global Alliance (GEA) under a non-exclusive, sub-licensable, perpetual, irrevocable, royalty-free licence. This which allows GEA to use and replicate the QGIS plugin and tool for the appointed project areas in Kenya, Uganda, and Malawi; and any other carbon offset future project areas managed, operated, and undertaken by GEA. The reforestation tool concept, functionality, and operations, as well as the physical QGIS plugin are covered, considered, and always remain the Intellectual Property of GT360.
---

# Project setup
<!-- This needs to be changed per project -->

## Clone [PROJECT_NAME] repository

This will clone the [PROJECT_NAME] repository to your machine
```
git clone https://github.com/project/repository.git
```
<!-- Change this to project repository -->

## Set up the project

This will set up the [PROJECT_NAME] project on your machine

```
cd [PROJECT_NAME]
cd deployment
cp docker-compose.override.template.yml docker-compose.override.yml
cp .template.env .env
cd ..
make up
```

Wait until everything is done.

After everything is done, open up a web browser and go to [http://127.0.0.1/](http://127.0.0.1/) and the dashboard will open:

By Default, we can use the admin credential:

```
username : admin
password : admin
```

## Set up different environment

To set up a different environment, for example, the Default credential, or the port of server, open **deployment/.env**.
You can check the description below for each variable.

```
COMPOSE_PROJECT_NAME=[PROJECT_NAME]
NGINX_TAG=0.0.1  -> Change this for different nginx image
DJANGO_TAG=0.0.1 -> Change this for different django image
DJANGO_DEV_TAG=0.0.1 -> Change this for different django dev image

# Environments
DJANGO_SETTINGS_MODULE=core.settings.prod -> Change this to use a different django config file
ADMIN_USERNAME=admin -> Default admin username 
ADMIN_PASSWORD=admin -> Default admin password
ADMIN_EMAIL=admin@example.com -> Default admin email
INITIAL_FIXTURES=True
HTTP_PORT=80 -> Change the port of nginx

# Database Environment
DATABASE_NAME=django -> Default database name
DATABASE_USERNAME=docker -> Default database username
DATABASE_PASSWORD=docker -> Default database password
DATABASE_HOST=db -> Default database host. Change this if you use a cloud database or any new docker container.
RABBITMQ_HOST=rabbitmq

# Onedrive
PUID=1000
PGID=1000
```

After you change the desired variable, run `make up`. This will restart the project with the updated environment.
