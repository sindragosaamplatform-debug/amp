# Використання плагінів Redirect Path та EditThisCookies
URL: https://help.aff.ltd/uk/additional-resources/useful-plugins
Category: Додаткові матеріали
Section: Додаткові матеріали
Summary: Огляд та флоу використання плагінів Redirect Path та EditThisCookies.
Updated: 1 рік тому

Плагіни Redirect Path та EditThisCookie – інструменти для перевірки коректності передачі параметрів партнерських посилань, таких як refcode або Click ID.

Redirect Path дозволяє відстежувати кожен крок редиректу, що допомагає виявити, чи зберігаються потрібні параметри на всіх етапах, або визначити, де саме може відбуватися втрата даних.

EditThisCookies надає можливість перевірити, чи зберігаються refcode, Click ID, affdata та інші параметри у файлах cookie під час тестування промо-матеріалів.

## Redirect Path: Аналіз редиректів

Redirect Path – плагін для відстеження всіх редиректів, які відбуваються під час завантаження сторінки.

Інструмент корисний для:

- Аналізу ланцюжків редиректів;
- Виявлення зайвих чи некоректних редиректів.

Як використовувати:

1. Встановлення плагіна. Завантажте Redirect Path з магазину розширень браузера або запосиланням (https://chromewebstore.google.com/detail/redirect-path/aomidfkchockcldhbkggjokdkkebmdll) (для Google Chrome).
2. Аналіз шляху редіректів. Після встановлення плагін буде відображати кожен етап редіректу при переході на сторінку.
3. Перевірка кодів редіректів. Redirect Path також показує HTTP-коди відповідей (наприклад, 302, 200), що допомагає виявити помилки та оптимізувати процес перенаправлення.

Приклад:

- Переходимо за партнерським посиланням: http://mysweet-profit.com/?s=35&ref=test&encoded_url=cmVnaXN0ZXI=
- Клікаємо на іконку плагіна Redirect Path у браузері та бачимо всі редиректи:

[image: https://ucarecdn.com/d99a2cfd-8b60-4071-a41b-cfe2b37c6691/image.png]

- При кліку на будь-який з редиректів можна переглянути його деталі, а також HTTP-коди відповідей:

[image: https://ucarecdn.com/a1415b26-aac1-49c5-838c-40148005dcce/image.png]

## EditThisCookies: Аналіз файлів cookie

EditThisCookies – це плагін для аналізу кукі-файлів, що дозволяє переглядати, змінювати, видаляти або додавати нові кукі. Він зручний для перевірки GET-параметрів, тестування сеансів або налаштування для конкретних користувачів.

Як використовувати:

1. Встановлення плагіна. Завантажте EditThisCookies з магазину розширень вашого браузера або за посиланням (https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg) (для Google Chrome).
2. Перегляд та редагування кукі. Після встановлення плагін дозволить відразу переглядати всі кукі на сторінці. Це особливо корисно для перевірки промо.

Приклад:

- Розглянемо партнерське посилання: https://vulkanvegas-promo.com/l/66e4092d3194458e6a070a52?sub_id=test&click_id=clickhttps://vulkan777.world/uk/register/?sub_id=cash%3Fclick_ID%3D%7BCLICK_ID%7D
- Переходимо за посиланням і відкриваємо EditThisCookies для перегляду кукі:

[image: https://ucarecdn.com/50973788-19b7-46ee-92d3-8c1c3fecfb85/image.png]

- Щоб переглянути, до прикладу, aff_data_cookie, натискаємо на відповідний кукі-файл і бачимо дані Name та Value.

[image: https://ucarecdn.com/6b7f0db8-23b6-41b7-9925-9dc4a1e9a0af/image.png]

- Наразі ця інформація нам мало про що говорить, але, використавши ресурс URL Decoder/Encoder (https://meyerweb.com/eric/tools/dencoder/), скопіювавши Value та вставивши його в URL Decoder, можна декодувати це значення:

[image: https://ucarecdn.com/9ce5cd25-a7ea-4645-9351-2feed1c4fa21/screencast 2024-11-04 13-13-57.gif]

Декодоване значення, яке ми отримали:

subdata=fc1489b8d45a152b397bc8a56eb42104&click_id=click&rotator=241935&landing=4425&sub_id=test

Бачимо ID лендінгу, значення sub_id, click_id і т. д., що дозволяє розпочати аналіз цих даних.

Інформацію про структуру та значення GET-параметрів партнерського посилання можна дізнатись у гайді за посиланням (https://help.aff.ltd/uk/aff-area/structure-of-affiliate-links-ng).
