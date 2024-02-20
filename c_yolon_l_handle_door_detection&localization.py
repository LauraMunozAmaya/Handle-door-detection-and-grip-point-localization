# -*- coding: utf-8 -*-
"""C_YOLON_L_Handle-door_Detection&Localization.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TZUkjbXZbfpbJH7hFAfy6Lddb_8X_S07

**Handle Door and Door Detection & Localization Model using YOLO NAS Architecture**
/(Add a short introduction later)

##**Steps of the Notebook**



*   Requirements

#**Requirements**
It is desired to ensure that the GPU Accelerator is being used in this notebook, in order to have significally speed up model training times. nvidia-smi command will be used for do that.
"""

!nvidia-smi

"""Installing YOLO-NAS"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# !pip install -q git+https://github.com/Deci-AI/super-gradients.git@stable
# !pip install -q super-gradients==3.2.0
# !pip install -q roboflow
# !pip install -q supervision

"""Reset RunTime

##Dataset
In this project was use Roboflow for the process of create the Data Base and take data from other repositories.

For create the Data Base, it was recorder door and hande door in The UJI and then processed in Roboflow software. In the next steps:


*   Upload Data
*   Make the Localization with the Boundig Box
*   Make the Detection
*   Make labeling - Classes
*   Split th data set for train the model (Train, Valid & Test)
*   Making Preprocessing Data (image transformation)
*   Making Data Augmentation
*   Exporting data in YOLOV5 Pytorch Format

Here the data set is downloaded with your labels and organized in each folder (Training, Test & Validation)
"""

#Dataset Just for Training & Valid (versin 10 Roboflow)
from roboflow import Roboflow
rf = Roboflow(api_key="XXXXXX")
project = rf.workspace("laura-munoz").project("door-handle-detection")
dataset = project.version(10).download("yolov5")

#Dataset Just for test

rf_t = Roboflow(api_key="XXXXXXX")
project_t = rf_t.workspace("laura-munoz").project("test_door_handle_detection")
dataset_t = project_t.version(2).download("yolov5")

"""## Class Definition"""

from typing import List, Dict
class config:
    # Project paths
    DATA_DIR: str = "/content/Door-handle-detection-10"
    CHECKPOINT_DIR: str = "/content/checkpoints"
    EXPERIMENT_NAME: str = "tesis_detection_localization_model_yoloNAS_L"

    # Datasets
    TRAIN_IMAGES_DIR: str = "/content/Door-handle-detection-10/train/images"
    TRAIN_LABELS_DIR: str = "/content/Door-handle-detection-10/train/labels"
    VAL_IMAGES_DIR: str = "/content/Door-handle-detection-10/valid/images"
    VAL_LABELS_DIR: str = "/content/Door-handle-detection-10/valid/labels"
    TEST_IMAGES_DIR: str = "/content/Test_Door_Handle_Detection-2/test/images"
    TEST_LABELS_DIR: str = "/content/Test_Door_Handle_Detection-2/test/labels"

    # Classes
    CLASSES: List[str] = ['Door','Handle-Door']
    NUM_CLASSES: int = len(CLASSES)

    # Model
    DATALOADER_PARAMS: Dict = {
      'batch_size': 16,
      'num_workers': 1
    }
    MODEL_NAME: str = 'yolo_nas_l'
    PRETRAINED_WEIGHTS: str = 'coco'

"""##DataLouders initialization"""

from super_gradients.training import Trainer
from super_gradients.training.dataloaders.dataloaders import coco_detection_yolo_format_train
from super_gradients.training.dataloaders.dataloaders import coco_detection_yolo_format_val

train_data = coco_detection_yolo_format_train(
    dataset_params={
        'data_dir': config.DATA_DIR,
        'images_dir': config.TRAIN_IMAGES_DIR,
        'labels_dir': config.TRAIN_LABELS_DIR,
        'classes': config.CLASSES
    },
    dataloader_params=config.DATALOADER_PARAMS
)

test_data = coco_detection_yolo_format_val(
    dataset_params={
        'data_dir': config.DATA_DIR,
        'images_dir': config.TEST_IMAGES_DIR,
        'labels_dir': config.TEST_LABELS_DIR,
        'classes': config.CLASSES
    },
    dataloader_params=config.DATALOADER_PARAMS
)

