#!/bin/bash

echo -n "Input blog post title: "
read title

echo -n "Input blog post category: "
read category

sudo docker run -it --entrypoint python3 -v "$(pwd)/edaweb.conf":/app/edaweb.conf -v "$(pwd)/$1":/app/$1 --link mariadb:mysql --rm jwansek/edaweb /app/parser.py save -m /app/$1 -u root -c $category -t $title
