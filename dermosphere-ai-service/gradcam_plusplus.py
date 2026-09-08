import numpy as np
import tensorflow as tf
import cv2

def generate_gradcam_plusplus(model, img_array, metadata_tensors, save_path, layer_name="top_conv"):
    """
    Extracts spatial hierarchies using Grad-CAM++ algorithms, supporting multi-input fusion models.
    """
    grad_model = tf.keras.models.Model(
        [model.inputs], 
        [model.get_layer(layer_name).output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model([img_array, *metadata_tensors])
        class_idx = tf.argmax(predictions[0])
        loss = predictions[:, class_idx]

    # First, Second, and Third derivative gradients for Grad-CAM++
    first_grads = tape.gradient(loss, conv_outputs)
    
    # Approximate second and third derivatives (simplified for inference speed)
    second_grads = tf.square(first_grads)
    third_grads = first_grads * second_grads

    global_sum = tf.reduce_sum(conv_outputs, axis=(0, 1, 2))
    alpha_num = second_grads
    alpha_denom = second_grads * 2.0 + third_grads * tf.reshape(global_sum, (1, 1, 1, -1))
    alpha_denom = tf.where(alpha_denom != 0.0, alpha_denom, tf.ones_like(alpha_denom))
    alphas = alpha_num / alpha_denom

    weights = tf.maximum(first_grads, 0.0)
    alpha_normalization = tf.reduce_sum(alphas * weights, axis=(1, 2))
    
    heatmap = tf.reduce_sum(alpha_normalization * conv_outputs, axis=-1)
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    heatmap = heatmap.numpy()[0]

    # Apply Jet Colormap
    heatmap = cv2.resize(heatmap, (224, 224))
    heatmap = np.uint8(255 * heatmap)
    heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    
    cv2.imwrite(save_path, heatmap_colored)
    return save_path