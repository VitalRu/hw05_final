# hw05_final

![Static Badge](https://img.shields.io/badge/python-3.9.10-blue?style=for-the-badge&logo=python&labelColor=yellow) ![Static Badge](https://img.shields.io/badge/django-%25?style=for-the-badge&logo=django) ![Static Badge](https://img.shields.io/badge/pillow-blue?style=for-the-badge) ![Static Badge](https://img.shields.io/badge/sqlite3-pink?style=for-the-badge&color=337CCF)







Социальная сеть блоггеров, где пользователи могут публиковать свои посты, 
прикреплять к ним одно изображение. Пост можно разместить в группе, которую
создал админ. Авторизованные пользователи могут комментировать свои посты и 
посты других авторов, также есть возможность подписываться на автора.

#### Развертывание проекта на локальном сервере

* Установить и активировать виртуальное окружение (для Windows)
  ```
  python -m venv venv
  source venv/Scripts/activate
  ```

* Установить и активировать виртуальное окружение (для Linux)
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```

* Находясь в виртуальном окружении обновить `pip` и установить зависимости
  ```
  python -m pip install upgrade pip
  pip install -r requirements.txt
  ```

* Из каталога, где находится файл `manage.py` 
  - Выполнить миграции
      ```
      python manage.py migrate
      python manage.py makemigrations
      ```
  - запустить проект на локальном сервере
      ```
      python manage.py runserver
      ```