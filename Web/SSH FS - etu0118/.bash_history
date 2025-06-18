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
# 1. Se connecter au serveur
ssh etu0118@projets.isen-ouest.info
cd /var/www/etu0118/
python3 -m venv venv15
ls
source venv15/bin/activate
pip install --upgrade pip
pip install numpy==1.26.4 scikit-learn==1.5.0 pandas joblib
python - <<'PY'
import numpy, sklearn
print("numpy", numpy.__version__, "sklearn", sklearn.__version__)
PY

cd ..
ls 
cd etu0118
ls
chmod 755 vessel_type_predict.py
source /var/www/etu0118/venv15/bin/activate
pip install catboost==1.2.5 
ls -l
ssh → ls -l /var/www/etu0118/venv15/bin/python
ls
cd venv15
ls
cdbin 
cd bin 
ls
realpath python 
realpath pip
cd ..
cd ..
chmod 755 /var/www/etu0118/vessel_type_predict.py
ls-l vessel_type_predict
ls-l vessel_type_predict.py
ls -l vessel_type_predict.py
chmod 755 /var/www/etu0118/vessel_type_predict.py
