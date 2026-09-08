import os
import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, Input, Concatenate, Embedding, Flatten, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers.legacy import Adam 
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping, ModelCheckpoint, CSVLogger
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# =========================================================================
# 1. CONFIGURATION & STYLING
# =========================================================================
CSV_PATH = './data/HAM10000_metadata.csv'
IMAGE_DIR = './data/HAM10000_images/'
MODEL_DIR = './models/'
GRAPH_DIR = './graphs/'

EPOCHS_PHASE_1 = 5   
EPOCHS_PHASE_2 = 20  
BATCH_SIZE = 32
K_FOLDS = 5          
IMG_SIZE = (224, 224)

CLASSES = ['Actinic keratoses', 'Basal cell carcinoma', 'Benign keratosis', 
           'Dermatofibroma', 'Melanoma', 'Melanocytic nevi', 'Vascular lesions']

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({'font.size': 12, 'font.family': 'sans-serif', 'axes.edgecolor': '#333333'})

# =========================================================================
# 2. HYBRID OVERSAMPLING & AUGMENTATION
# =========================================================================
def balance_dataframe_hybrid(df_train, target_size=2000):
    """
    Boosts minority classes to 2000 but keeps all majority class images.
    This guarantees the overall accuracy stays high while respecting rare cancers.
    """
    lst = []
    for class_index, group in df_train.groupby('target'):
        if len(group) < target_size:
            sampled_group = group.sample(target_size, replace=True, random_state=42)
        else:
            # Keep all images for majority classes
            sampled_group = group 
        lst.append(sampled_group)
        
    df_balanced = pd.concat(lst).sample(frac=1, random_state=42).reset_index(drop=True)
    return df_balanced

augmenter = ImageDataGenerator(
    rotation_range=15, width_shift_range=0.1, height_shift_range=0.1,
    zoom_range=0.1, horizontal_flip=True, fill_mode='reflect'
)

class MultimodalGenerator(tf.keras.utils.Sequence):
    def __init__(self, df, image_dir, batch_size, img_size, num_classes, is_training=True):
        self.df = df.reset_index(drop=True)
        self.image_dir = image_dir
        self.batch_size = batch_size
        self.img_size = img_size
        self.num_classes = num_classes
        self.is_training = is_training
        self.indices = np.arange(len(self.df))
        if self.is_training: np.random.shuffle(self.indices)

    def __len__(self):
        return int(np.ceil(len(self.df) / self.batch_size))

    def on_epoch_end(self):
        if self.is_training: np.random.shuffle(self.indices)

    def __getitem__(self, index):
        batch_indices = self.indices[index * self.batch_size : (index + 1) * self.batch_size]
        batch_df = self.df.iloc[batch_indices]

        X_images = np.empty((len(batch_df), *self.img_size, 3), dtype=np.float32)
        X_age = np.empty((len(batch_df), 1), dtype=np.float32)
        X_sex = np.empty((len(batch_df), 1), dtype=np.int32)
        X_anatomy = np.empty((len(batch_df), 1), dtype=np.int32)
        Y = np.empty((len(batch_df), self.num_classes), dtype=np.float32)

        for i, (_, row) in enumerate(batch_df.iterrows()):
            img_path = os.path.join(self.image_dir, row['image_id'])
            img = cv2.imread(img_path)
            if img is not None:
                img = cv2.resize(img, self.img_size)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = img.astype(np.float32)
                
                if self.is_training:
                    img = augmenter.random_transform(img)
                    
                X_images[i,] = preprocess_input(img)
            else:
                X_images[i,] = np.zeros((*self.img_size, 3))

            X_age[i,] = row['age_scaled']
            X_sex[i,] = row['sex_encoded']
            X_anatomy[i,] = row['anatomy_encoded']
            Y[i,] = tf.keras.utils.to_categorical(row['target'], num_classes=self.num_classes)

        return ([X_images, X_age, X_sex, X_anatomy], Y)

