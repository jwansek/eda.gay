## CPUs i still own

### Intel Mobile Pentium 4-M 1.8 GHz

*2002, 30W, 1c1t*

**Status: In use (print server)**

the first real computer i used a lot, lived inside a thinkpad t30, back when they still were made by ibm instead of lenovo. it is still used to this day, it runs debian stable with the lxde desktop environment and its used as a print server since the only computer i have with a parallel port. its also nice to have for nostagia purposes

![thinkpad t30](/img/t30.jpg?h=400&w=200)

### Intel Xeon E5-4620 v3

*2015, 105W, 10c20t*

**Status: Testing**

this meaty cpu will be at the heart of the next generation of edencloud. as yet i dont know if i'll use this for a workstation or as a vm hypervisor since its significant tdp will make it difficult to run 24/7

![xeon cpu](/img/xeon.jpg?h=400&w=200) ![rack 2.0 - under constuction!](/img/rack1.jpg?h=400&w=200) ![xeon motherboard](/img/xeon_motherboard.jpg?h=400&w=200)

*new rack under construction! - look at all those PCIe lanes!*

### Intel i7-6500u

*2015, 15w, 2c4t*

**Status: In active use**

the heart of the main computer i use on a day-to-day basis, a thinkpad x260. i also have a thinkpad x260 with an [i5-6300u](do the link). this cpu is fine for most people, and the whole laptop only cost me £110. it is dual booted with windows and debian unstable.

### Intel Core 2 Duo P8400

*2008, 25w, 2c2t*

**Status: In active use**

you may think this cpu is old and awful, but cpu development has stalled so much that its perfectly fine to use day-to-day. i use it for web browsing, programming and writing latex documents with its excellent keyboard. in fact im typing this blog post on it now! its age has an advantage- core 2 duo era cpus can have the intel management engine totally removed from them. making this one of the few laptops that can be 100% FOSS. mine uses a custom bios called libreboot

![x200](/img/x200.jpg?h=400&w=200) ![libreboot](/img/libreboot.jpg?h=400&w=200)

*flashing the bios with a raspberry pi*

### Intel Celeron J1800

*2013, 10w, 2c2t*

**Status: In a cupboard**

i got this bundled with a server case i bought off ebay. its basically worthless for reasons i will explain. its attached to an embedded itx motherboard. its too slow to run a decent desktop environment on (it's somehow slower than my [P8400?](#Intel+Core+2+Duo+P8400)) it would make an excellent pfsenserouter, due to its very low tdp, but it doesnt have hardware AES or enough pci lanes to run a dual port nic. my [A4-5000](do the link idiot) is actually older but has twice the cores, hardware AES, and more pci lanes. apparently AMD seemed to be better at including hardware features in their low-end processors back then

![j1800](/img/j1800.jpg?h=400&w=200)

### AMD A4-5000

*2013, 15w, 4c4t*

**Status: Testing**

imo this is the best cpu for a home pfsense router. it has everything you need- a low tdp for cheap running costs, hardware AES for vps, and a 4x PCIe lane for network cards. also you can find old oem mATX motherboard containing one [on ebay](https://www.ebay.co.uk/itm/154502676419) for as little as £15. mine is in an embedded itx case with 8Gb of memory (which is crazy overkill for a router!)

![low res image lol](/img/a4-5000.jpg)

### Intel Core i5-8500T

*2018, 35w, 6c6t*

**Status: In active use**

this is the cpu inside my dell optiplex 3060 sff pc. its only really used to play games (and i dont really play any games any more) so i'm probably going to sell this thing soon.

### Intel Core i5-9400T

*2019, 35w, 6c6t*

**Status: In active use (main server)**

this is the main cpu that my servers run off. its currently the host for this website too. it lives inside my main NAS, which runs truenas, and an ubuntu virtual machine. its got a 35w tdp so its fairly cheap to run, and has a passive cpu cooler for quietness. i got it for only 90£, used cpus are crazy cheap nowadays. this is likely to be the brains of my file server for a long time yet.

![cables lol](/img/9400t_cooler.jpg?h=200&w=400) ![9400t CPU](/img/9400t.jpg?h=400&w=200)

*i took this picture \*before\* doing the cable management ;3*

## CPUs i *used* to own

### AMD A9-9420

*2017, 15w, 2c2t*

**Status: Sold to a friend**

i still have a soft spot for this cpu, which lived inside the first decent laptop i had. i did my a-levels on this thing. it was also my first server. i used to run openmediavault on it and host docker containers on it. later it became a web server. 

building a server from a laptop has some unique advantages: a low tdp so its cheap to run and a built-in UPS. however for some reason this laptop was crazy loud. eventually it was relegated to live downstairs.

![first server](/img/first_server.jpg?h=200&w=400) ![downstairs](/img/router.jpg?h=400&w=200)

the picture on the left is my first ever file server with a raspberry pi on top

### Intel Core i5-6300u

*2015, 15w, 2c4t*

**Status: Broken**

the CPU in my first thinkpad x260. sadly its broken

### Intel Pentium Silver J5040

*2019, 10w, 4c4t*

**Status: Sold**

imo this is the most interesting CPU i've owned it blows me away how good low-end CPUs are nowadays. this is a quad core cpu with passive cooling in an embedded itx motherboard. it was used for my first *proper* server running ZFS. imo this is the best cpu to use as a simple file server. it has 4 sata slots and you can add more with a pcie hba like i did, and even more using the m.2 slot using something like [this](https://www.ebay.co.uk/itm/154502395872). its only real disadvantage is the lack of higher speed networking (i guess you could put a 2.5gigabit nic in) or enough horsepower to run VMs.

![in the server case](/img/j5040_server.jpg?h=400&w=200) ![motherboard](/img/j5040.jpg?h=200&w=400)
