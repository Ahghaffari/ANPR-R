# ANPR Project

This project contains source codes for Automatic Licence Plate Recognition for using in ITS subsytems. Project structured with different section containing:

1. Plate detection
2. Car type detection
3. Car tracker based on plate detection
4. Plate segmentation
5. Digit recognition

## Prerequisites
1. python 3.+
2. RabbitMQ
3. Tensorflow 2
4. OpenCV2+
7. SQL Server

## Development
In order to run the project for development purposes do as following instruction. Note that you should serve the motion and motion side pictures from INPUT/motionframe and INPUT/motionframe_side folders respectively.

```python
virtualenv -p python3 venv
pip install -r requirements.txt
python ocr.py
python tracker.py
``` 

## Deployment
In order to run the project in deployment mode clone the project in deploy environment. Then configure the [config.ini](config.ini) file according to your needs. Then take following steps:
```python
virtualenv -p python3 venv
pip install -r requirements.txt
python ocr.py
python tracker.py
```

## Making executable
First install PyInstaller. Then run following command from project root.

### UNIX:
```python
pyinstaller --paths venv/lib/python3.8/site-packages/tensorflow/python/compiler/tensorrt/trt_convert.py --paths venv/lib/python3.8/site-packages/tensorflow/compiler/tf2tensorrt/ops/gen_trt_ops.py --path venv/lib/python3.8/site-packages/tensorflow --clean --add-data weights/char_best.hdf5:weights/ --add-data weights/char_model.json:weights/ --add-data weights/yolov3tiny-my.cfg:weights/ --add-data weights/yolov3tiny-my_best.weights:weights/ --add-data weights/num_model.json:weights/ --add-data weights/num_best.hdf5:weights/ --add-data weights/plate_RFB_mobile_VOC_epoches_600_eid_ghorban.pth:weights/ --paths venv/lib/python3.8/site-packages/tensorflow/lite/experimental/microfrontend/python/ops/_audio_microfrontend_op.so --paths venv/lib/python3.8/site-packages/tensorflow/lite/ --add-binary venv/lib/python3.8/site-packages/tensorflow/lite/experimental/microfrontend/python/ops/_audio_microfrontend_op.so:tensorflow/lite/experimental/microfrontend/python/ops/ --hidden-import=torchvision --hidden-import=torch --exclude-module 'torch.distributions' --add-data venv/lib/python3.8/site-packages/tensorflow/python/keras/engine/base_layer_v1.py:tensorflow/python/keras/engine/ --add-data assets/bad_plate.jpg:assets --add-data config.ini:. -i assets/icon.ico main.py
```

### WINDOWS:

1-Tracker
```bash
pyinstaller --paths venv\Lib\site-packages\tensorflow\python\compiler\tensorrt\trt_convert.py --paths venv\Lib\site-packages\tensorflow\compiler\tf2tensorrt\ops\gen_trt_ops.py --path venv\Lib\site-packages\tensorflow --paths venv\Lib\site-packages\tensorflow\lite\experimental\microfrontend\python\ops\_audio_microfrontend_op.so --paths venv\Lib\site-packages\tensorflow\lite\ --clean --add-data weights\cc.onnx;weights\ --add-data weights\seg.cfg;weights\ --add-data weights\seg.w;weights\ --add-data weights\nc.onnx;weights\ --add-data weights\pd.xml;weights\ --add-data weights\cpd.w;weights\ --add-data weights\cpd.cfg;weights\ --add-data weights\cd.cfg;weights\ --add-data weights\cd.w;weights\ --add-binary venv\Lib\site-packages\tensorflow\lite\experimental\microfrontend\python\ops\_audio_microfrontend_op.so;tensorflow\lite\experimental\microfrontend\python\ops\ --add-data venv\Lib\site-packages\tensorflow\python\keras\engine\base_layer_v1.py;tensorflow\python\keras\engine\ --add-data assets\bad_plate.jpg;assets\ --add-data assets\slut.xlsx;assets\ --add-data config.ini;. -i assets\tracker.ico tracker.py
```

2-OCR
```bash
pyinstaller --paths venv\Lib\site-packages\tensorflow\python\compiler\tensorrt\trt_convert.py --paths venv\Lib\site-packages\tensorflow\compiler\tf2tensorrt\ops\gen_trt_ops.py --path venv\Lib\site-packages\tensorflow --paths venv\Lib\site-packages\tensorflow\lite\experimental\microfrontend\python\ops\_audio_microfrontend_op.so --paths venv\Lib\site-packages\tensorflow\lite\ --clean --add-data weights\cc.onnx;weights\ --add-data weights\seg.cfg;weights\ --add-data weights\seg.w;weights\ --add-data weights\nc.onnx;weights\ --add-data weights\pd.xml;weights\ --add-data weights\cpd.w;weights\ --add-data weights\cpd.cfg;weights\ --add-data weights\cd.cfg;weights\ --add-data weights\cd.w;weights\ --add-binary venv\Lib\site-packages\tensorflow\lite\experimental\microfrontend\python\ops\_audio_microfrontend_op.so;tensorflow\lite\experimental\microfrontend\python\ops\ --add-data venv\Lib\site-packages\tensorflow\python\keras\engine\base_layer_v1.py;tensorflow\python\keras\engine\ --add-data assets\bad_plate.jpg;assets\ --add-data assets\slut.xlsx;assets\ --add-data config.ini;. -i assets\ocr.ico ocr.py
```

NOTE: If you got following error:
```python
oduleNotFoundError: No module named 'tensorflow.compiler.tf2tensorrt'
```
Open trt_convert.py
```python
vim venv/lib/python3.8/site-packages/tensorflow/python/compiler/tensorrt/trt_convert.py
```
Add following to trt_convert.py
```python
import tensorflow.compiler.tf2tensorrt.ops.gen_trt_ops as gen_trt_ops
```
Then comment lines 64 to 66 as follow:
```python
#gen_trt_ops = LazyLoader(
#    "gen_trt_ops", globals(),
#    "tensorflow.compiler.tf2tensorrt.ops.gen_trt_ops")
```

NOTE: If you got "ModuleNotFoundError: No module named 'pkg_resources.py2_warn'", then Hack in a change to Python37/Lib/site-packages/PyInstaller/hooks/hook-pkg_resources.py
```python
hiddenimports = collect_submodules('pkg_resources._vendor') + ['pkg_resources.py2_warn'] # Added py2_warn for setuptools 45.0 and later.
```

NOTE: If you got error about pypylon after running executable file, just copy and paste "\venv\Lib\site-packages\pypylon" into "\dist\tracker1".