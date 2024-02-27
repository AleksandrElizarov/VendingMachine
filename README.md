# VendingMachine
Программное обеспечение Вендинг аппарата
Среда разработки и развертывания Raspberry PI 3 Model B

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

#### параметры датчика потока воды 1000мл=5880пульов или 0,17мл=1пульс

