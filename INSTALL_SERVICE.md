# Installing an Acquire service

Here are instructions for setting up a server that can host
the Acquire services

## Step 1 - Set up a server

First, set up a server somewhere on the internet. For example,
on Oracle a VM.Standard2.1 would be fine. As a start, you need
the firewall to allow ingress to ports 22, 80, 443 and 8080.
Once SSL is working, we will close 8080...

## Step 2 - Install Fn pre-requisites

Fn requires Docker 17.10.0-ce or later. Install this, e.g. on Oracle Linux 7
using

```
# cd /etc/yum.repos.d/
# sudo wget http://yum.oracle.com/public-yum-ol7.repo
# sudo vi public-yum-ol7.repo

[ol7_latest]
name=Oracle Linux $releasever Latest ($basearch)
baseurl=http://yum.oracle.com/repo/OracleLinux/OL7/latest/$basearch/
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oracle
gpgcheck=1
enabled=1

[ol7_UEKR4]
name=Latest Unbreakable Enterprise Kernel Release 4 for Oracle Linux $releasever ($basearch)
baseurl=http://yum.oracle.com/repo/OracleLinux/OL7/UEKR4/$basearch/
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oracle
gpgcheck=1
enabled=1

[ol7_addons]
name=Oracle Linux $releasever Add ons ($basearch)
baseurl=http://yum.oracle.com/repo/OracleLinux/OL7/addons/$basearch/
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oracle
gpgcheck=1
enabled=1

# sudo yum install docker-engine
```

Now start docker and ensure it runs on login

```
# sudo systemctl start docker
# sudo systemctl enable docker
```

(you may need to add your user to the 'docker' group so that you
 have permission to use docker - check using `docker ps`)

## Install Fn

Now install Fn - bit insecure as need to execute a curl!

```
# curl -LSs https://raw.githubusercontent.com/fnproject/cli/master/install | sudo sh
```

## Start Fn

```
# fn start
```

Check this has worked by navigating to `http://{IP_ADDRESS}:8080`

## Set up DNS and SSL

Optional - if you want to secure access to your service then you need
to create a DNS record for your service. First, create a DNS ANAME record
for the IP address of your server.

Next, install nginx as we will use this as the loadbalancer to handle
SSL.

```
# sudo yum install nginx
# sudo yum install certbot python2-certbot-nginx
# sudo systemctl enable nginx
# sudo systemctl start nginx
```

Now make sure that the local firewall allow http and https traffic

```
# sudo systemctl enable firewalld
# sudo firewall-cmd --zone=public --add-port=80/tcp
# sudo firewall-cmd --zone=public --add-port=443/tcp
# sudo firewall-cmd --zone=public --add-port=80/tcp --permanent
# sudo firewall-cmd --zone=public --add-port=443/tcp --permanent
```

Navigate to `http://{IP_ADDRESS_OF_SERVER}` to see if you can see the
nginx launch page

Now get the SSL certificate

```
# sudo certbot --nginx -d {HOSTNAME}
```

Finally, you need to set up redirect to the Fn service. Do this by
editing your `/etc/nginx/nginx.conf` and making it equal

```
# For more information on configuration, see:
#   * Official English Documentation: http://nginx.org/en/docs/
#   * Official Russian Documentation: http://nginx.org/ru/docs/

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;

    server {
        listen       80 default_server;
        listen       [::]:80 default_server;
        server_name  _;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        location / {
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }

    server {
    server_name hugs.acquire-aaai.com; # managed by Certbot
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Credentials' 'true';
        add_header 'Access-Control-Allow-Headers' 'Authorization,Accept,Origin,DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        add_header 'Access-Control-Allow-Methods' 'GET,POST,OPTIONS,PUT,DELETE,PATCH';

        location / {
        }

        location /t {
            proxy_pass http://127.0.0.1:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }


    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/hugs.acquire-aaai.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/hugs.acquire-aaai.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}

    server {
    if ($host = hugs.acquire-aaai.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


        listen       80 ;
        listen       [::]:80 ;
    server_name hugs.acquire-aaai.com;
    return 404; # managed by Certbot


}}
```

And then, you may need to let selinux know that you need to allow
nginx to route to fn. You can check this by running;

```
# sudo cat /var/log/audit/audit.log | grep nginx | grep denied | audit2allow -M mynginx
```

and follow the instructions recorded, e.g.

```
# sudo semodule -i mynginx.pp
```

## Install Acquire

Once you have tested that Fn is accessible, then you can next install Acquire.

First, download via GitHub

```
# git clone https://github.com/chryswoods/acquire
```

Make sure that you have created Oracle user accounts for each
service you want to install, with the ability to create object storage
buckets in your desired compartment. Also create a single bucket
for the service, e.g.

* user = acquire_identity
* compartment = acquire_services
* bucket = identity_bucket

For each service, you will need to change into the service directory,
e.g. `cd services/{SERVICE}`, so `cd services/identity` for the
identity service.

Now change into the `credentials` directory and run the command

```
# python3 generate_keys.py {name} {passphrase}
```

where `{name}` is the name of the key (e.g. `acquire_identity`) and
`{passphrase}` is the passphrase you will use to protect this key.
Make a note of the passphrase as you will need it later.

This will create a public and private key used to log into the service.

Log onto the OCI console and upload the public key to the user account
on OCI that you have specified for this service. Make a record
of the fingerprint that OCI will report.

Next, create a Fn app for the service, e.g.

```
# fn create app identity
```

Next, edit the `upload_credentials.py` file to include the OCIDs of the
OCI user, compartment, bucket and key fingerprint that will be used to
store data for this service.

Finally, copy into the file `../secret_key` a secret password/key
that will be used to encrypt everything.

Once you have copied in all of the details, run the script using

```
# PYTHONPATH=../../../ python3 upload_credentials.py {NAME}.pem {PASS1} {PASS2}
```

where `{NAME}` is the name of the key you generated above using
`generate_keys.py`, where `{PASS1}` is the passphrase you used to
encrypt that key, and where `{PASS2}` is the key as written into
`../secret_key`.

You should see a lot printed to the screen, showing that an encrypted config
has been added for the service.

Next, you need to deploy the service. Do this by typing

```
# cd ..
# cd ../base_image
# ./build_and_push.sh
# cd -
# fn deploy . --local
```

Check that the service is working by navigating to
`http://{SERVER_IP}:8080/t/{SERVICE_NAME}`

(or, by calling `fn invoke {SERVICE} {SERVICE}-root`)