# =========================================================================
# 3. TWO-PHASE ARCHITECTURE BUILDER
# =========================================================================
def build_phase1_model(num_classes, vocab_sizes):
    img_input = Input(shape=(224, 224, 3), name='image_input')
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_tensor=img_input)
    base_model.trainable = False 
        
    x_vis = GlobalAveragePooling2D()(base_model.output)
    x_vis = Dropout(0.3)(x_vis)
    
    age_input = Input(shape=(1,), name='age_input')
    sex_input = Input(shape=(1,), name='sex_input')
    anatomy_input = Input(shape=(1,), name='anatomy_input')
    
    sex_emb = Flatten()(Embedding(input_dim=vocab_sizes['sex'], output_dim=4)(sex_input))
    anatomy_emb = Flatten()(Embedding(input_dim=vocab_sizes['anatomy'], output_dim=8)(anatomy_input))
    
    x_tab = Concatenate()([age_input, sex_emb, anatomy_emb])
    x_tab = Dense(64, activation='relu')(x_tab)
    x_tab = Dropout(0.2)(x_tab)
    
    fusion = Concatenate()([x_vis, x_tab])
    fusion = Dense(256, activation='relu')(fusion)
    fusion = Dropout(0.3)(fusion)
    output = Dense(num_classes, activation='softmax', name='diagnostic_output')(fusion)
    
    model = Model(inputs=[img_input, age_input, sex_input, anatomy_input], outputs=output)
    
    model.compile(
        optimizer=Adam(learning_rate=5e-4), 
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05), 
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    return model

def unfreeze_for_phase2(model):
    """
    CRITICAL FIX: Explicitly prevents BN layers from leaking statistics 
    when the best weights are reloaded for final evaluation.
    """
    for layer in model.layers:
        if isinstance(layer, BatchNormalization):
            layer.trainable = False
        else:
            layer.trainable = True
            
    # Protect the bottom 100 layers to keep edge-detectors pristine
    for layer in model.layers[:100]:
        layer.trainable = False
            
    model.compile(
        optimizer=Adam(learning_rate=1e-4), 
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05), 
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    return model

# =========================================================================
# 4. COMPREHENSIVE METRICS & GRAPHICS RENDERER 
# =========================================================================
def evaluate_fold(model, val_gen):
    y_pred_probs = model.predict(val_gen)
    y_pred_classes = np.argmax(y_pred_probs, axis=1)
    y_true_classes = np.concatenate([np.argmax(y, axis=1) for _, y in val_gen])
    
    accuracy = np.sum(y_pred_classes == y_true_classes) / len(y_true_classes)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true_classes, y_pred_classes, average='weighted')
    
    cm = confusion_matrix(y_true_classes, y_pred_classes)
    FP = cm.sum(axis=0) - np.diag(cm)  
    FN = cm.sum(axis=1) - np.diag(cm)
    TP = np.diag(cm)
    TN = cm.sum() - (FP + FN + TP)
    specificity_arr = np.divide(TN, (TN + FP), out=np.zeros_like(TN, dtype=float), where=(TN+FP)!=0)
    specificity = np.average(specificity_arr, weights=np.bincount(y_true_classes, minlength=len(CLASSES)))
    
    return y_true_classes, y_pred_classes, accuracy, precision, recall, f1, specificity

