# HEARD & UNDERSTOOD<sup>tm</sup> App

[![DOI](https://zenodo.org/badge/851837059.svg)](https://doi.org/10.5281/zenodo.14649131)

The HEARD & UNDERSTOOD<sup>tm</sup> App provides a way to explore and classify silence and gaps in conversations.

## Description
This is an [Open Community Research Accelerator (ORCA)](https://verso.w3.uvm.edu/orca/) project in collaboration with the [Vermont Conversation Lab](https://vermontconversationlab.com/) and their GitHub organization [HEARD & UNDERSTOOD<sup>tm</sup>](https://github.com/heard-and-understood). This supports the exploration and adoption of the CONSert (Connectional Silence Ensemble-BERT) algorithm which uses a combination of Random Forests, Convolutional Neural Networks, OpenAI Whisper Transcriptions and a BERT ML model to detect, locate and classify pauses. Pauses will be classified as either Non-Connectional, Emotional, or Invitational.

Pause Types:

* Non-Connectional - a pause that does not provide connectional context for the rest of the conversation
* Emotional - a pause which provides time for emotional reflection
* Invitational - a pause that invites another speaker to interact with the conversation

The methods used in this package are based on the methods used in Matt et al. 2023.

Matt et al. 2023: Matt, Jeremy E et al. “An Acoustical and Lexical Machine-Learning Pipeline to Identify Connectional Silences.” Journal of palliative medicine, 10.1089/jpm.2023.0087. 13 Jul. 2023, doi:10.1089/jpm.2023.0087

## Getting Started

### Installing
You will need Python 3.10 or earlier installed.

To install for development, clone this repository, navigate to it, and run `pip install -e .` (don't miss the period at the end)

To install for production/testing, download the .whl file for the appropriate version from the releases tab and run `pip install hua-1.0.0-py2.py3-none-any.whl` replacing the version to match your downloaded file.

If you want to use CONSert, follow the steps in the [Consert Install Guide](hua/consert/CONSERT_INSTALLATION.md)

### Executing program
Make sure you have `serviceAccountKey.json` and `email_credentials.py`.
If you installed from source for development, they'll need to be in the project's root directory.
if you installed from a `.whl` for production/testing, they'll simply need to be in whatever directory you run the app from.

Run `flask --app hua run`

### Building program
If you haven't already, install `build` by running `pip install build`

Then, whenever you'd like to build a new `.whl` file, run `python -m build --wheel` in the project's root directory. The `.whl` file will appear in the `dist` directory.

## Help and FAQs

### credentials.py and serviceAccountKey.json
These files are not visible on GitHub as they contain sensitive information. For access to them, please reach out to the admin or developer that gave you access to the repository in the first place. 
<br><br>
As of 10/30/25, we have an email-based alert system for alerting the Admins to new PI access requests. Temporarily, there is not a proper email associated with this as we are still determining who will be in charge of distributing PI access. 

### Unpickle version mismatch
The following warning regarding the version mismatch can be ignored, the algorithm will still run as expected.
>InconsistentVersionWarning: Trying to unpickle estimator LabelEncoder from version 1.0.2 when using version 1.3.0. This might lead to breaking code or invalid results. Use at your own risk. For more info please refer to:
https://scikit-learn.org/stable/model_persistence.html#security-maintainability-limitations

### User system and Firebase
Account information (username, institute, email, etc.) is stored externally in a Google Firebase. This is how we keep track of users relevant information like what projects they are involved in, or what status their account has. 
<br><br>
Accounts are split into __User__ which is the default permission level, __PI__, and __Admin__. __PI__ accounts are able to generate new projects and project codes for the __Users__ in their labs.
<br><br>
__No sensitive audio file information is stored in the Firebase.__ Audio files are only ever stored in your computer's local storage. The inputs and outputs all stay within that specific Flask instance.

### Running CONSERT on your audio file
1. Create an instance of the Flask app.
2. Sign in to the Heard & Understood Application.
3. From the homepage, click `Click to Enter Project Access Code` and enter the project code associated with your lab.
    - Note that without a project code, you __cannot__ run the CONSERT algorithm on an audio file. To generate project codes, you need an account with __PI access__. This can be requested via the `Request PI Access` navigation tab. 
4. Once you have a project associated with your account, it will appear in the `Projects` drowndown. Clicking it will bring you to the project __dashboard__. 
5. If your audio file is already in storage, you can select it from the `Recording` dropdown. Otherwise, navigate to the `Upload Audio Files` navigation tab. Select your file from local storage, and add it to the Flask app's local storage (lets Flask know where to access the file to run the CONSERT algorithm).
6. If necessary, return to the `Dashboard` tab. Select your audio file from the dropdown, and click `Run Algorithm`. 
   - Note: This process may take a while, especially if your audio file is lengthy. The command line outputs progess as the algorithm works, and we are working to add feedback to the front-end of the application. 
7. When CONSERT finishes, it will alert your browser, and then display the output png.
8. __Future work__: Functionality for `View Confusion Matrix` and ability to filter pause classifications is in progress. `Ground Truthing` __does__ make changes to the output csv, but there is no visualization in the current implementation.


### Expectations for output
There should be 19 files generated by running CONSERT. For an audio file named `test_audio.mp3`, the list of files includes:
* test_audio_bert_prediction.csv <br>
* test_audio_bert_prediction.npy<br>
* test_audio_classification.csv<br>
* test_audio_classification.png<br>
* test_audio_cnn_prediction.csv<br>
* test_audio_cnn_prediction.npy<br>
* test_audio_metadata.json<br>
* test_audio_metrics.csv<br>
* test_audio_metrics.npy<br>
* test_audio_pauses.csv<br>
* test_audio_pauses.npy<br>
* test_audio_rf_prediction.csv<br>
* test_audio_rf_prediction.npy<br>
* test_audio_spectrograms.csv<br>
* test_audio_spectrograms.npy<br>
* test_audio_transcription.csv<br>
* test_audio_transcription.json<br>
* test_audio_transcription.npy<br>
* test_audio_transcription.txt<br>


## Team

### Fall 2024
* Fernanda De Oliveira Girelli (Team Lead)
* Johnna  Schulz
* Adrien Monks
* Tucker  Schulz 
* Felix Walberg
* Grace Kinney (Designer/UX)

### Spring 2025
* Fernanda De Oliveira Girelli (Team Lead)
* Johnna  Schulz
* Tucker  Schulz 
* Shiloh Chiu
* Aurelia Kornheiser
* Grace Kinney (Designer/UX)
  
## Version History

TBD

## License

This project is licensed under the Apache 2.0 License - see the LICENSE.md file for details

## Acknowledgments
This project would not be possible without Robert "Bob" Gramling, MD and Donna Rizzo and the work by the [Vermont Conversation Lab](https://vermontconversationlab.com/) at the University of Vermont (UVM) and funding through the [EpsCor SOCKS](https://www.uvm.edu/socks/#about) grant.
