# CONSert Installation for HUA

## Introduction

The consert package is host to the CONSert (Connectional Silence Ensemble-BERT) algorithm which uses a combination of Random Forests, Convolutional Neural Networks, OpenAI Whisper Transcriptions and a BERT ML model to detect, locate and classify pauses. Pauses will be classified as either Non-Connectional, Emotional, or Invitational. 

Read more here: https://github.com/Heard-and-Understood/CONSert

## Installing the CONSert Package

This section of the guide is meant for HUA contributors who have access to the CONSert repository.  

As of 10/24/2024 testing and implementation of CONSert has been done with CONDA environments running python 3.10.11. The linux/macos version of this package must be run on python 3.10 or earlier. 

### Pip Install Via Local Repository

Start by cloning the repository from github into your desired directory and activating any desired virtual environment.
If you are a owner/maintainer/developer you can install the packagage via pip install (path to cloned repo).

```
pip install path/to/cloned/CONSert
```

### Pip Install Via Github Repository

Alternatively the package can be installed without the original source code.

```
pip install git+https://github.com/Heard-and-Understood/CONSert.git
```

### The Models

CONSert's pause detection and classification requires several models to run: CNN, RF, and BERT. The paths to the models are specified in package.json which can be found in the root directory of the package:
```
/consert/package.json
```
and looks like this:

```
  "model_cache": "absolute/path/to/original_code/models",
  "model_temp": "~/Downloads",
  "trained_cnn_model_name": "cnn_pause_det_itr0_epoch0.hdf5",
  "trained_cnn_model_path": "absolute/path/to/original_code/models/CNN/cnn_pause_det_itr0_epoch0.hdf5",
  "trained_rf_model_name": "rf_pause_det.pickle",
  "trained_rf_model_path": "absolute/path/to/original_code/models/RF/rf_pause_det.pickle",
  "trained_bert_model_name": "bert_pause_class_10f_epoch0",
  "trained_bert_model_path": "absolute/path/to/original_code/models/BERT/bert_pause_class_10f_epoch0"
```

Update your model paths by replacaing: aboslute/path/to/ with the absolute path to the original code directory. When you're done, save the packages.json file.

As of now we are not sure the best practice for storing these models in git. The can be transferred as .tar compressed file using fileshare. Create a directory title BERT inside "absolute/path/to/original_code/models/ " and extract the tar file here.

### Whisper AI Transcription

As of 10/21/24 there is a bug in whisper_timestamped that causes it to fail transcriptions with the latest copy of Whisper. To avoid this, run the following once CONSert is fully installed:

```
pip3 install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git@v20231117

```
This will downgrade the version of Whisper to the most recent compatable version. Whisper now includes timestamps, which it didn't when CONSert was developed. Eventually, we'll want to remove whisper_timestamped and use a more recent version of Whisper, instead.

### Testing 

You can verify the package's installation via:
````
 pip show consert
````

Once consert has been installed update the path to media file in [Consert Test Script](consert_test_script.py) and give it a run. If consert is able to fully process it will create a summary png in the test_output directory.


