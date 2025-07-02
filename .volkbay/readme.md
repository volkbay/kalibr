# ETH Kalibr Installation Updates [@volkbay, 2025]
Bu kamera kalibrasyonu yapmak için kullanılan bir ROS uygulamasıdır. Lens kalibrasyonu, stereo kameralar ve kamera-IMU kalibrasyonu gibi işler yapılabilir. Dokümantasyon için orijinal repoda [wikiye](https://github.com/ethz-asl/kalibr/wiki) bak. Burada tutorial ve örnek dosyalar var. Ayrıca YouTube'da ekstra [tutoriallar](https://youtu.be/BtzmsuJemgI?si=wn6cBYtmsPNjo46X) için bakabiliriz. Nadiren upstream güncelleniyor, kontrol etmeyi unutma.

İki veya üç adımlı kalibrasyon yapıyoruz; varsa stereo kameralar arası extrinsic kalibrasyon, kameranın lens distortion düzeltmek için intrinsicler sonra da kamera-IMU arası extrinsic kalibrasyon. 

Ben işime yarayacak YAML dosyalarını `/yaml` altına koydum ve ihtiyacımıza göre bir `Dockerfile` oluşturdum. IMU noise parametrelerini inivation GitLab sayfasından bulduk. AprilTag boyutlarını ve kameranın IMU parametrelerini güncellemeyi gerekirse unurma.
  
## Docker ##
1. Önce file indirip kur.
    
   ```
   docker build -t kalibr -f Dockerfile .
   ```

2. Sonra host bilgisayarda bir `/data` klasörü aç.
3. Son olarak kurulan Docker image'ini çalıştır. X11 socketing, data klasörü bind mount ve DISPLAY değişkenini vermeyi unutma.

    ```
    export DATASET_LOC=/data

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

## Çekim Yapmak ##

Herhangi yöntemi seçip çekim yaptıktan sonra finalde, ilgili `/data` klasöründe ROSbag hazır olmalıdır. Ama bu işlemden önce DV-GUI veya Kalibr ile odak ayarlaması yapmayı ve lens vidalarını sabitlemeyi unutma.

Kalibre etmek için kullanılacak verinin oluşturulmasının iki yolu var:
- **AEDAT4-ROSbag Çevrimi**: Host PC'de DV-GUI üzerinden görüntü almak istersen bunu takip etmelisin. Önce DV'nin AEDAT4 dosyasını [ROSbag uygun topiclere](https://github.com/ethz-asl/kalibr/wiki/Bag-format) çeviririz. Bu iş için internette Python kodları mevcut. Sonra aşağıda verildiği gibi `bagcreate` ile birleştiririz.
- **ROSbag Record**: `rosbag record` ile direkt olarak bag formatında veriyi toplayabiliriz. Bunun için bir event-based ROS driver kurmuş olmak gerekir. _Dockerfile_ içinde driver kurulumunu yapıyorum ve kamera configleri başka bir projeden çekiyorum. Direkt burada çekim yapabiliriz.

## ROS ##
Çekim yapıp AEDAT4 veya ROSbag dosyasını `/data` altına koyduk. AEDAT4 çevrimi için Python kodunu çalıştırınca, `/data/davis_bag` altında gerekli rostopicler hazır olmalı. Ayrıca YAML dosyaları da `/data` altında olsun.

> [!NOTE]
> Frameler için 20 Hz, IMU için 200 Hz önerilir.

> [!IMPORTANT]
> AprilTag veya hangi checkerboard kullanılyorsa YAML dosyasını buna göre güncelle. Gerekirse IMU dosyasında da noise parametrelerini güncelle.

> [!NOTE]
> İki kalibrasyon için farklı çekimler ve boardlar kullanabiliriz. Ama genel olarak aprilTag iş yapar.

> [!IMPORTANT]
> Lens için ekranın her yerini, IMU için tüm hareketleri kapsamaya ve akışkan hareketler yapmaya çalış.  

1. Docker container başlatıp içine girelim. İşleri kolaylaştırmak için
   
   ```
   export DATA_DIR=/data
   export BAG_DIR=${DATA_DIR}/davis_bag
   ```

2. Eğer AEDAT4 çekimi yaptıysak elimizdeki topicleri ROSbag haline çevirmeliyiz.
   
   ```
   rosrun kalibr kalibr_bagcreater --folder $BAG_DIR --output-bag $DATA_DIR/davis.bag
   ```

4. İlk kalibrasyon aşaması olan lens kalibrasyonu ve varsa multi-kamera kalibrasyonu yapıyoruz. Sonuçları ekrana basması ve PDF/metin dosyaları oluşturması gerekir. Piksel hataları küçük olmalı.
   
   ```
   # Mono kamera
   rosrun kalibr kalibr_calibrate_cameras --target $DATA_DIR/apriltag.yaml --bag $DATA_DIR/davis.bag --topics /cam0/image_raw --models pinhole-equi
   
   # Stereo kamera
   rosrun kalibr kalibr_calibrate_cameras --target $DATA_DIR/apriltag.yaml --bag $DATA_DIR/davis.bag --topics /cam0/image_raw /cam1/image_raw --models pinhole-radtan pinhole-radtan --bag-freq 20.0
   ```

5. Son aşama olan IMU kalibrasyonu. Bunu bir çok parametresi var aslında. Wikide ve issuelarda param ile ilgili sayafalara bakabilirsin ya da ```--help``` de kısaca.
   
   ```
   rosrun kalibr kalibr_calibrate_imu_camera --target $DATA_DIR/apriltag.yaml --cam $DATA_DIR/davis-camchain.yaml --imu $DATA_DIR/imu.yaml --bag $DATA_DIR/davis.bag --verbose --show-extraction --bag-from-to 40 80 --timeoffset-padding 0.4 --max-iter 50
   ```

> [!CAUTION]
> USLAM'de kullanılan swe config dosyasına çeviremiyoruz IMU sonuçlarını. Böyle bir şey gerekirse oradaki örnek swe dosyasına kopyala matris sonuçlarını. Ama vektör yapılarına ve indentlere dikkat et.
