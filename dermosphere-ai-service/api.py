import os
import time
import traceback
import cv2
import numpy as np
import tensorflow as tf

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

router = APIRouter(
    prefix="/api/v1/triage",
    tags=["Triage"]
)

MODEL_PATH = os.path.join(BASE_DIR, "models", "fold1_best_val_acc.h5")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
HEATMAP_FILE = os.path.join(STATIC_DIR, "latest_heatmap.jpg")

CLASSES = [
    "Actinic keratoses",
    "Basal cell carcinoma",
    "Benign keratosis",
    "Dermatofibroma",
    "Melanoma",
    "Melanocytic nevi",
    "Vascular lesions"
]

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

model = None

def load_ai_model():
    global model
    try:
        print("================================")
        print("[SYSTEM] Loading DermoSphere AI model...")
        print(f"[SYSTEM] Model path: {MODEL_PATH}")
        print("================================")

        if not os.path.exists(MODEL_PATH):
            print(f"[WARNING] Model file not found at: {MODEL_PATH}. Running without loaded weights.")
            return None

        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print("[SYSTEM] AI model loaded successfully.")
        print(f"[SYSTEM] Model input count: {len(model.inputs)}")

        for index, model_input in enumerate(model.inputs):
            print(
                f"[SYSTEM] Input {index + 1}: "
                f"name={model_input.name}, "
                f"shape={model_input.shape}, "
                f"dtype={model_input.dtype}"
            )

        print(f"[SYSTEM] Model output shape: {model.output_shape}")
        return model

    except Exception as error:
        print("[FATAL ERROR] Model loading failed.")
        print(str(error))
        traceback.print_exc()
        model = None
        return None

load_ai_model()

def get_image_quality(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray_image, cv2.CV_64F).var())
    brightness = float(np.mean(gray_image))
    glare_ratio = float(np.sum(gray_image > 240) / gray_image.size)
    return sharpness, brightness, glare_ratio

def prepare_image(image):
    resized_image = cv2.resize(image, (224, 224))
    rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
    image_tensor = np.expand_dims(rgb_image.astype(np.float32) / 255.0, axis=0)
    return image_tensor

def create_prediction_inputs(image_tensor, age_scaled, sex_encoded, anatomy_encoded):
    if model is None:
        raise RuntimeError("AI model is not loaded.")

    input_count = len(model.inputs)
    if input_count == 1:
        return image_tensor

    if input_count == 4:
        patient_age = np.array([[age_scaled]], dtype=np.float32)
        patient_sex = np.array([[sex_encoded]], dtype=np.int32)
        patient_anatomy = np.array([[anatomy_encoded]], dtype=np.int32)
        return [image_tensor, patient_age, patient_sex, patient_anatomy]

    raise ValueError(f"Unsupported model architecture. Model has {input_count} inputs.")

def save_output_image(image):
    resized_image = cv2.resize(image, (224, 224))
    success = cv2.imwrite(HEATMAP_FILE, resized_image)
    if not success:
        print("[WARNING] Could not save output image.")

@router.get("/test")
async def test_api():
    return {
        "status": "success",
        "message": "Triage API is working",
        "model_loaded": model is not None,
        "model_inputs": len(model.inputs) if model is not None else 0
    }

@router.post("/predict")
async def predict_lesion(request: Request):
    start_time = time.time()
    try:
        print("\n================================")
        print("[SYSTEM] Prediction request received")
        print("================================")

        # 1. Parse Multipart Form Safely (Bypasses FastAPI AsyncExitStack Bug)
        form = await request.form()
        file_obj = form.get("file")
        
        if file_obj is None:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing 'file' field in multipart form-data."}
            )

        file_bytes = await file_obj.read()
        if not file_bytes:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Uploaded image is empty."}
            )

        # Extract numerical form values with defaults
        age_scaled = float(form.get("age_scaled", 0.0))
        sex_encoded = int(form.get("sex_encoded", 0))
        anatomy_encoded = int(form.get("anatomy_encoded", 0))

        if model is None:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "AI model is not loaded on server."}
            )

        # 2. Decode Image Bytes with OpenCV
        image_array = np.frombuffer(file_bytes, dtype=np.uint8)
        original_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if original_image is None:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid image file format."}
            )

        # 3. Image Quality Pre-Checks
        sharpness, brightness, glare_ratio = get_image_quality(original_image)
        print(f"[QUALITY] Sharpness: {sharpness:.2f} | Brightness: {brightness:.2f} | Glare: {glare_ratio:.4f}")

        BLUR_THRESHOLD = 20.0
        MIN_BRIGHTNESS = 30.0
        MAX_BRIGHTNESS = 220.0
        GLARE_THRESHOLD = 0.12

        if sharpness < BLUR_THRESHOLD:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Image is too blurry for neural inference."}
            )

        if brightness < MIN_BRIGHTNESS:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Image lighting too dark."}
            )

        if brightness > MAX_BRIGHTNESS:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Image overexposed/too bright."}
            )

        if glare_ratio > GLARE_THRESHOLD:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Excessive specular glare detected."}
            )

        # 4. Neural Network Inference Execution
        image_tensor = prepare_image(original_image)
        prediction_inputs = create_prediction_inputs(image_tensor, age_scaled, sex_encoded, anatomy_encoded)

        print("[SYSTEM] Running AI inference...")
        predictions = model.predict(prediction_inputs, verbose=0)

        if isinstance(predictions, list):
            predictions = predictions[0]

        predictions = np.asarray(predictions)
        probabilities_array = predictions[0] if predictions.ndim == 2 else predictions

        if len(probabilities_array) != len(CLASSES):
            raise ValueError(f"Model outputs {len(probabilities_array)} classes; configured for {len(CLASSES)}.")

        predicted_index = int(np.argmax(probabilities_array))
        prediction_name = CLASSES[predicted_index]
        confidence = float(probabilities_array[predicted_index])

        probabilities = {CLASSES[i]: float(probabilities_array[i]) for i in range(len(CLASSES))}

        # Triage categorization (Tier 2 = Urgent/Malignant, Tier 1 = Routine/Benign)
        triage_tier = 2 if prediction_name in ["Melanoma", "Basal cell carcinoma"] else 1
        inference_time_ms = round((time.time() - start_time) * 1000, 2)

        save_output_image(original_image)

        print(f"[RESULT] Prediction: {prediction_name} | Confidence: {confidence:.4f} | Latency: {inference_time_ms}ms")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "prediction": prediction_name,
                "confidence": confidence,
                "triage_tier": triage_tier,
                "probabilities": probabilities,
                "heatmap_path": "/static/latest_heatmap.jpg",
                "latency_ms": inference_time_ms
            }
        )

    except Exception as error:
        tb_str = traceback.format_exc()
        print("\n================================")
        print("[ERROR] AI prediction failed")
        print(tb_str)
        print("================================")

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(error),
                "traceback": tb_str
            }
        )