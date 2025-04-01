# shortlinks

* Реализованы методы:
  * `GET /links/search` — поиск коротких ссылок по оригинальному URL.
  * `GET /links/{short_code}` — редирект по короткой ссылке на оригинальный URL.
  * `POST /links/shorten` — создание новой короткой ссылки.
  * `DELETE /links/{short_code}` — удаление короткой ссылки.
  * `PUT /links/{short_code}` — обновление данных короткой ссылки.
  * `GET /links/{short_code}/stats` — получение статистики по короткой ссылке.
* В github actions собирается докер образ и пушится в docker hub https://hub.docker.com/r/tfonferm/calorites-tg-bot/tags
* Секреты лежат на виртуальной машине в .env файле. SSH к ней лежит в секретах репозитория.
* Деплой на виртуальный хост в yandex cloud происходит через github actions автоматически.