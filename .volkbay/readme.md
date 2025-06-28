# ETH Kalibr Installation Updates (2023, @volkbay)  #
Bu kamera kalibrasyonu yapmak için kullanılan bir ROS uygulamasıdır. Lens kalibrasyonu, stereo ve kamera-IMU kalibrasoynu gibi işler yapılabilir. GitHub [wiki](https://github.com/ethz-asl/kalibr/wiki)ye bak. Burada bir tutorial ve örnek dosyalar var. Bazen upstream güncelleniyor, kontrol etmeyi unutma. Ayrıca YouTube'da kalibrasyon videoları var.

İki veya üç adımlı kalibrasyon yapıyoruz; varsa stereo kameralar arası kalibrasyon, kameranın lens distortion düzeltmek için intrinsicler sonra da kamera-IMU arası kalibrasyon. 

Ben işime yarayacak YAML dosyalarını ve ihtiyacımıza göre bir *Dockerfile*'ı oluşturdum. IMU noise parametlerini inivation GitLab sayfasından bulduk.

Kalibre etmek için kullanılacak verinin iki yolu var:
- **Aedat-Bag Çevrimi**: DV AEDAT4 dosyasını [ROSbag uygun topiclere](https://github.com/ethz-asl/kalibr/wiki/Bag-format) çevirir. Sonraki aşamalarda `bagcreate` edeceğiz.
- **Bag Record**: `rosbag record` ile direkt olarak bag formatında veriyi toplayabiliriz.
  
## Docker ##
1. Önce file indirip kur.
    
   ```
   docker build -t kalibr -f Dockerfile .
   ```

2. Sonra host bilgisayarda bir */data* klasörü aç.
3. Son olarak kurulan Docker image'ini çalıştır. X11 socketing, data klasörü bind mount ve DISPLAY değişkenini vermeyi unutma.

    ```
    export DATASET_LOC=./data

    docker run -it --privileged --net=host -v /dev/bus/usb:/dev/bus/usb \
      -v /run/user/1000/gdm/Xauthority:/root/.Xauthority \
      -v /run/user/1000/:/run/user/1000/ \
      -v /tmp/.X11-unix/:/tmp/.X11-unix/ -v ${DATASET_LOC}:/data -e DISPLAY \
      --env=NVIDIA_DRIVER_CAPABILITIES=all --gpus all --runtime=nvidia kalibr
    ```

> [!IMPORTANT]
> Nvidia container toolkit yüklemek gerekebilir.

> [!CAUTION]
> Docker Desktop ile GUI işini çözemedik, Docker CE kullan X11 socketing için.

## ROS ##
Çekim yapıp AEDAT veya rosbag dosyasını */data* altına koy. AEDAT çevrimi için Python kodunu çalıştırınca, */data/davis_bag* altında gerekli rostopic'ler hazır olmalı. Ayrıca gerekli YAML dosyaları da */data* altında hazır olsun.

> [!NOTE]
> Frameler için 20 Hz, IMU için 200 Hz önerilir.

> [!IMPORTANT]
> AprilTag veya hangi checkerboard kullanılyorsa YAML dosyasını buna göre güncelle. Gerekirse IMU dosyasında da noise parametrelerini güncelle.

> [!NOTE]
> İki kalibrasyon için farklı çekimler ve boardlar kullanabiliriz. Ama genel olarak aprilTag iş yapar.

> [!IMPORTANT]
> Lens için ekranın her yerini, IMU için tüm hareketleri kapsamaya ve akışkan hareketler yapmaya çalış.  

1. İşleri kolaylaştırmak için
   
   ```
   export BAG_DIR=/data/davis_bag
   ```

2. Elimizdeki topicleri ROSbag haline çeviririz.
   
   ```
   rosrun kalibr kalibr_bagcreater --folder $BAG_DIR --output-bag $BAG_DIR/davis.bag
   ```

4. İlk kalibrasyon aşaması olan lens kalibrasyonu ve varsa multi-kamera kalibrasyonu yapıyoruz. Sonuçları ekrana basması ve PDF/metin dosyaları oluşturması gerekir. Piksel hataları küçük olmalı.
   
   ```
   # Mono kamera
   rosrun kalibr kalibr_calibrate_cameras --target $BAG_DIR/apriltag.yaml --bag $BAG_DIR/davis.bag --topics /cam0/image_raw --models pinhole-equi
   
   # Stereo kamera
   rosrun kalibr kalibr_calibrate_cameras --target $BAG_DIR/apriltag.yaml --bag $BAG_DIR/davis.bag --topics /cam0/image_raw /cam1/image_raw --models pinhole-radtan pinhole-radtan --bag-freq 20.0
   ```

5. Son aşama olan IMU kalibrasyonu. Bunu bir çok parametresi var aslında. Wikide ve issuelarda param ile ilgili sayafalara bakabilirsin ya da ```--help``` de kısaca.
   
   ```
   rosrun kalibr kalibr_calibrate_imu_camera --target $BAG_DIR/apriltag.yaml --cam $BAG_DIR/davis-camchain.yaml --imu $BAG_DIR/imu.yaml --bag $BAG_DIR/davis.bag --verbose --show-extraction --bag-from-to 40 80 --timeoffset-padding 0.4 --max-iter 50
   ```

> [!CAUTION]
> USLAM'de kullanılan swe config dosyasına çeviremiyoruz IMU sonuçlarını. Böyle bir şey gerekirse oradaki örnek swe dosyasına kopyala matris sonuçlarını. Ama vektör yapılarına ve indentlere dikkat et.