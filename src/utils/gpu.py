import onnxruntime as ort

def get_gpu_info():
    """
    Returns a tuple (is_available, device_name)
    """
    providers = ort.get_available_providers()
    
    if 'CUDAExecutionProvider' in providers:
        return True, "NVIDIA CUDA"
    elif 'DmlExecutionProvider' in providers:
        return True, "DirectML (Windows)"
    elif 'CoreMLExecutionProvider' in providers:
        return True, "CoreML (macOS)"
    else:
        return False, "CPU Mode"
