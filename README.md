# Heard-and-Understood-App

[![DOI](https://zenodo.org/badge/851837059.svg)](https://doi.org/10.5281/zenodo.14649131)

The Heard and Understood App provides a way to explore and classify silence and gaps in conversations.

## Description
This is an [Open Community Research Accelerator (ORCA)](https://verso.w3.uvm.edu/orca/) project in collaboration with the [Vermont Conversation Lab](https://vermontconversationlab.com/) and their GitHub organization [Heard & Understood(tm)](https://github.com/heard-and-understood). This supports the exploration and adoption of the CONSert (Connectional Silence Ensemble-BERT) algorithm which uses a combination of Random Forests, Convolutional Neural Networks, OpenAI Whisper Transcriptions and a BERT ML model to detect, locate and classify pauses. Pauses will be classified as either Non-Connectional, Emotional, or Invitational.

Pause Types:

* Non-Connectional - a pause that does not provide connectional context for the rest of the conversation
* Emotional - a pause which provides time for emotional reflection
* Invitational - a pause that invites another speaker to interact with the conversation

The methods used in this package are based on the methods used in Matt et al. 2023.

Matt et al. 2023: Matt, Jeremy E et al. “An Acoustical and Lexical Machine-Learning Pipeline to Identify Connectional Silences.” Journal of palliative medicine, 10.1089/jpm.2023.0087. 13 Jul. 2023, doi:10.1089/jpm.2023.0087

## Getting Started

### Dependencies
You will need Python 3.10 or earlier installed. 

Then use pip to install
- flask
- Flask-Mail
- firebase-admin
- bcrypt
- mysql-connector

If you want to use CONSert, follow the steps in the [Consert Install Guide](hua/consert/CONSERT_INSTALLATION.md)

### Installing
Clone this repository, then add `serviceAccountKey.json` to `flaskApp/firebase`

### Executing program
Run `app.py`

## Help

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