val_data = coco_detection_yolo_format_val(
    dataset_params={
        'data_dir': config.DATA_DIR,
        'images_dir': config.VAL_IMAGES_DIR,
        'labels_dir': config.VAL_LABELS_DIR,
        'classes': config.CLASSES
    },
    dataloader_params=config.DATALOADER_PARAMS
)

train_data.dataset.transforms

"""##Visualization"""

val_data.dataset.plot()

test_data.dataset.plot()

"""##Training hyperparameters

Estudiar a fondo los hiperparametros y ver cuales vale la pea modificar, si es que se pueden modificar
"""

from super_gradients.training.losses import PPYoloELoss
from super_gradients.training.metrics import DetectionMetrics_050
from super_gradients.training.models.detection_models.pp_yolo_e import PPYoloEPostPredictionCallback

train_params = {
    "average_best_models":True,
    "warmup_mode": "linear_epoch_step",
    "warmup_initial_lr": 1e-6,
    "lr_warmup_epochs": 3,
    "initial_lr": 5e-4,
    "lr_mode": "cosine",
    "cosine_final_lr_ratio": 0.1,
    "optimizer": "Adam",
    "optimizer_params": {"weight_decay": 0.001},
    "zero_weight_decay_on_bias_and_bn": True,
    "ema": True,
    "ema_params": {"decay": 0.9, "decay_type": "threshold"},
    "max_epochs": 30,
    "mixed_precision": True,
    "loss": PPYoloELoss(
        use_static_assigner=False,
        num_classes=config.NUM_CLASSES,
        reg_max=16
    ),
    "valid_metrics_list": [
        DetectionMetrics_050(
            score_thres=0.1,
            top_k_predictions=300,
            num_cls=config.NUM_CLASSES,
            normalize_targets=True,
            post_prediction_callback=PPYoloEPostPredictionCallback(
                score_threshold=0.01,
                nms_top_k=1000,
                max_predictions=300,
                nms_threshold=0.7
            )
        )
    ],
    "metric_to_watch": 'mAP@0.50'
}

"""##Training Model"""

# Model Download. Yolo-NAS_L Model is downloaded
from super_gradients.training import models
model = models.get(config.MODEL_NAME, #YOLO_NAS_L
                   num_classes=config.NUM_CLASSES,
                   pretrained_weights=config.PRETRAINED_WEIGHTS)  #PRETRAINED_WEIGHTS = "coco"

#Trainer Initializating
#Experiment name (described before), and in checkpoints will be saved (Betters results, average, ephocs, weigths, mAP (mil Average Presicion))
trainer = Trainer(experiment_name=config.EXPERIMENT_NAME,
                  ckpt_root_dir=config.CHECKPOINT_DIR)

#Train
trainer.train(model=model,
              training_params=train_params,
              train_loader=train_data,
              valid_loader=val_data)

"""Loading the best Model"""

import os
best_model = models.get(config.MODEL_NAME,
                        num_classes=config.NUM_CLASSES,
                        checkpoint_path=os.path.join(config.CHECKPOINT_DIR, config.EXPERIMENT_NAME, '/content/checkpoints/tesis_detection_localization_model_yoloNAS_L/average_model.pth'))

from google.colab import files
files.download('/content/checkpoints')

"""Evaliating the best trained Model"""

###############   REVISAR COMO DECIDE CUAL ES EL MEJOR MODELO, SI ES BASANDOSE EN UNA METRICA EN ESPECIFICO O SI TOMA UN PONDERADO
trainer.test(model=best_model,
            test_loader=test_data,
            test_metrics_list=DetectionMetrics_050(score_thres=0.1,
                                                   top_k_predictions=300,
                                                   num_cls=config.NUM_CLASSES,
                                                   normalize_targets=True,
                                                   post_prediction_callback=PPYoloEPostPredictionCallback(score_threshold=0.01,
                                                                                                          nms_top_k=1000,
                                                                                                          max_predictions=300,
                                                                                                          nms_threshold=0.7)
                                                  ))

"""Visualization"""

import cv2
import numpy as np

#img = cv2.imread("/content/Door-handle-detection-6/valid/images/VID_20200803_134024_mp4-16_jpg.rf.360b41da70c44413aeffa47ec54f9574.jpg")

#img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

#outputs = best_model.predict(img)

#----------
path_img = ("/content/Door-handle-detection-8/valid/images/")

