# VendingMachine
**Программное обеспечение Вендинг аппарата**<br>
**Среда разработки и развертывания Raspberry PI 3 Model B**

## 📹 Видео демонстрация

[Смотреть видео](https://aleksandrelizarov.github.io/VendingMachine/assets/)

#### параметры датчика YF-S201 потока воды: 1000мл=450пульов или 0,0022мл=1пульс

````bash
sudo apt update
sudo apt upgrade
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
pip install loguru
````
Для работы купюроприемника, в директории заменить содержимое файла eSSP.py из файла CoinInterface/for_change_eSSP.py
````bash
/home/pi/.local/lib/python3.9/site-packages/eSSP
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

НАСТРОЙКА ДЕМОНА ДЛЯ АВТОМАТИЧЕСКОГО ЗАПУСКА СКРИПТА
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
ExecStart=/usr/bin/python3.9 /home/pi/VendingMachine/main_board_control.py
WorkingDirectory=/home/pi
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pi/.Xauthority"
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

````
Сохранение изменений:

Нажмите Ctrl + O (используйте клавишу Ctrl и удерживайте ее, затем нажмите O).
После нажатия Ctrl + O, ниже внизу экрана появится сообщение 
"File Name to Write: /path/to/your/file". Нажмите Enter, чтобы сохранить изменения.
Закрытие файла:

Нажмите Ctrl + X.
Если вы внесли изменения и не сохранили их (не использовали Ctrl + O), 
nano спросит вас, хотите ли вы сохранить изменения перед выходом. 
Нажмите Y (для подтверждения) или N (для отмены сохранения) в соответствии с вашими предпочтениями.

Также, убедитесь, что ваш пользователь (например, pi) принадлежит к группе video. 
Вы можете добавить пользователя в группу video командой:
````bash
sudo usermod -aG video pi
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

НАСТРОЙКА И УСТАНОВКА ДРАЙВЕРОВ ДЛЯ LCD 4'(MPI4008)
````bash
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./MPI4008-show
````
Вращение
````bash
cd LCD-show/
sudo ./rotate.sh 90
````


НАСТРОЙКА И УСТАНОВКА ДРАЙВЕРОВ ДЛЯ LCD 3.5'
````bash
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./LCD35-show
````
Разрешение экрана 1280*720

Установка PYTHON3.12

Убедитесь, что установлены необходимые библиотеки для SSL
````bash
sudo apt-get update
sudo apt-get install libssl-dev libffi-dev
sudo apt-get install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt-get install -y libsmpeg-dev libportmidi-dev libavformat-dev libswscale-dev libjpeg-dev libfreetype6-dev


````
Пересоберите Python с поддержкой SSL
````bash
cd Python-3.12.0
sudo make clean
./configure --enable-optimizations --with-ssl
make -j$(nproc)
sudo make altinstall
````
Добавление новой версии Python в переменную PATH
````bash
nano ~/.bashrc
export PATH="/usr/local/bin:$PATH"
source ~/.bashrc
python3 --version
````
Установка PIP

````bash
wget https://bootstrap.pypa.io/get-pip.py
````

````bash
python3.12 get-pip.py
````

````bash
python3.12 -m pip --version
````







