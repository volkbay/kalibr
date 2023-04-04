# ETH Kalibr Installation Updates (2023, @volkbay)  #
Bu kamera kalibrasyonu yapmak için kullanılan bir ROS node. Lens calib, stereo calib ve IMU calib gibi işler yapılabilir. GitHub [wiki](https://github.com/ethz-asl/kalibr/wiki)ye bak. Burada bir tutorial ve örnek dosyalar var. Bazen upstream güncelleniyor kontrol. Ayrıca YouTube kalibrasyon videoları var.

İki adımlı kalibrasyon yapıyoruz biz; önce kameranın lens distortion düzeltmek için sonra da kamera-imu arası kalibrasyon.

Bu committe yarattığımız *.volkan* klasörü altında bize ait bilgiler var. Ayrıca *Dockerfile* küçük bir oynama yaptık (git).

Bizim klasörün yapısı:
- **results**: Daha önceki kalibrasyon sonuçları ve kalibrasyon için gerekli yaml dosyaları. IMU noise parametlerini inivation GitLab sayfasından bulduk.
- **aedat2bag.py**: DV aedat4 dosyasını [ROSbag uygun topiclere](https://github.com/ethz-asl/kalibr/wiki/Bag-format) çevirir. Sonraki aşamalarda bagcreate edeceğiz.
- **dv...xml**: DV gui için recording konfigürasyonu.
- **readme.md**
  
## Docker ##
---
Tüm repo indirmeden sadece bir Dockerfile ve *.volkan* indirip kullanmak mantıklı zaten kalibrasyon geliştirme yapılacak bir şey değil. Tek kullanımlık bir tool. Yaklaşık 5GB bir images yaratır.

1. Önce file indirip build et.
    
    ```docker build -t kalibr -f Dockerfile_ros1_20_04 .```

2. Sonra *.volkan* altına bir */dat* klasörü aç.
3. Son olarak build edilen img run edeceğiz. X11 socketing, data klasörü bind mount ve DISPLAY bilgisi vermeyi unutma. Ayrıca .volkan klasörünü indirdiğin yeri aşağıda değiştir.

    ```docker run -it -v /tmp/.X11-unix/:/tmp/.X11-unix:ro -v /run/user/1000/gdm/Xauthority:/root/.Xauthority:ro -v ${HOME}/prj/kalibr/.volkan/dat/:/data:rw -e DISPLAY kalibr```

> Nvidia container toolkit yüklemek gerekebilir.

> Docker Desktop ile GUI işini çözemedik, Docker CE kullan X11 socketing için.

## ROS ##
---
Çekim yapıp .aedat dosyasını */dat* altına *dvSave.aedat4* olarak koy. Python script çalıştırınca */dat/davis_bag* altında gerekli topicler hazır olmalı. Ayrıca gerekli .yaml dosyaları da */dat* altında hazır olsun.
> Frameler için 20 Hz, IMU için 200 Hz önerilir.

> AprilTag veya hangi checkerboard kullanılyorsa yaml dosyasını buna göre güncelle. Gerekirse IMU dosyasında da noise param güncelle.

> İki kalibrasyon için farklı çekimler ve boardlar kullanabiliriz.

> Lens için ekranın her yerini span etmeye, IMU için tüm hareketleri kapsamaya ve smooth olmaya çalış.  

1. Her terminal açılışında ROS env kullanabilmek için:
   
   ```source /catkin_ws/devel/setup.bash```

2. İşleri kolaylaştırmak için
   
   ```export BAG_DIR=/data/davis_bag```

3. Elimizdeki topicleri ROSbag haline çeviririz.
   
   ```rosrun kalibr kalibr_bagcreater --folder /data/bag/ --output-bag $BAG_DIR/davis.bag```

4. İlk kalibrasyon aşaması olan lens calib yapıyoruz. Sonuçları ekrana basması ve pdf/text dosyaları oluşturması gerekir. Pixel error küçük olmalı.
   
   ```rosrun kalibr kalibr_calibrate_cameras --target $BAG_DIR/apriltag.yaml --bag $BAG_DIR/davis.bag --topics /cam0/image_raw --models pinhole-equi```

5. Son aşama olan IMU kalibrasyonu. Bunu bir çok parametresi var aslında. Wikide ve issuelarda param ile ilgili sayafalara bakabilirsin ya da ```--help``` de kısaca.
   
   ```rosrun kalibr kalibr_calibrate_imu_camera --target $BAG_DIR/apriltag.yaml --cam $BAG_DIR/davis-camchain.yaml --imu $BAG_DIR/imu.yaml --bag $BAG_DIR/davis.bag --verbose --show-extraction --bag-from-to 40 80 --timeoffset-padding 0.4 --max-iter 50```

6. Nedense USLAM'de kullanılan swe config dosyasına çeviremiyoruz IMU sonuçlarını. Böyle bir şey gerekirse oradaki örnek swe dosyasına kopyala matris sonuçlarını. Ama vektör yapılarına ve indentlere dikkat et.