selected_img = random.sample(path_img, k=1)

img = cv2.imread(selected_img)

img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

outputs = best_model.predict(img)

print(outputs)
outputs.show()

#Selecting a random image from path image
import cv2
import numpy as np
import os
import random

#path to the directory containing images
path_img = ("/content/Test_Door_Handle_Detection-2/test/images/")

#List all images in the directory
file_img = os.listdir(path_img)

#Selecting a random subset of images from the list (file_imgs)
selected_imgs = random.sample(file_img, k=10)

#initialize a list to store the loaded images
images = []

#Loop through the selected image file names, read and convert in RGB color
for img_file in selected_imgs:
  img_path = os.path.join(path_img, img_file) #recreating path file complete name
  img = cv2.imread(img_path)  #Uploading images in cv2 format
  img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) #converting in RGB color

  if img is not None:
    images.append(img) #Adding image selected in "images" list
  else:
    print(f"Failed to load image: {img_file}")

outputs = best_model.predict(images)

print(outputs)
outputs.show()

"""Confusión Matrix"""

#Inference
import supervision as sv

ds = sv.DetectionDataset.from_yolo(
    images_directory_path=f"{dataset_t.location}/test/images",
    annotations_directory_path=f"{dataset_t.location}/test/labels",
    data_yaml_path=f"{dataset_t.location}/data.yaml",
    force_masks=False
)

#wITH A CONFIDENCE UMBRAL tresholf of 0.5, In this lines I will take the images that are up of 50% of predection from the test dataset
# I took coordinates, result of prediction, and the number (0 or 1) of the class for each image in test dataset
import supervision as sv

CONFIDENCE_TRESHOLD = 0.5

predictions = {}

for image_name, image in ds.images.items():
    result = list(best_model.predict(image, conf=CONFIDENCE_TRESHOLD))[0]
    detections = sv.Detections(
        xyxy=result.prediction.bboxes_xyxy,
        confidence=result.prediction.confidence,
        class_id=result.prediction.labels.astype(int)
    )
    predictions[image_name] = detections

"""Visualize inference result"""

import random
random.seed(10)

# Commented out IPython magic to ensure Python compatibility.
import supervision as sv

MAX_IMAGE_COUNT = 5

n = min(MAX_IMAGE_COUNT, len(ds.images))

keys = list(ds.images.keys())
keys = random.sample(keys, n)

box_annotator = sv.BoxAnnotator()

images = []
titles = []

for key in keys:
    frame_with_annotations = box_annotator.annotate(
        scene=ds.images[key].copy(),
        detections=ds.annotations[key],
        skip_label=True
    )
    images.append(frame_with_annotations)
    titles.append('annotations')
    frame_with_predictions = box_annotator.annotate(
        scene=ds.images[key].copy(),
        detections=predictions[key],
        skip_label=True
    )
    images.append(frame_with_predictions)
    titles.append('predictions')

# %matplotlib inline
sv.plot_images_grid(images=images, titles=titles, grid_size=(n, 2), size=(2 * 4, n * 4))

"""Calculating confusion matrix"""

# Intenta configurar el locale de forma diferente
!export LC_ALL=C.UTF-8
!export LANG=C.UTF-8

!pip install onemetric

import os

import numpy as np

from onemetric.cv.object_detection import ConfusionMatrix

keys = list(ds.images.keys())

annotation_batches, prediction_batches = [], []

for key in keys:
    annotation=ds.annotations[key]
    annotation_batch = np.column_stack((
        annotation.xyxy,
        annotation.class_id
    ))
    annotation_batches.append(annotation_batch)

    prediction=predictions[key]
    prediction_batch = np.column_stack((
        prediction.xyxy,
        prediction.class_id,
        prediction.confidence
    ))
    prediction_batches.append(prediction_batch)

confusion_matrix = ConfusionMatrix.from_detections(
    true_batches=annotation_batches,
    detection_batches=prediction_batches,
    num_classes=len(ds.classes),
    conf_threshold=CONFIDENCE_TRESHOLD
)

confusion_matrix.plot(os.path.join(HOME, "confusion_matrix.png"), class_names=ds.classes)

"""
#**Playing with treshold 0.50**"""