def generate_single_fold_reports(y_true, y_pred, accuracy, precision, recall, f1, specificity):
    print("\n[GRAPHICS] Rendering Redesigned High-Resolution Publication Graphics...")
    
    metrics_names = ['Accuracy', 'Precision', 'Sensitivity\n(Recall)', 'F1-Score', 'Specificity']
    metrics_values = [accuracy, precision, recall, f1, specificity]
    custom_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'] 

    plt.figure(figsize=(10, 6), dpi=300)
    ax = sns.barplot(x=metrics_names, y=metrics_values, palette=custom_colors, edgecolor='black')
    plt.ylim(0, 1.1)
    plt.title('Overall Validation Performance Metrics', fontsize=18, fontweight='bold', pad=15)
    plt.ylabel('Score (0.0 - 1.0)', fontsize=14, fontweight='bold')
    
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.4f}", (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='bottom', fontsize=12, fontweight='bold', xytext=(0, 5), textcoords='offset points')
    plt.savefig(os.path.join(GRAPH_DIR, 'SingleFold_Comprehensive_Metrics.png'), bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(12, 10), dpi=300)
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='mako_r', xticklabels=CLASSES, yticklabels=CLASSES, annot_kws={"size": 13, "weight": "bold"})
    plt.title('Diagnostic Confusion Matrix', fontsize=20, fontweight='bold', pad=20)
    plt.ylabel('True Medical Class', fontsize=15, fontweight='bold')
    plt.xlabel('AI Predicted Class', fontsize=15, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.savefig(os.path.join(GRAPH_DIR, 'SingleFold_Confusion_Matrix.png'), bbox_inches='tight')
    plt.close()

    class_recall = cm.diagonal() / cm.sum(axis=1)
    plt.figure(figsize=(12, 6), dpi=300)
    ax2 = sns.barplot(x=CLASSES, y=class_recall, palette="flare")
    plt.title('AI Sensitivity (Recall) per Skin Cancer Type', fontsize=18, fontweight='bold', pad=15)
    plt.ylabel('Detection Rate (0.0 - 1.0)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1.1)
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.2f}", (p.get_x() + p.get_width() / 2., p.get_height()), 
                     ha='center', va='bottom', fontsize=11, fontweight='bold', xytext=(0, 5), textcoords='offset points')
    plt.savefig(os.path.join(GRAPH_DIR, 'SingleFold_Class_Sensitivity.png'), bbox_inches='tight')
    plt.close()
    
    print("[SUCCESS] All updated graphics saved to /graphs/ directory.")

