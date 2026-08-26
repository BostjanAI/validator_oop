# HTTPS z internim certifikatom (AD CS)

Navodila za vklop HTTPS na intranet strežniku z uporabo internega
Microsoft **Active Directory Certificate Services** (AD CS) certifikata.
Aplikacija ostane v celoti on-prem — brez javnih CA in brez interneta.

## 1. Izdaja certifikata (AD CS)

Na strežniku, kjer teče Docker (ali na poljubnem domenskem računalniku):

1. Ustvari zahtevek (CSR) s privatnim ključem. Primer z OpenSSL:

   ```bash
   openssl req -new -newkey rsa:2048 -nodes \
     -keyout validator.key \
     -out validator.csr \
     -subj "/CN=validator.podjetje.local/O=Podjetje" \
     -addext "subjectAltName=DNS:validator.podjetje.local"
   ```

   > `CN` in `subjectAltName` morata ustrezati DNS imenu strežnika,
   > pod katerim bodo uporabniki dostopali do aplikacije.

2. Zahtevek podpiši pri internem AD CS:
   - **Spletni vpis (Web Enrollment):** `https://<ca-streznik>/certsrv` →
     *Request a certificate* → *Advanced certificate request* → prilepi
     vsebino `validator.csr`, izberi predlogo **Web Server**, prenesi
     certifikat v Base-64 obliki (`validator.crt`).
   - **Ali prek ukazne vrstice** (na domenskem računalniku):

     ```bat
     certreq -submit -attrib "CertificateTemplate:WebServer" validator.csr validator.crt
     ```

3. Izvozi še verigo internega CA (root + morebitni vmesni CA) v
   `ca-chain.crt` (Base-64). Root CA je na domenskih računalnikih običajno
   že nameščen prek GPO, zato brskalniki certifikatu samodejno zaupajo.

## 2. Namestitev v nginx

1. Ustvari mapo `web/deploy/certs/` in vanjo skopiraj:
   - `validator.crt` (strežniški certifikat),
   - `validator.key` (privatni ključ – **omeji dostop**, npr. `chmod 600`),
   - opcijsko `ca-chain.crt` (veriga CA).

2. V `web/deploy/nginx.conf` odkomentiraj blok `server { listen 443 ssl; … }`
   in nastavi pravi `server_name` (DNS ime strežnika). Za preusmeritev
   HTTP → HTTPS odkomentiraj `return 301 https://$host$request_uri;`
   v HTTP bloku.

3. V `web/deploy/docker-compose.yml` odkomentiraj:

   ```yaml
   ports:
     - "8443:443"
   volumes:
     - ./certs:/etc/nginx/certs:ro
   ```

4. V `validator` servisu nastavi `MES_WEB_SECURE_COOKIES: "1"`, da se
   sejni piškotek (`mes_session`) pošilja samo prek HTTPS.

5. Ponovni zagon:

   ```bash
   docker compose -f web/deploy/docker-compose.yml up -d --build
   ```

Dostop: `https://validator.podjetje.local:8443` (ali 443, če spremeniš
mapiranje vrat).

## 3. WebSocket prek HTTPS

Frontend samodejno uporabi `wss://`, kadar stran teče prek HTTPS.
Nginx konfiguracija že vsebuje `location /api/ws/` z `Upgrade` headerji —
za HTTPS blok je enaka sekcija že pripravljena v zakomentiranem delu.

## 4. Obnova certifikata

Interni AD CS certifikati imajo običajno veljavnost 1–2 leti:

1. Ponovi korak 1–2 (nov CSR ali obnova prek `certreq`).
2. Zamenjaj `validator.crt`/`validator.key` v `web/deploy/certs/`.
3. `docker compose -f web/deploy/docker-compose.yml restart nginx`

## 5. Preverjanje

```bash
# Preveri certifikat in verigo:
openssl s_client -connect validator.podjetje.local:8443 -showcerts </dev/null

# Preveri, da API deluje prek HTTPS:
curl -k https://validator.podjetje.local:8443/api/health
```

V brskalniku na domenskem računalniku mora biti povezava označena kot
varna (interni root CA prek GPO). Če ni, preveri, da je AD CS root
certifikat v *Trusted Root Certification Authorities*.