trainer.test(model=best_model,
            test_loader=test_data,
            test_metrics_list=DetectionMetrics_050(score_thres=0.5,
                                                   top_k_predictions=300,
                                                   num_cls=config.NUM_CLASSES,
                                                   normalize_targets=True,
                                                   post_prediction_callback=PPYoloEPostPredictionCallback(score_threshold=0.01,
                                                                                                          nms_top_k=1000,
                                                                                                          max_predictions=300,
                                                                                                          nms_threshold=0.7)
                                                  ))

#Selecting a random image from path image
import cv2
import numpy as np
import os
import random

#path to the directory containing images
path_img = ("/content/Test_Door_Handle_Detection-2/test/images/")

#List all images in the directory
file_img = os.listdir(path_img)

#Selecting a random subset of images from the list (file_imgs)
selected_imgs = random.sample(file_img, k=10)

#initialize a list to store the loaded images
images = []

#Loop through the selected image file names, read and convert in RGB color
for img_file in selected_imgs:
  img_path = os.path.join(path_img, img_file) #recreating path file complete name
  img = cv2.imread(img_path)  #Uploading images in cv2 format
  img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) #converting in RGB color

  if img is not None:
    images.append(img) #Adding image selected in "images" list
  else:
    print(f"Failed to load image: {img_file}")

outputs = best_model.predict(images)

print(outputs)
outputs.show()

"""#**cONFUSION MATRIX**"""

#CONFUSION MATRIX
#Inference
import supervision as sv

ds = sv.DetectionDataset.from_yolo(
    images_directory_path=f"{dataset_t.location}/test/images",
    annotations_directory_path=f"{dataset_t.location}/test/labels",
    data_yaml_path=f"{dataset_t.location}/data.yaml",
    force_masks=False
)

#wITH A CONFIDENCE UMBRAL tresholf of 0.5, In this lines I will take the images that are up of 50% of predection from the test dataset
# I took coordinates, result of prediction, and the number (0 or 1) of the class for each image in test dataset
import supervision as sv

CONFIDENCE_TRESHOLD = 0.5

predictions = {}

for image_name, image in ds.images.items():
    result = list(best_model.predict(image, conf=CONFIDENCE_TRESHOLD))[0]
    detections = sv.Detections(
        xyxy=result.prediction.bboxes_xyxy,
        confidence=result.prediction.confidence,
        class_id=result.prediction.labels.astype(int)
    )
    predictions[image_name] = detections

import random
random.seed(10)

# Commented out IPython magic to ensure Python compatibility.
import supervision as sv

MAX_IMAGE_COUNT = 5

n = min(MAX_IMAGE_COUNT, len(ds.images))

keys = list(ds.images.keys())
keys = random.sample(keys, n)

box_annotator = sv.BoxAnnotator()

images = []
titles = []

for key in keys:
    frame_with_annotations = box_annotator.annotate(
        scene=ds.images[key].copy(),
        detections=ds.annotations[key],
        skip_label=True
    )
    images.append(frame_with_annotations)
    titles.append('annotations')
    frame_with_predictions = box_annotator.annotate(
        scene=ds.images[key].copy(),
        detections=predictions[key],
        skip_label=True
    )
    images.append(frame_with_predictions)
    titles.append('predictions')

# %matplotlib inline
sv.plot_images_grid(images=images, titles=titles, grid_size=(n, 2), size=(2 * 4, n * 4))

import locale
locale.getpreferredencoding = lambda: "UTF-8"

!pip install onemetric

import os

import numpy as np

from onemetric.cv.object_detection import ConfusionMatrix

keys = list(ds.images.keys())

annotation_batches, prediction_batches = [], []

for key in keys:
    annotation=ds.annotations[key]
    annotation_batch = np.column_stack((
        annotation.xyxy,
        annotation.class_id
    ))
    annotation_batches.append(annotation_batch)

    prediction=predictions[key]
    prediction_batch = np.column_stack((
        prediction.xyxy,
        prediction.class_id,
        prediction.confidence
    ))
    prediction_batches.append(prediction_batch)

confusion_matrix = ConfusionMatrix.from_detections(
    true_batches=annotation_batches,
    detection_batches=prediction_batches,
    num_classes=len(ds.classes),
    conf_threshold=CONFIDENCE_TRESHOLD
)

confusion_matrix.plot(os.path.join(HOME, "confusion_matrix.png"), class_names=ds.classes)