# VendingMachine
Программное обеспечение Вендинг аппарата
Среда разработки и развертывания Raspberry PI 3 Model B

#### параметры датчика потока воды 1000мл=5880пульов или 0,17мл=1пульс

````bash
sudo apt update
sudo apt apgrade
sudo apt install python3.9.2
sudo apt install git
````

Пакеты для Python
````bash
pip install git+https://github.com/Minege/eSSP.git
pip install pillow
pip install RPi.GPIO
pip install numpy
pip install pygame
````
КОМАНДЫ ДЛЯ GIT:  
клонирование с GITHUB
````bash
git clone https://github.com/AleksandrElizarov/VendingMachine.git
````
обновление с GITHUB
````bash
git pull origin
````

увидеть, какие файлы были изменены, добавлены или удалены
````bash
git status
````

просмотреть конкретные изменения в файлах
````bash
git diff
````

добавить все измененные файлы в индекс (подготовить к коммиту)
````bash
git add --all
````

комментарии к коммиту
````bash
git commit -m "Ваш комментарий к коммиту здесь"
````

просмотр списка существующих веток
````bash
git branch
````

 отправить изменения на GitHub
````bash
git push origin
````

Настройка демона для автоматической загрузки скрипта
````bash
which python3.9
locate python3.9
````
Обычно, он может быть что-то вроде /usr/bin/python3.9 или /usr/local/bin/python3.9, либо использовать команду dpkg -L python3.9

Создание служебного файла
````bash
sudo nano /etc/systemd/system/vending_machine.service
````

В данный файл добавить код
````bash
[Unit]
Description=Vending Machine Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/vending_machine.py
WorkingDirectory=/home/pi
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

````

А затем выполнить команды
````bash
sudo systemctl daemon-reload
sudo systemctl enable vending_machine.service
sudo systemctl start vending_machine.service
````

Для проверки состояния службы
````bash
sudo systemctl status vending_machine.service
sudo journalctl -u vending_machine.service
````




