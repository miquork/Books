# Books

GitHub Pages for self-published books, researched, produced and directed by
Mikko Voutilainen. AI writing and illustration are credited individually.

Intended site: **https://miquork.github.io/Books/**
(Available after the first successful Pages deployment.)

## Ensimmäinen julkaisu

1. Avaa **Settings → Pages** ja valitse **Source: GitHub Actions**.
2. Avaa **Releases → Draft a new release**.
   - Luo uusi tagi **`mirror-2026-09-05-v3`**, target **main**.
   - Otsikko: **The Mirror That Opened the Sky — 5 September 2026**.
   - Lisää tiedostoliitteinä molemmat paikallisen `release/`-kansion tiedostot:
     `the-mirror-that-opened-the-sky-2026-09-05-workshop.pdf` ja
     `mirror-web-images.zip`.
   - Valitse **Publish release**. Älä lisää tiedostoja repon Code-näkymään.
3. Avaa **Actions → Publish bookshelf → Run workflow → main → Run workflow**.
   Sivusto julkaistaan vasta, kun sekä PDF että kuvat vastaavat hyväksyttyä
   versiota. Ennen liitteiden lataamista ensimmäinen automaattinen ajo voi
   epäonnistua latausvaiheessa; tämä ei julkaise rikkinäistä sivua.
4. Kun ajo on vihreä, avaa **Settings → Pages → Visit site**.

Sivuston koodi ja tekstit ovat tässä repossa. PDF ja JPEG-kuvat ovat
Releases-liitteissä, **eivät Git-historiassa**. Sivuston julkaisu sisältää vain
HTML:n, CSS:n ja kolme web-kuvaa. PDF ladataan suoraan Releasesista.
Tutkimusrepo, raakakuvat ja yksityiset aineistot eivät siirry tänne.

## Tekstin ja ulkoasun muokkaaminen

- `content/index.md`: yhteisen kirjahyllyn johdanto.
- `content/the-mirror-that-opened-the-sky.md`: kirjan esittely Markdownina.
- `content/the-mirror-that-opened-the-sky-credits.md`: kirjan tekijäkrediitit.
- `site.json`: kirjat, otsikot, julkaisuversion tiedot ja latausten tarkistussummat.
- `assets/style.css`: ulkoasu; `templates/page.html`: yhteinen sivupohja.
- `scripts/build.py`: sivujen rakentaminen. Uusi kirja saa oman sivunsa
  lisäämällä tietueen `site.json`-listaan sekä samannimisen Markdown-tiedoston
  ja `-credits.md`-tiedoston. Tietueeseen kuuluvat kirjan omat kuvat, kuvatekstit
  ja lataukset. Nykyinen kuvapohja olettaa 7:10-kannen ja 14:10-aukeamat;
  muiden kuvasuhteiden leveys/korkeus pitää päivittää rakentajaan.

Pushaaminen main-haaraan päivittää sivuston automaattisesti. Kun PDF vaihtuu,
tee uusi release-tagi ja päivitä sen tiedot ja tarkistussummat `site.json`:iin.
Älä korvaa vanhaa PDF:ää hiljaisesti. Sivusto ei seuraa vaihtuvaa `latest`-linkkiä.
Kuvatarkisteen muutos on tietoinen uuden julkaisun hyväksyntä.

## Paikallinen tarkistus

Python 3.12:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py --output build/preview/Books --local-release release
.venv/bin/python scripts/check.py build/preview/Books
python3 -m http.server 8765 --bind 127.0.0.1 --directory build/preview
```

Avaa `http://127.0.0.1:8765/Books/`. Tuloskansion täytyy olla uusi:
rakentaja ei poista vanhoja tiedostoja rekursiivisesti. Voit valita uuden
preview-kansion seuraavalle ajolle. Ilman `--local-release`-valintaa rakentaja
lataa tarkistetut tiedostot GitHub Releasesista.

`scripts/prepare_release.py --book-root /path/to/book` valmistaa web-JPEG:t
hyväksytyistä sivukuvista ja kopioi tarkistetun PDF:n `release/`-kansioon.
Tämä valinnainen paikallinen työkalu tarvitsee Pillow-kirjaston. Se ei julkaise
mitään. Se tulostaa media-arkiston SHA-256:n, joka kirjataan `site.json`:iin.

## Rajaukset

Ei analytiikkaa, seurantaskriptejä, lomakkeita, ulkoisia fontteja eikä
kirjautumista. Ladattavuus ei itsessään anna kuville tai tekstille erillistä
uudelleenkäyttölisenssiä. Julkaisun lisenssistä päättää projektin tuottaja.

GitHubin ohjeet: [Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
ja [Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
