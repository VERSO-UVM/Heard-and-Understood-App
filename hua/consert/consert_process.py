import consert

class ConsertProcess:
    def __init__(self, filename, proj_name):
        """Initiate consert with the uploaded file"""
        print("starting init")
        filename = "hua/" + filename
        self.run_consert(filename, proj_name)

    def run_consert(self, media_file, proj_name):
        # Test 1: Run pause identification and classification
        consert.classify_pauses(
            input_filepath=media_file,
            output_directory='hua/static/audio/' + proj_name,  # TODO: Adjust output path as needed
            save_output_file=True,
            save_intermediate_files=True,
            audio_file_format='mp3',          # Ensure correct format for 'mp3'
            whisper_model_name='medium'
        )

        # Test 2: Plot results
        consert.plot_classification(media_file, 'hua/static/audio/' + proj_name) 
# Initialize the class to run the process
#process = ConsertProcess()