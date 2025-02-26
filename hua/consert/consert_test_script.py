import consert

media_file = 'path/to/media/file'

# Test 1: run the pauses identification and classification
consert.classify_pauses(
    input_filepath = media_file,
    output_directory = 'hua/consert/test_output',
    save_output_file = True,
    save_intermediate_files = True,
    # use_intermediate_files =
    audio_file_format = 'mp3',   # be sure to change this for other audio formats
    # audio_sampling_rate =
    # cnn_confidence_threshold = 
    # rf_confidence_threshold =
    # frame_length = ,
    # cnn_time_per_prediction =
    # rf_feature_length =
    # rf_feature_step = 
    whisper_model_name = 'medium',
    # whisper_device =
    # whisper_time_before_pause =
    # whisper_time_after_pause =
    # bert_n_folds = 
)

# Test 2: plot results
consert.plot_classification(media_file, 'hua/consert/test_output')