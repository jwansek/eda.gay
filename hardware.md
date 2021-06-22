# general computing
- my main computer that i do most of my work on is a thinkpad x260. it has a 6300U cpu and 8Gb of ram. it runs debian unstable, manjaro and windows for when i need to use shitty proprietary software
- i also use a thinkpad x200. it has an amazing keyboard so its great for writing latex documents. it's librebooted and has no proprietary software at all on it. its running devuan currently since parabola is shit

![x200 with hand for scale](https://eda.gay/img/x200.jpg?h=400&w=200)

# games etc
i have a small form factor dell optiplex 3060 with an 8500T cpu
with 16Gb of memory. its useful to have a windows computer laying
about that i can play games with my friends on

# server
- my nas has a i5-9400t cpu. i went with the t version since it has a lower tdp and therefore it is cheaper to run. it runs truenas (formerly called freenas). it also runs all of my docker containers on a ubuntu server VM. it has 32gb of memory for a nice big zfs cache and is potentially upgradeable to 64gb. it has a passive cooler for quietness. 
- i also have a raspberry pi 3b running pihole and some torrent clients in docker it should be connected to a vpn all the time
- another raspberry pi 3b runs database backups every 2 hours
- both raspberry pis are powered off POE
- docker is shit, using systemd services is better, but docker is used a lot so i wanted to teach myself how to use it

![please disregard the dust](https://eda.gay/img/server.jpg)

- the POE switch is the Netgear GS108PE. it has 4 POE ports which power my raspberry pis and the other switch. speaking of...
- the other switch is the Mikrotik CSS610-8G-2S+in. it has 2 SFP+ ports for 10 gigabit connectivity

all my computers and servers are connected to my periferals with an expensive startech kvm switch. kvm switches are insanely expensive for some reason, especially dual monitor ones

![nice cable ties](/img/nicfan.jpg)

my network card draws like 15w lol and has a fan even when my cpu doesnt
