import consert

class ConsertProcess:
    def __init__(self):
        """Initializes the ConsertProcess with test data and runs consert."""
        print("starting init")
        self.media_file = '/Users/tucker/Documents/ORCA/CONSert/test_video.mp3' #TODO will need to adjust for input data
        self.run_consert(self.media_file)

    def run_consert(self, media_file):
        # Test 1: Run pause identification and classification
        consert.classify_pauses(
            input_filepath=media_file,
            output_directory='test_output',  # TODO: Adjust output path as needed
            save_output_file=True,
            save_intermediate_files=True,
            audio_file_format='mp3',          # Ensure correct format for 'mp3'
            whisper_model_name='medium'
        )

        # Test 2: Plot results
        consert.plot_classification(media_file, 'test_output')

# Initialize the class to run the process
process = ConsertProcess()
