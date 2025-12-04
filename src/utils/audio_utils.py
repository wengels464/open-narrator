import numpy as np

def create_silence(duration_sec, sample_rate=24000):
    """
    Creates a silence audio segment of specified duration.
    """
    return np.zeros(int(sample_rate * duration_sec), dtype=np.float32)

def trim_silence(audio, threshold=0.01, padding_sec=0.0, sample_rate=24000):
    """
    Trims silence from the end of an audio array.
    
    Args:
        audio: Numpy array of audio data
        threshold: Amplitude threshold below which is considered silence
        padding_sec: Amount of silence to leave at the end (in seconds)
        sample_rate: Sample rate of the audio
    
    Returns:
        Trimmed audio array
    """
    if len(audio) == 0:
        return audio
        
    # Find the last index where amplitude > threshold
    # We iterate backwards
    non_silent_indices = np.where(np.abs(audio) > threshold)[0]
    
    if len(non_silent_indices) == 0:
        # All silent
        return np.array([], dtype=np.float32)
        
    last_non_silent = non_silent_indices[-1]
    
    # Calculate padding samples
    padding_samples = int(padding_sec * sample_rate)
    
    end_index = min(len(audio), last_non_silent + 1 + padding_samples)
    
    return audio[:end_index]
