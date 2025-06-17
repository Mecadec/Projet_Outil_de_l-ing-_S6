ls -ld /tmp/etu0118_logs
ls
cd ..
ls
cd etu0118
ls
ls
cd php
ls
pip install fastapi uvicorn
ls -l /var/www/etu0118/php/predict.php
chmod 755 /var/www/etu0118/php/predict.php
dos2unix /var/www/etu0118/predict_cli.py
perl -pi -e 's/\r$//' /var/www/etu0118/predict_cli.py
head -1 /var/www/etu0118/predict_cli.py
python3 -V
pip install fastapi uvicorn joblib numpy
uvicorn predict_service:app --host 0.0.0.0 --port 8000
pip install fastapi uvicorn joblib numpy
python3 -m uvicorn predict_service:app --host 127.0.0.1 --port 8000 --reload
