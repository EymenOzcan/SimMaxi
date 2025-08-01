Projeyi ayağa kaldırıp fonksiyonları kullanmak için env aktif edip celery çalıştırmak gerekiyor fonksiyonlar celery üzerinden çalışıyor 

celery:
celery -A simmaxi worker --loglevel=info --pool=solo(windows)

env:
source/venv/scripts/activate
