it is a common issue to not be able to forward ports on home internet connections. this can be caused by ISPs locking down ports, or just not having access to the router settings (e.g. living in student accommadation)

this would make it impossible to host any websites/vps/git servers

a solution could be to use a cheap vps as a *proxy* which does have a static IP. for example you can get amazon AWS free for a year. get a new cheap credit card, and get another year for free.

however these cheap servers are often too slow or don't have enough space to host all of the services I want to.

instead we can create a tunnel from our home servers to the VPS. from what I've looked at, there seem to be two main ways to do this. 

- setup a wireguard server and reverse the connection through it, like [this](https://www.aapelivuorinen.com/blog/2020/09/17/wireguard-reverse-proxy/). this is probably the best thing to do, but i couldn't get it to work lol

- setting up a reverse ssh tunnel

## setting up a reverse ssh tunnel

this is surprisingly easy to do.

1. (optional) setup a key pair for passwordless and more secure ssh connection (very easy and convenient) then set `PasswordAuthentication no`
2. Make sure `GatewayPorts yes` is set in the ssh config file to allow forwarding ports
3. This is all you need to do on the vps!
4. Forward the ports on the server. the command is `ssh -nNTv -R [proxy_local_ip]:[proxy_port]:[server_local_ip]:[server_local_port]`. You can forward additional ports by using more `-R` arguments. for example i'd use `ssh -nNTv -R localhost:6969:192.168.1.92:6969 vps.eda.gay` to proxy [eda.gay](https://eda.gay)
5. BONUS use autossh instead of ssh (newer ssh versions do this anyway)
6. then setup your nginx server as normal. its a good idea to set it up to do a lot of caching to make it a caching proxy too to put less strain on the ssh tunnel

## benchmarks

[some people](https://serverfault.com/questions/529528/ssh-tunnel-speed-is-very-slow) have reported slow preformance using this method. 

[this](https://sites.inka.de/~W1011/devel/tcp-tcp.html) says that doing TCP over TCP is generally a bad idea since it adds a lot overhead. it's probably true but its sufficient for my needs.

### baseline test

first we run iperf on the vps as a baseline speed test:

```
eden@thonkpad2:~$ iperf3 -c vps.eda.gay
Connecting to host vps.eda.gay, port 5201
[  5] local 139.222.149.15 port 41606 connected to 45.91.93.195 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  18.4 MBytes   154 Mbits/sec    2    468 KBytes
[  5]   1.00-2.00   sec  18.1 MBytes   152 Mbits/sec    0    533 KBytes
[  5]   2.00-3.00   sec  13.7 MBytes   115 Mbits/sec    0    577 KBytes
[  5]   3.00-4.00   sec  17.2 MBytes   145 Mbits/sec    0    611 KBytes
[  5]   4.00-5.00   sec  16.9 MBytes   142 Mbits/sec    0    625 KBytes
[  5]   5.00-6.00   sec  18.5 MBytes   155 Mbits/sec    0    636 KBytes
[  5]   6.00-7.00   sec  13.8 MBytes   116 Mbits/sec    0    639 KBytes
[  5]   7.00-8.00   sec  18.0 MBytes   151 Mbits/sec    0    639 KBytes
[  5]   8.00-9.00   sec  16.9 MBytes   142 Mbits/sec    0    639 KBytes
[  5]   9.00-10.00  sec  15.4 MBytes   129 Mbits/sec    0    644 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec   167 MBytes   140 Mbits/sec    2             sender
[  5]   0.00-10.02  sec   166 MBytes   139 Mbits/sec                  receiver

iperf Done.
```

### reverse SSH tunnel benchmark

then we run iperf on the server and tunnel the connection through `ssh -nNTv -R 0.0.0.0:5201:localhost:5201 vps.eda.gay`. this gives us:

```
eden@thonkpad2:~$ iperf3 -c vps.eda.gay
Connecting to host vps.eda.gay, port 5201
[  5] local 139.222.149.15 port 41614 connected to 45.91.93.195 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  15.8 MBytes   133 Mbits/sec    0    938 KBytes
[  5]   1.00-2.00   sec  11.6 MBytes  97.1 Mbits/sec  203    730 KBytes
[  5]   2.00-3.00   sec  10.5 MBytes  87.8 Mbits/sec    0    796 KBytes
[  5]   3.00-4.00   sec  13.0 MBytes   109 Mbits/sec    1    594 KBytes
[  5]   4.00-5.00   sec  10.4 MBytes  87.3 Mbits/sec    0    594 KBytes
[  5]   5.00-6.00   sec  11.7 MBytes  98.1 Mbits/sec    0    594 KBytes
[  5]   6.00-7.00   sec  8.25 MBytes  69.2 Mbits/sec    1    852 KBytes
[  5]   7.00-8.00   sec  12.1 MBytes   102 Mbits/sec    2    631 KBytes
[  5]   8.00-9.00   sec  9.24 MBytes  77.5 Mbits/sec    0    710 KBytes
[  5]   9.00-10.00  sec  13.4 MBytes   112 Mbits/sec    0    721 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec   116 MBytes  97.3 Mbits/sec  207             sender
[  5]   0.00-10.18  sec   109 MBytes  90.1 Mbits/sec                  receiver

iperf Done.
```

obviously it's a fair bit slower, but im pretty sure **the bottleneck is my internal network**. nonetheless i'm very happy with the preformance, its plenty for my needs (and like 3x faster than my parents' internet LUL)

## my implementation

[git project](https://git.eda.gay/ReverseSSHTunnel/files.html) [github mirror](https://github.com/jwansek/ReverseSSHTunnel)

i don't like having daemon services running in the background or in a tmux or something, so I made a little docker container to run the ssh command in. i also made a nice little configuration file which looks something like:

```
[server]
host = eden@vps.eda.gay
ssh_port = 2222
keyfile = vps.pem

[forward-eda.gay]
from = 192.168.1.92:6969
to = 0.0.0.0:6969

[forward-invidious]
from = localhost:3000
to = 0.0.0.0:3000
```

You don't even have to run it in a docker container if you don't like docker if you dont like docker, but if you choose to make sure you pass through the ssh keyfile as a volume in `docker-compose.yml`

### Deployment

1. `git clone https://github.com/jwansek/ReverseSSHTunnel/blob/master/docker-compose.yml && cd ReverseSSHTunnel`
2. edit `tunnel.conf` to your liking
3. passthrough your ssh key in `docker-compose.yml`
4. `sudo docker-compose build`
5. `sudo docker-compose up -d`
6. i'd recommend changing `0.0.0.0:[port]` to `localhost:[port]` on the vps once you've set up the nginx (or apache whatever) reverse proxy so people can't access your shit without caching (or make firewall rules if you prefer)
