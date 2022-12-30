# general computing
- my main computer that i do most of my work on is a thinkpad x260. it has a [6500U cpu](https://eda.gay/thought?id=13#Intel+i7-6500u) and 8Gb of ram. it runs debian unstable, manjaro and windows for when i need to use shitty proprietary software
- i also use a [thinkpad x200](https://eda.gay/thought?id=13#Intel+Core+2+Duo+P8400). it has an amazing keyboard so its great for writing latex documents. it's librebooted and has no proprietary software at all on it. it runs debian unstable too :3

![x200 with hand for scale](https://eda.gay/img/x200.jpg?h=400&w=200) ![libreboot](/img/libreboot.jpg?h=400&w=200)

me flashing the bios to libreboot with a raspberry pi

# servers
read about my previous server setups [here](https://eda.gay/thought?id=14)

![lackrack 3](https://eda.gay/img/IMG_20220811_133224877_HDR.jpg?h=300&w=4000) ![lackrack 1](https://eda.gay/img/startech_rack_1.jpg?h=1000&w=400)

here it is! i finally got my own real server rack. from top to bottom, it has:

0. a startech 4 port dual monitor kvm switch (SV431DD2DUA), for main workstations with dvi connections
1. an aten 4 port vga/ps2 kvm switch for servers and stuff i don't need to access often
2. a rack shelf with a Mikrotik CSS610-8G-2S+in 10gig switch and the [dell optiplex 3060](https://eda.gay/thought?id=13#Intel+Core+i5-8500T). behind the switch there is a raspberry pi 3b
3. a cable brush management thingy
4. a Netgear GS516TP switch with 8 POE ports. the POE powers the mikrotik switch and three raspberry pis. interestingly it can be powered of POE itself, which is pretty crazy, although i struggle to find a reason why you'd want to do that. behind it on another shelf is an external hard drive for backups and two more raspberry pi 3bs
5. an old HP IP KVM switch, not currently in use. i wrote about it in [this](https://eda.gay/thought?id=18) blog post. the older pic on the right has my pfsense router, with an [AMD A4-5000](https://eda.gay/thought?id=13#AMD+A4-5000) 15W quad core CPU with hardware AES. It has 8Gb of memory and a powerful intel i350 dual port nic. it has since been moved downstairs
6. below is my main server/nas. it has an [i5-9400t](https://eda.gay/thought?id=13#Intel+Core+i5-9400T) 6 core cpu. i went with the t version since it has a lower tdp and therefore it is cheaper to run. it runs truenas (formerly called freenas). it also runs all of my docker containers on a ubuntu server VM. it has 32gb of memory for a nice big zfs cache and is potentially upgradeable to 64gb. it has a passive cooler for quietness. click [here](https://eda.gay/services) to see what's running on the server.
7. the 4u server below has a [xeon e5-4620v3](https://eda.gay/thought?id=13#Intel+Xeon+E5-4620+v3) cpu, a quadro k4200, and 64gb of ecc memory. i like it because it has lots and lots of PCIe lanes. its quite powerful!

![switch on the switch](https://eda.gay/img/IMG_20220809_172130442_HDR.jpg?h=1000&w=400) ![router](https://eda.gay/img/IMG_20220823_154457137_HDR.jpg?h=1000&w=400)

downstairs i have the aformentioned pfsense router, a nintendo switch, on top of a netgear GS108PEv3 POE switch. it powers a raspberry pi (running the tp-link omada controller), and [a tp-link access point.](https://eda.gay/img/IMG_20220812_112838125_HDR.jpg)

# software stack

my software stack consists of the following

```
├── AMD A4-5000 @ pfsense 2.6
│   ├── DDNS
│   ├── DHCP (with netboot redirect)
│   └── Wireguard server
│
├── Intel i5-9400T @ truenas core 12
│   ├── freebsd jails
│   │   ├── jellyfin (to allow hardware re-encoding)
│   │   ├── mariadb (currently testing)
│   │   ├── nextcloud
│   │   └── open speed test
│   │
│   ├── byhve hypervisor
│   │   ├── ubuntu server 22.04.1
│   │   │   ├── docker
│   │   │   │   ├── invidious
│   │   │   │   ├── gitolite-cgit
│   │   │   │   ├── netboot TFTP
│   │   │   │   ├── klaus (git viewer)
│   │   │   │   ├── transmission-openvpn
│   │   │   │   ├── SubredditModLog
│   │   │   │   ├── SmallYTChannelBot
│   │   │   │   ├── RSSPoster
│   │   │   │   ├── yaoi-communism
│   │   │   │   ├── reverse ssh tunnel
│   │   │   │   ├── nitter
│   │   │   │   ├── mariadb
│   │   │   │   ├── phpmyadmin
│   │   │   │   ├── bibliogram
│   │   │   │   └── a bunch of stuff. see https://eda.gay/services...
│   │   │   │
│   │   │   └── nginx
│   │   │
│   │   └── ubuntu server 20.04.5
│   │       └── tp-link omada wifi controller
│   │
│   ├── zfs pools
│   │   ├── SpinningRust pool (hard drive array)
│   │   │   ├── databaseBackups
│   │   │   ├── encrypted data
│   │   │   ├── ISOs
│   │   │   ├── spinningRust
│   │   │   └── TFTP
│   │   │       ├── images
│   │   │       └── config
│   │   │
│   │   ├── theNVMEVault (NVME ssd array)
│   │   │   ├── docker volumes
│   │   │   ├── iSCSI disks
│   │   │   ├── steamLibrary
│   │   │   ├── theVault
│   │   │   ├── VM images
│   │   │   ├── iocage (jails stuff)
│   │   │   └── git assets
│   │   │       └── git config
│   │   │
│   │   └── backup0
│   │       ├── databaseBackups
│   │       ├── spinningBackup
│   │       │   ├── encrypted data
│   │       │   ├── spinningRust
│   │       │   └── TFTP config
│   │       │
│   │       └── theVaultBackup
│   │           ├── docker volumes
│   │           ├── VM images
│   │           ├── theVault
│   │           ├── iSCSI disks
│   │           ├── iocage
│   │           └── git assets
│   │               └── git config
│   │
│   ├── NFS
│   ├── SMB
│   └── iSCSI
│
├── raspberry pi 3b @ raspbian
│   ├── git server
│   └── externally accessable SSH
│
├── raspberry pi 3b @ home assistant OS
│   └── home assistant
│
└── raspberry pi 3b @ ubuntu server 22.10
    └── database backups

```

# nics

![nice cable ties](/img/nicfan.jpg?h=1000&w=250) ![wow dusty](/img/media_FfcNNZ2WYAAz97v.jpg?h=1000&w=250)

dual port 10 gigabit network card i got for only £25. the picture on the left has since been upgraded to a proper HBA card (see right)

> be me
> buy low tdp cpu to save money on electricity bills
> also be me
> install network card that draws 15w
> has to cable tie a fan to it so it doesnt turn into lava

my main workstation has an intel X520 10 gigabit nic.

# switches

![the two switches](/img/switches.jpg?h=300&w=3000) ![new switch](/img/new_switch_opened.jpg?h=300&w=3000)

the four switches i use in my house. above, the netgear gs108pe and mikrotik CSS610-8G-2S+in. to the right, the netgear GS516TP. below is the tp-link TL-RP108GE. this switch is notable since it can be powered off POE, and has a POE output port, which powers my other access point (on the right). all of my switches are managed, which is required for setting up VLANs. as you can see, my other AP is installed in a *HIGHLY PROFESSIONAL* manner.

![reverse POE switch](/img/IMG_20221023_163821542.jpg?h=300&w=3000) ![professional-tier AP install](/img/media_FeP_m8FXEAAqcJs.jpg?h=300&w=3000)

# kvm switches

![back of the kvm switch - io porn](/img/ioporn.jpg?h=300&w=1000)

the back of the startech kvm switch - some serious i/o porn! plus my old shitty dumb switch on top

![ip kvm switch](/img/s-l1600.jpg)

i also have an HP IP kvm switch, currently unused, see the blog post [Everything you need to know about old HP IP KVM Switches (EO1010 series)](https://eda.gay/thought?id=18).
