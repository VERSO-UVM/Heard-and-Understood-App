import consert
import os

class ConsertProcess:
    def __init__(self, filename, proj_name, recname):
        """Initiate consert with the uploaded file"""
        print("starting init")
        self.proj_dir = "hua/static/audio/" + proj_name + '/' + recname
        self.check_dirs(proj_name, recname)
        filename = "hua/" + filename
        self.run_consert(filename, proj_name)
    
    def check_dirs(self, proj_name, recname):
        # TODO: If it does exist do we want a copy of this data?
        if not os.path.exists(self.proj_dir):
            os.makedirs(self.proj_dir)
            os.makedirs(self.proj_dir + "/output")
        
    def run_consert(self, media_file, proj_name):
        print("starting consert")
        # Test 1: Run pause identification and classification
        consert.classify_pauses(
            input_filepath=media_file,
            output_directory=self.proj_dir + "/output",  # TODO: Adjust output path as needed
            save_output_file=True,
            save_intermediate_files=True,
            audio_file_format='mp3',          # Ensure correct format for 'mp3'
            whisper_model_name='medium'
        )

        # Test 2: Plot results
        consert.plot_classification(media_file, self.proj_dir + "/output") 
# Initialize the class to run the process
#process = ConsertProcess()