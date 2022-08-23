# edaweb
My Personal Website

## Notes
Exporting a blog post
`touch hardware.md && sudo docker run -it --entrypoint python3 -v "$(pwd)/edaweb.conf":/app/edaweb.conf -v "$(pwd)/hardware.md":/app/hardware.md --link mariadb:mysql --rm jwansek/edaweb /app/parser.py export -i 5 -u root -o hardware.md`

Updating a blog post
`sudo docker run -it --entrypoint python3 -v "$(pwd)/edaweb.conf":/app/edaweb.conf -v "$(pwd)/hardware.md":/app/hardware.md --link mariadb:mysql --rm jwansek/edaweb /app/parser.py update -i 5 -u root -m hardware.md`
