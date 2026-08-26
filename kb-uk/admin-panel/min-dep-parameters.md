# Функціонал налаштування min. dep та recommended sum
URL: https://help.aff.ltd/uk/admin-panel/min-dep-parameters
Category: ⚙️ Адмін-панель
Section: Промо
Summary: Особливості функціоналу min. dep та recommended sum для брендів SMEN.
Updated: 4 місяці тому

## 1. Загальна інформація

Функціонал дозволяє для певних оферів і партнерів додавати параметри Min deposit та/або Recommended sum із заданими значеннями.

Значення для Min deposit та/або Recommended sum налаштовуються в адмін-панелі.

Наразі функціонал підтримується лише на брендах групи SMEN.

Розташування: TDS → Налаштування min.dep та recommended sum (https://aff.ltd/admin/tds_traffic_scheme/mindep_settings)

## 2. Min deposit / Recommended sum

- Min deposit – дозволяє додати параметр мінімального депозиту з окремими значеннями для різних валют. Гравець не зможе внести суму, меншу за задану. GET-параметр &mcmd= обмежує гравцеві суму депозиту в касі бренду.
- Recommended sum – дозволяє додати рекомендовану суму депозиту з окремими значеннями для різних валют. GET-параметр &mcrsum= встановлює гравцеві рекомендовану суму депозиту в касі бренду.

## 3. Форма додавання правила

У формі додавання правила задається значення для Min deposit та/або Recommended sum. Потрібно заповнити хоча б одне з полів.

[image: https://d295evyo48.ucarecd.net/d4567bc3-397f-4fd3-927b-d7e0d2ff9b63/image.png]

Для параметрів відображається таблиця з колонками: Валюта, Значення.
Можна вводити суми в будь-якій доступній валюті.

Допускаються дробові значення (копійки), наприклад: mcmd=20.5BRL

3.1. GET-параметр для Min deposit (&mсmd=)

Раніше використовуваний параметр дефолтної валюти бренду (&md=) замінено на мультивалютний формат (&mcmd=).

○ Значення складається із суми та тикера валюти. Наприклад, &mcmd=100BRL
○ Підтримує кілька валют, розділених нижнім підкресленням. Наприклад, &mcmd=5USD_50BRL_100TRY

TDS і надалі підтримує параметр &md= при ручному прописуванні.

По GET-параметру &md= бренд приймає значення у дефолтній валюті (діапазон 2–1500), після чого відбувається конвертація у валюту користувача.

Дефолтні валюти брендів:

- 7slots.casino – USD
- Vulkan777 – UAH
- VulkanRoyale – KZT
- Інші бренди – RUB

3.2. GET-параметр для Recommended sum (&mсrsum=)

○ Значення складається із суми та тикера валюти. Наприклад, &mcrsum=100BRL

○ Підтримує значення для кількох валют. Наприклад, &mcrsum=5USD_50BRL_100TRY

3.3. Можна зберегти правило з value в mcrsum та mcmd – передаються всі значення.

Наприклад:

○ mcmd=19USD&mcrsum=77USD

○ mcmd=109BRL_58.6USD_77.5PEN&mcrsum=109BRL_58.6USD_33.5PEN

Після встановлення налаштування для партнера, під час переходу за його посиланням, в URL на TDS автоматично будуть підставлятися GET-параметри в кінці всіх параметрів.

## 4. Таблиця

В таблиці виводиться інформація про налаштовані параметри Min deposit і Recommended sum.

[image: https://d295evyo48.ucarecd.net/fc78248f-0086-4ee2-82c0-1b162f1e3a08/Group_11.png]

У колонці Min deposit відображається мультивалютність (якщо обрано кілька валют).

Логіка фільтрації:

○ За входженням – якщо введено 1 слово/символ.
○ За точним співпадінням – якщо введено 2+ слів (роздільник пробіл).
○ Можлива фільтрація за кількома запитами – через кому.

## 5. Ліміти для параметрів Min deposit та Recommended sum (SMEN)

Назва бренду | Мінімальне значення параметра min. dep | Максимальне значення параметра min. dep | Мінімальне значення параметра recommend. sum | Максимальне значенння параметра recommend. sum
GMSlots | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Maxbet | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Slotozal | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
ClubVulkan | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
RubinOnline | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
GMSDeluxe | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Admiral | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Pharaonbet | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Eldorado24 | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Vulkan24Club | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
VDeluxe | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
JoyCasino | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
RoyalCasino | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Vulkan777 | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
PlatinumCasino | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
RoyalR | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
7k.casino | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
Basari.Bet | RUB 100 / KZT 1 500 | RUB 1 500 / KZT 7 500 | RUB 500 / KZT 10 000 | RUB 3 000 / KZT 20 000
VulkanStars (VStars) | RUB 100 / KZT 500 / AMD 400 / AZN 2 / PLN 20 / RON 20 / UZS 10 000 | RUB 1 500 / KZT 8 000 / AMD 6 500 / AZN 30 / PLN 100 / RON 100 / UZS 200 000 | RUB 500 / KZT 2 500 / AMD 2 000 / AZN 10 / PLN 20 / UZS 60 000 | RUB 3 000 / KZT 15 000 / AMD 12 000 / AZN 55 / PLN 120 / RON 120 / UZS 400 000
VoxCasino | RUB 100 / KZT 500 / AMD 400 / AZN 2 / PLN 20 / RON 20 / UZS 10 000 | RUB 1 500 / KZT 8 000 / AMD 6 500 / AZN 30 / PLN 100 / RON 100 / UZS 200 000 | RUB 500 / KZT 2 500 / AMD 2 000 / AZN 10 / PLN 20 / UZS 60 000 | RUB 3 000 / KZT 15 000 / AMD 12 000 / AZN 55 / PLN 120 / RON 120 / UZS 400 000
SeaStarCasino | USD 2 / TRY 50 | USD 50 / TRY 1 500 | USD 12 / TRY 400 | USD 60 / TRY 2000
Awintura | USD 2 / CLP 1 800 / BRL 9 / MXN 33 / PEN 7 | USD 50 / CLP 50 000 / BRL 250 / MXN 850 / PEN 200 | USD 10 / CLP 9 000 / BRL 50 / MXN 170 / PEN 40 | USD 1 000 / CLP 900 000 / BRL 5 000 / MXN 16 000 / PEN 3 700
7slots.casino | USD 2 / TRY 60 / EUR 2 / CLP 1 819 / BRL 10 / VND 49 014 / THB 70 / MYR 9 / PHP 112 / INR 166 / BTC 0.00004666 | USD 50 / TRY 1 500 / EUR 46 / CLP 45 482 / BRL 243 / VND 1 225 340 / THB 1 745 / MYR 232 / PHP 2 790 / INR 4 144 / BTC 0.00116651 | USD 10 / TRY 300 / EUR 9 / CLP 9 000 / BRL 45 / VND 245 068 / THB 349 / MYR 46 / PHP 558 / INR 829 / BTC 0.00116651 | USD 1 000 / TRY 30 000 / EUR 912 / CLP 910 000 / BRL 4 855 / VND 24 506 810 / THB 34 899 / MYR 4 647 / PHP 55 806 / INR 82 879 / BTC 0.02333012
Winnita | USD 2 / TRY 60 / EUR 2 / CLP 1 819 / BRL 10 / VND 49 014 / THB 70 / MYR 9 / PHP 112 / INR 166 / BTC 0.00004666 | USD 50 / TRY 1 500 / EUR 46 / CLP 45 482 / BRL 243 / VND 1 225 340 / THB 1 745 / MYR 232 / PHP 2 790 / INR 4 144 / BTC 0.00116651 | USD 10 / TRY 300 / EUR 9 / CLP 9 000 / BRL 45 / VND 245 068 / THB 349 / MYR 46 / PHP 558 / INR 829 / BTC 0.00116651 | USD 1 000 / TRY 30 000 / EUR 912 / CLP 910 000 / BRL 4 855 / VND 24 506 810 / THB 34 899 / MYR 4 647 / PHP 55 806 / INR 82 879 / BTC 0.02333012

Ліміти для платіжних методів Туреччини:
○ 7slots.casino
○ Basari.Bet
○ Abe.Bet
○ Masal.Bet

TL – для акаунтів в TRY.
USD – для акаунтів в USD.

Назва | Мінімальне значення параметра min. dep
MasterCard | 40 TL / 2 USD
Visa | 140 TL / 5 USD
Payfix | 30 TL / 2 USD
Banka Havalesi | 100 TL / 3 USD
Papara | 50 TL / 3 USD
PayCO | 50 TL / 3 USD

○ VulkanStavka – на платформі GIN, параметр поки не працює.
○ League of Slots – трафік на бренд пускати заборонено.

5.1. Нюанси щодо лімітів

- У касі можливі деякі відхилення від заявленої суми.

Наприклад: якщо min. dep для бренду становить 2 USD, у касі це може бути 2.3 USD.
У такому випадку налаштований min. dep (2 USD у get-параметрі) буде проігнорований – гравець побачить 2.3 USD. Це відбувається через коригування на стороні S2P.

Під час налаштування правила рекомендується додатково протестувати ліміти по функціоналу.

- Є платіжні методи, де суми вказуються на стороні клієнта, а не каси.
У таких випадках фактична сума може бути меншою за min. dep у get-параметрі. Точний список таких методів відсутній.
