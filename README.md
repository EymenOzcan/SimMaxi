Markdown

# SimMaxi

![Proje Durumu](https://img.shields.io/badge/Durum-Geliştirme_Aşamasında-yellow)
![Lisans](https://img.shields.io/github/license/EymenOzcan/SimMaxi)

## 📝 Açıklama

SimMaxi, modern web teknolojilerini kullanarak oluşturulmuş, modüler ve ölçeklenebilir bir web uygulamasıdır. Projenin ana hedefi, belirli bir alanda (örneğin, simülasyon, veri analizi veya özel bir iş akışı) kullanıcıların ihtiyaçlarına cevap veren kapsamlı bir platform sunmaktır. Şu an için temel yapılandırma ve çekirdek özellikler üzerinde çalışmalar devam etmektedir.

## ✨ Özellikler

Projenin tamamlandığında içermesi planlanan başlıca özellikler:

* **Kullanıcı Yönetimi:** Güvenli kullanıcı kayıt, giriş ve profil yönetimi.
* **Görev Yönetimi:** Celery ile arka planda asenkron görevleri yürütme yeteneği.
* **Veri Yönetimi:** PostgreSQL veritabanı ile güçlü ve yapılandırılmış veri saklama.
* **Web Arayüzü:** Django'nun güçlü şablon yapısı ile dinamik web sayfaları.
* **Modüler Yapı:** Kolayca yeni özellikler eklenmesine olanak tanıyan organize edilmiş bir kod tabanı.

## 🚀 Teknolojiler

Bu proje, aşağıdaki temel teknolojiler üzerine inşa edilmiştir:

* **Arka Uç:** Python, Django
* **Veritabanı:** PostgreSQL
* **Asenkron Görevler:** Celery
* **Mesaj Kuyruğu:** Redis
* **Paket Yönetimi:** Pip

## 🛠️ Kurulum

Projenin yerel makinenizde çalıştırılması için aşağıdaki adımları izleyin:

### 1. Depoyu Klonlama

Öncelikle projeyi yerel makinenize klonlayın:

```bash
git clone [https://github.com/EymenOzcan/SimMaxi.git](https://github.com/EymenOzcan/SimMaxi.git)
cd SimMaxi
2. Sanal Ortam Oluşturma
Python bağımlılıkları için bir sanal ortam oluşturup etkinleştirin:

Bash

python -m venv venv
# Windows için
.\venv\Scripts\activate
# macOS/Linux için
source venv/bin/activate
3. Bağımlılıkları Yükleme
Gerekli tüm Python paketlerini requirements.txt dosyasından yükleyin:

Bash

pip install -r requirements.txt
4. Veritabanı Kurulumu
PostgreSQL sunucunuzun çalıştığından emin olun ve veritabanı bağlantı ayarlarınızı settings.py dosyasında güncelleyin. Ardından, veritabanı şemasını oluşturmak için göçleri çalıştırın:

Bash

python manage.py makemigrations
python manage.py migrate
5. Celery ve Redis Kurulumu
Celery ve Redis'i kullanabilmek için yerel makinenizde Redis sunucusunun çalıştığından emin olun. Gerekirse Redis'i resmi web sitesinden indirip çalıştırabilirsiniz.

6. Geliştirme Sunucusunu Başlatma
Son olarak, projeyi başlatmak için Django'nun geliştirme sunucusunu çalıştırın:

Bash

python manage.py runserver
Uygulamaya tarayıcınızdan http://127.0.0.1:8000/ adresinden erişebilirsiniz.

🤝 Katkıda Bulunma
Proje hala geliştirme aşamasında ve katkılarınıza açıktır. Eğer katkıda bulunmak isterseniz, lütfen aşağıdaki adımları izleyin:

Projenin kod deposunu (fork) kopyalayın.

Yeni bir özellik veya hata giderme için yeni bir dal (branch) oluşturun: git checkout -b ozellik/yeni-ozellik

Değişikliklerinizi yapın ve commit mesajınızı yazın: git commit -m 'feat: yeni özellik eklendi'

Değişikliklerinizi kendi dalınıza gönderin: git push origin ozellik/yeni-ozellik

GitHub üzerinden bir "Pull Request" oluşturun.

📄 Lisans
Bu proje, MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için LICENSE dosyasına bakabilirsiniz.
