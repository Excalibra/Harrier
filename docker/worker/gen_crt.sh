cd /etc/ssl/certs/

if [ ! -f harrier_web.csr ]; then
  openssl req -new -newkey rsa:2048 -sha256 -nodes -out harrier_web.csr -keyout \
harrier_web.key -subj "/C=CN/ST=Shanghai/L=Shanghai/O=Example Inc./OU=Web Security/CN=127.0.0.1"
fi

if [ ! -f harrier_web.crt ]; then
  openssl x509 -req -days 3650 -in harrier_web.csr -signkey harrier_web.key -out harrier_web.crt
fi
