import onnxruntime as ort
import numpy as np

# ĐƯỜNG DẪN MODEL
model_path = "best.onnx"

# Khởi tạo ONNX Runtime
session = ort.InferenceSession(model_path)

# Xem input của model
inputs = session.get_inputs()
print("Inputs:", inputs)

# Tạo 1 input giả (random)
input_shape = inputs[0].shape
dummy_input = np.random.rand(*[1] + input_shape[1:]).astype(np.float32)

# Chạy thử model
outputs = session.run(None, {inputs[0].name: dummy_input})

print("Output OK -> Model chạy được!")
print("Output shape:", [o.shape for o in outputs])