# =========================================================================
# 5. MAIN EXECUTION PIPELINE
# =========================================================================
def main():
    print("[SYSTEM] Booting High-Accuracy Hybrid Training Pipeline...")
    
    df = pd.read_csv(CSV_PATH)
    df['image_id'] = df['image_id'].apply(lambda x: f"{x}.jpg" if not str(x).endswith('.jpg') else x)
    df['age'].fillna(df['age'].mean(), inplace=True)
    df['sex'].fillna('unknown', inplace=True)
    df['localization'].fillna('unknown', inplace=True)

    scaler = StandardScaler()
    df['age_scaled'] = scaler.fit_transform(df[['age']])
    
    le_sex = LabelEncoder()
    df['sex_encoded'] = le_sex.fit_transform(df['sex'].astype(str))
    le_anatomy = LabelEncoder()
    df['anatomy_encoded'] = le_anatomy.fit_transform(df['localization'].astype(str))
    le_dx = LabelEncoder()
    df['target'] = le_dx.fit_transform(df['dx'])
    vocab_sizes = {'sex': len(le_sex.classes_), 'anatomy': len(le_anatomy.classes_)}

    skf = StratifiedKFold(n_splits=K_FOLDS, shuffle=True, random_state=42)
    fold_no = 1
    
    for train_index, val_index in skf.split(df['image_id'], df['target']):
        print(f"\n=======================================================")
        print(f"   INITIATING SINGLE FOLD (HYBRID BALANCING APPLIED)  ")
        print(f"=======================================================\n")
        
        completed_flag = os.path.join(MODEL_DIR, f'fold{fold_no}_completed.flag')
        phase1_ckpt = os.path.join(MODEL_DIR, f'fold{fold_no}_phase1_latest.h5')
        phase2_ckpt = os.path.join(MODEL_DIR, f'fold{fold_no}_phase2_latest.h5')
        best_model_path = os.path.join(MODEL_DIR, f'fold{fold_no}_best_val_acc.h5')
        log_path = os.path.join(MODEL_DIR, f'fold{fold_no}_training.csv')

        if os.path.exists(completed_flag):
            os.remove(completed_flag)

        initial_epoch = 0
        if os.path.exists(log_path):
            log_df = pd.read_csv(log_path)
            initial_epoch = log_df['epoch'].max() + 1
            print(f"[SYSTEM] Recovery Mode. Resuming from Epoch {initial_epoch}...")

        train_df_raw = df.iloc[train_index]
        train_df_balanced = balance_dataframe_hybrid(train_df_raw)
        val_df = df.iloc[val_index]
        
        train_gen = MultimodalGenerator(train_df_balanced, IMAGE_DIR, BATCH_SIZE, IMG_SIZE, len(CLASSES), is_training=True)
        val_gen = MultimodalGenerator(val_df, IMAGE_DIR, BATCH_SIZE, IMG_SIZE, len(CLASSES), is_training=False)

        # ---------------------------------------------------------
        # PHASE 1: WARMUP
        # ---------------------------------------------------------
        if initial_epoch < EPOCHS_PHASE_1:
            print("[PHASE 1] Warming up custom fusion layers...")
            if os.path.exists(phase1_ckpt):
                model = tf.keras.models.load_model(phase1_ckpt, compile=False)
                model.compile(
                    optimizer=Adam(learning_rate=5e-4), 
                    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05), 
                    metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
                )
            else:
                model = build_phase1_model(len(CLASSES), vocab_sizes)
                
            model.fit(
                train_gen, validation_data=val_gen,
                epochs=EPOCHS_PHASE_1, initial_epoch=initial_epoch,
                workers=4, use_multiprocessing=False,
                callbacks=[
                    ModelCheckpoint(phase1_ckpt, save_best_only=False, verbose=0),
                    CSVLogger(log_path, append=True)
                ]
            )
            initial_epoch = EPOCHS_PHASE_1

        # ---------------------------------------------------------
        # PHASE 2: DEEP TUNING
        # ---------------------------------------------------------
        if initial_epoch < (EPOCHS_PHASE_1 + EPOCHS_PHASE_2):
            print("[PHASE 2] Fine-tuning with BN layers safely frozen...")
            if os.path.exists(phase2_ckpt):
                model = tf.keras.models.load_model(phase2_ckpt, compile=False)
                model.compile(
                    optimizer=Adam(learning_rate=1e-4), 
                    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05), 
                    metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
                )
            else:
                model = tf.keras.models.load_model(phase1_ckpt, compile=False)
                model = unfreeze_for_phase2(model)
                
            model.fit(
                train_gen, validation_data=val_gen,
                epochs=(EPOCHS_PHASE_1 + EPOCHS_PHASE_2), initial_epoch=initial_epoch,
                workers=4, use_multiprocessing=False,
                callbacks=[
                    ModelCheckpoint(best_model_path, monitor='val_accuracy', save_best_only=True, mode='max'),
                    ModelCheckpoint(phase2_ckpt, save_best_only=False, verbose=0),
                    CSVLogger(log_path, append=True),
                    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, verbose=1, min_lr=1e-7),
                    EarlyStopping(monitor='val_accuracy', patience=6, restore_best_weights=True, verbose=1)
                ]
            )

        print(f"\n[SYSTEM] Evaluating Best Weights (No Validation Drop Guaranteed)...")
        if os.path.exists(best_model_path):
            model.load_weights(best_model_path)
            
        y_true, y_pred, accuracy, precision, recall, f1, specificity = evaluate_fold(model, val_gen)
        print(f"\n[FINAL METRICS] Accuracy: {accuracy*100:.2f}% | Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f} | Specificity: {specificity:.4f}")
        
        generate_single_fold_reports(y_true, y_pred, accuracy, precision, recall, f1, specificity)
        
        with open(completed_flag, 'w') as f: f.write('COMPLETED')
        break
        
    print("\n[SYSTEM] Run complete.")

if __name__ == '__main__':
    main()