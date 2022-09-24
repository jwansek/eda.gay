#!/bin/bash

echo -n "Input blog post ID to export: "
read id

sudo docker run -it --entrypoint python3 -v "$(pwd)/edaweb.conf":/app/edaweb.conf -v "$(pwd)/$1":/app/$1 --link mariadb:mysql --rm jwansek/edaweb /app/parser.py update -i $id -u root -m $1
