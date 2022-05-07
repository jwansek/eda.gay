# general computing
- my main computer that i do most of my work on is a thinkpad x260. it has a [6500U cpu](https://eda.gay/thought?id=13#Intel+i7-6500u) and 8Gb of ram. it runs debian unstable, manjaro and windows for when i need to use shitty proprietary software
- i also use a [thinkpad x200](https://eda.gay/thought?id=13#Intel+Core+2+Duo+P8400). it has an amazing keyboard so its great for writing latex documents. it's librebooted and has no proprietary software at all on it. it runs debian unstable too :3

![x200 with hand for scale](https://eda.gay/img/x200.jpg?h=400&w=200) ![libreboot](/img/libreboot.jpg?h=400&w=200)

me flashing the bios to libreboot with a raspberry pi

# games etc
i have a small form factor dell optiplex 3060 with an [8500T cpu](https://eda.gay/thought?id=13#Intel+Core+i5-8500T) with 16Gb of memory. its useful to have a windows computer laying about that i can play games with my friends on

# server(s)
![please disregard the dust](https://eda.gay/img/lackrack1.jpg)

here it is! server racks are very expensive, so i'm using a [lackrack](https://wiki.eth0.nl/index.php/LackRack) instead. from top to bottom there is:

0. on top there is a [thinkpad t30](https://eda.gay/thought?id=13#Intel+Mobile+Pentium+4-M+1.8+GHz) being used as a CUPS print server. it is connected to a Star LC-10 dot matrix printer. i use the old t30 for this since its the only computer i have with a parallel port. [here's a video of the really old printer running.](https://nc.eda.gay/s/HbbCmCZdFJHmHAB) also there is a dock for the x200. finally a keyboard for the top kvm switch and a couple game controllers.
1. a shitty old vga/PS2 kvm switch. connected to it are the raspberry pis, the nas, and the print server (stuff i dont need to access often)
2. a startech 4 port dual monitor kvm switch (SV431DD2DUA). connected to it are the dell optiplex, the x260 dock, the x200 dock, and the fedora 1u.
3. the first shelf has a Netgear GS108PE POE switch which powers 3x raspberry pis and the other switch. there's also a hard drive behind for backups and the dell optiplex 3060 windows pc.
4. a brush cable management thingy
5. Mikrotik CSS610-8G-2S+in 10gig switch, 3x raspberry pi 3bs, and a dvd drive connected to the server below. one of the raspberry pis is a torrent client and the other is my DNS server, using unbound and pihole. it also does database backups, and is also my git server. the third one is still being setup.
6. a 1u server. its gonna be a pfsense router later, but for now it runs fedora workstation. it has an [AMD A4-5000](https://eda.gay/thought?id=13#AMD+A4-5000) 15W quad core CPU with hardware AES. It has 8Gb of memory and a powerful intel i350 dual port nic.
7. below is my main server/nas. it has an [i5-9400t](https://eda.gay/thought?id=13#Intel+Core+i5-9400T) 6 core cpu. i went with the t version since it has a lower tdp and therefore it is cheaper to run. it runs truenas (formerly called freenas). it also runs all of my docker containers on a ubuntu server VM. it has 32gb of memory for a nice big zfs cache and is potentially upgradeable to 64gb. it has a passive cooler for quietness. click [here](https://eda.gay/services) to see what's running on the server.

![nice cable ties](/img/nicfan.jpg?h=500&w=400)

dual port 10 gigabit network card i got for only £25

> be me
> buy low tdp cpu to save money on electricity bills
> also be me
> install network card that draws 15w
> has to cable tie a fan to it so it doesnt turn into lava

![the two switches](/img/switches.jpg?h=400&w=300) ![new switch](/img/new_switch_opened.jpg?h=400&w=300)

a better pic of the two switches - plus my new POE one I will be switching too soon!

![back of the kvm switch - io porn](/img/ioporn.jpg?h=300&w=1000)

the back of the startech kvm switch - some serious i/o porn! plus my old shitty dumb switch on top

![gamer router](/img/router.jpg?h=400&w=300)

current *gamer* router my roomie bought. it has loads of cool features, but doesnt have network boot :(. it runs an openvpn server for when my wireguard server is broken.

![next router](/img/1urouter.jpg?h=500&w=400)

the 1u machine in rack space 6 that will be my pfsense router next year. currently it just runs fedora for some backup stuff. despite having two small fans it is surprisingly quiet. 

# the next generation

here's what im working on now- a brand new (real rack) with a new xeon server!

![rack pic 1](/img/rack1.jpg?h=400&w=300) ![rack pic 2](/img/rack2.jpg?h=400&w=300)
