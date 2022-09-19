### lambda環境

lambda function with python3.7

make selenium layer(selenium ver4.1)
``` bash
mkdir ./tmp
mkdir ./tmp/python
pip install selenium==4.1 -t ./tmp/python
zip -r selenium_layer.zip ./tmp/python
```

headless chromium download for 
[headless-chromiun](https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-37/stable-headless-chromium-amazonlinux-2017-03.zip)

chrome driver download for 
[chromedriver](https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip)

labmbda function write for [lambda_function.py](./src/lambda_function.py)

