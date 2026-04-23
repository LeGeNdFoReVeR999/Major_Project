#!/usr/bin/env python3
"""
Phishing URL Detection - Model Training Script (Improved)
Extracts features from raw URLs using intelligent feature calculation
Trains a RandomForestClassifier on phishing URL dataset
"""

import pandas as pd
import numpy as np
import pickle
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Configuration
# ============================================================================

CONFIG = {
    'dataset_path': 'pbl/phishing_url/PhiUSIIL_Phishing_URL_Dataset.csv',
    'test_size': 0.2,
    'random_state': 42,
    'model_output': 'phishing_model.pkl',
    'scaler_output': 'scaler.pkl',
    'label_columns': ['label', 'class', 'target', 'Class'],
    'verbose': True
}

# ============================================================================
# Enhanced Feature Extraction (Same as in app.py)
# ============================================================================

def calculate_url_features(url):
    """
    Extract URL features for phishing detection
    Returns dict with 50 features for RF model
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        full_url_lower = url.lower()
        
        # Basic feature extraction
        url_length = len(url)
        domain_length = len(domain)
        
        # Count special characters
        special_chars = len([c for c in url if not c.isalnum() and c not in ['.', ':', '/', '-', '_']])
        
        # Check HTTPS
        has_https = 1 if url.startswith('https') else 0
        
        # Check for IP address in domain
        has_ip = 1 if re.match(r'\d+\.\d+\.\d+\.\d+', domain) else 0
        
        # Count subdomains
        subdomain_count = domain.count('.') - 1 if '.' in domain else 0
        
        # Character continuation rate
        continuation_rate = 0
        if len(url) > 1:
            repeated = sum(1 for i in range(len(url) - 1) if url[i] == url[i + 1])
            continuation_rate = repeated / len(url)
        
        # TLD length
        try:
            tld = domain.split('.')[-1]
            tld_length = len(tld)
        except:
            tld_length = 0
        
        # Detect impersonation keywords
        bank_keywords = ['bank', 'paypal', 'amazon', 'apple', 'microsoft', 'google', 'ebay', 'linkedin', 'twitter', 'facebook']
        secure_keywords = ['secure', 'verify', 'confirm', 'login', 'account', 'auth', 'update', 'validate', 'check']
        
        # Count how many impersonation keywords in domain
        impersonation_score = 0
        bank_in_domain = 0
        for keyword in bank_keywords:
            if keyword in domain:
                impersonation_score += 1
                if keyword == 'bank':
                    bank_in_domain = 1
        
        # Count secure/verify keywords
        secure_keywords_found = sum(1 for kw in secure_keywords if kw in domain or kw in path)
        
        # Calculate URLSimilarityIndex (intelligent calculation)
        url_similarity = 100
        if impersonation_score > 0 and secure_keywords_found > 0:
            url_similarity = max(20, 100 - (impersonation_score * 15) - (secure_keywords_found * 10))
        elif secure_keywords_found > 2:
            url_similarity = max(30, 100 - (secure_keywords_found * 15))
        elif domain.count('-') > 2:
            url_similarity = max(40, 100 - (domain.count('-') * 10))
        elif has_ip:
            url_similarity = 20
        elif not has_https:
            url_similarity = max(60, url_similarity - 20)
        
        # Detect form submission
        has_form_params = 1 if any(p in full_url_lower for p in ['email', 'password', 'user', 'login', 'account', 'card', 'ssn', 'token']) else 0
        
        # Build features dict matching dataset structure
        features = {
            'URLLength': url_length,
            'DomainLength': domain_length,
            'IsDomainIP': has_ip,
            'URLSimilarityIndex': url_similarity,
            'CharContinuationRate': continuation_rate,
            'TLDLegitimateProb': 1.0 if tld in ['com', 'org', 'net', 'gov'] else 0.3,
            'URLCharProb': (len([c for c in domain if c.isalpha()]) / len(domain)) if domain else 0,
            'TLDLength': tld_length,
            'NoOfSubDomain': subdomain_count,
            'HasObfuscation': 1 if domain.count('-') > 2 else 0,
            'NoOfObfuscatedChar': domain.count('-'),
            'ObfuscationRatio': domain.count('-') / len(domain) if domain else 0,
            'NoOfLettersInURL': len([c for c in url if c.isalpha()]),
            'LetterRatioInURL': len([c for c in url if c.isalpha()]) / len(url) if url else 0,
            'NoOfDegitsInURL': len([c for c in url if c.isdigit()]),
            'DegitRatioInURL': len([c for c in url if c.isdigit()]) / len(url) if url else 0,
            'NoOfEqualsInURL': url.count('='),
            'NoOfQMarkInURL': url.count('?'),
            'NoOfAmpersandInURL': url.count('&'),
            'NoOfOtherSpecialCharsInURL': special_chars,
            'SpacialCharRatioInURL': special_chars / len(url) if url else 0,
            'IsHTTPS': has_https,
            'LineOfCode': 0,
            'LargestLineLength': len(url),
            'HasTitle': 0,
            'DomainTitleMatchScore': 50 if impersonation_score > 0 else 100,
            'URLTitleMatchScore': 50 if secure_keywords_found > 1 else 100,
            'HasFavicon': 0,
            'Robots': 0,
            'IsResponsive': 0,
            'NoOfURLRedirect': url.count('redirect') + url.count('return'),
            'NoOfSelfRedirect': 0,
            'HasDescription': 0,
            'NoOfPopup': 0,
            'NoOfiFrame': 0,
            'HasExternalFormSubmit': has_form_params,
            'HasSocialNet': 0,
            'HasSubmitButton': 0,
            'HasHiddenFields': 0,
            'HasPasswordField': 1 if 'password' in full_url_lower else 0,
            'Bank': bank_in_domain,
            'Pay': 1 if any(kw in domain for kw in ['paypal', 'payment', 'pay']) else 0,
            'Crypto': 1 if any(kw in domain for kw in ['bitcoin', 'crypto', 'blockchain']) else 0,
            'HasCopyrightInfo': 0,
            'NoOfImage': 0,
            'NoOfCSS': 0,
            'NoOfJS': 0,
            'NoOfSelfRef': 0,
            'NoOfEmptyRef': 0,
            'NoOfExternalRef': 1 if 'redirect' in full_url_lower else 0,
        }
        
        return features
    except Exception as e:
        print(f"  Error extracting features from '{url}': {e}")
        return None
    print(f"✅ Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"\nDataset Info:")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Data types:\n{df.dtypes}")
    
    return df

def find_label_column(df):
    """Find the label column in the dataset"""
    print("\n🔍 Searching for label column...")
    
    for col in CONFIG['label_columns']:
        if col.lower() in [c.lower() for c in df.columns]:
            label_col = [c for c in df.columns if c.lower() == col.lower()][0]
            print(f"✅ Found label column: '{label_col}'")
            return label_col
    
    raise ValueError(
        f"Could not find label column. Tried: {CONFIG['label_columns']}\n"
        f"Available columns: {df.columns.tolist()}"
    )

def handle_missing_values(df):
    """Handle missing values"""
    print("\n🧹 Handling missing values...")
    
    missing_before = df.isnull().sum().sum()
    print(f"  Missing values before: {missing_before}")
    
    if missing_before > 0:
        # Show missing value info
        print(f"  Missing per column:")
        print(f"{df.isnull().sum()[df.isnull().sum() > 0]}")
        
        # Drop rows with missing values
        df = df.dropna()
        missing_after = df.isnull().sum().sum()
        print(f"  Missing values after: {missing_after}")
        print(f"  ✅ Removed rows with missing values")
    else:
        print(f"  ✅ No missing values found")
    
    return df

def separate_features_labels(df, label_col):
    """Separate features and labels, keeping only numeric features"""
    print(f"\n📊 Separating features and labels...")
    
    X = df.drop(columns=[label_col])
    y = df[label_col]
    
    # Remove non-numeric columns (strings like URL, Domain, etc.)
    non_numeric_cols = X.select_dtypes(include=['object']).columns.tolist()
    if non_numeric_cols:
        print(f"  Removing non-numeric columns: {non_numeric_cols}")
        X = X.drop(columns=non_numeric_cols)
    
    print(f"  Features shape: {X.shape}")
    print(f"  Labels shape: {y.shape}")
    print(f"  Feature columns used: {X.columns.tolist()}")
    print(f"  Label distribution:")
    print(f"{y.value_counts()}")
    
    return X, y

# ============================================================================
# Model Training
# ============================================================================

def split_data(X, y, test_size=0.2, random_state=42):
    """Split data into train/test sets"""
    print(f"\n✂️  Splitting data (train: {1-test_size:.0%}, test: {test_size:.0%})...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
    
    print(f"  Train set: {X_train.shape[0]} samples")
    print(f"  Test set:  {X_test.shape[0]} samples")
    
    return X_train, X_test, y_train, y_test

def scale_features(X_train, X_test):
    """Standardize features"""
    print(f"\n📈 Scaling features using StandardScaler...")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"  ✅ Features scaled")
    print(f"  Train set - Mean: {X_train_scaled.mean():.4f}, Std: {X_train_scaled.std():.4f}")
    
    return X_train_scaled, X_test_scaled, scaler

def train_model(X_train, y_train):
    """Train RandomForestClassifier"""
    print(f"\n🤖 Training RandomForestClassifier...")
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=CONFIG['random_state'],
        n_jobs=-1,
        verbose=0
    )
    
    model.fit(X_train, y_train)
    print(f"  ✅ Model trained successfully")
    print(f"  Trees: {model.n_estimators}")
    print(f"  Max depth: {model.max_depth}")
    
    return model

# ============================================================================
# Model Evaluation
# ============================================================================

def evaluate_model(model, X_train, X_test, y_train, y_test, feature_names):
    """Evaluate model on train and test sets"""
    print(f"\n📊 Evaluating model...")
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]
    
    # Training metrics
    print(f"\n{'='*60}")
    print(f"TRAINING SET METRICS")
    print(f"{'='*60}")
    train_accuracy = accuracy_score(y_train, y_train_pred)
    train_precision = precision_score(y_train, y_train_pred, average='weighted')
    train_recall = recall_score(y_train, y_train_pred, average='weighted')
    train_f1 = f1_score(y_train, y_train_pred, average='weighted')
    
    print(f"  Accuracy:  {train_accuracy:.4f} ({train_accuracy*100:.2f}%)")
    print(f"  Precision: {train_precision:.4f}")
    print(f"  Recall:    {train_recall:.4f}")
    print(f"  F1-Score:  {train_f1:.4f}")
    
    # Test metrics
    print(f"\n{'='*60}")
    print(f"TEST SET METRICS")
    print(f"{'='*60}")
    test_accuracy = accuracy_score(y_test, y_test_pred)
    test_precision = precision_score(y_test, y_test_pred, average='weighted')
    test_recall = recall_score(y_test, y_test_pred, average='weighted')
    test_f1 = f1_score(y_test, y_test_pred, average='weighted')
    
    print(f"  Accuracy:  {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    print(f"  Precision: {test_precision:.4f}")
    print(f"  Recall:    {test_recall:.4f}")
    print(f"  F1-Score:  {test_f1:.4f}")
    
    # ROC-AUC for binary classification
    try:
        roc_auc = roc_auc_score(y_test, y_test_proba)
        print(f"  ROC-AUC:   {roc_auc:.4f}")
    except:
        print(f"  ROC-AUC:   N/A (multi-class)")
    
    # Confusion matrix
    print(f"\n{'='*60}")
    print(f"CONFUSION MATRIX (TEST SET)")
    print(f"{'='*60}")
    cm = confusion_matrix(y_test, y_test_pred)
    print(f"{cm}")
    
    # Classification report
    print(f"\n{'='*60}")
    print(f"CLASSIFICATION REPORT (TEST SET)")
    print(f"{'='*60}")
    print(classification_report(y_test, y_test_pred))
    
    # Feature importance
    print(f"\n{'='*60}")
    print(f"TOP 20 FEATURE IMPORTANCE")
    print(f"{'='*60}")
    
    importances = model.feature_importances_
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print(f"\n{feature_importance.head(20).to_string(index=False)}")
    
    # Save feature importance
    feature_importance.to_csv('feature_importance.csv', index=False)
    print(f"\n✅ Feature importance saved to: feature_importance.csv")
    
    return {
        'train_accuracy': train_accuracy,
        'test_accuracy': test_accuracy,
        'test_precision': test_precision,
        'test_recall': test_recall,
        'test_f1': test_f1,
        'confusion_matrix': cm,
        'feature_importance': feature_importance
    }

# ============================================================================
# Model Saving
# ============================================================================

def save_model(model, scaler, model_path, scaler_path):
    """Save model and scaler to disk"""
    print(f"\n💾 Saving model and scaler...")
    
    # Create directory if needed
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(scaler_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"  ✅ Model saved: {model_path}")
    
    # Save scaler
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"  ✅ Scaler saved: {scaler_path}")

def load_model(model_path, scaler_path):
    """Load model and scaler from disk"""
    print(f"\n📂 Loading model and scaler...")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print(f"  ✅ Model loaded: {model_path}")
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    print(f"  ✅ Scaler loaded: {scaler_path}")
    
    return model, scaler

# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    """Main training pipeline"""
    print(f"\n{'='*60}")
    print(f"🚀 Phishing URL Detection - Model Training")
    print(f"{'='*60}")
    
    try:
        # 1. Load dataset
        df = load_dataset(CONFIG['dataset_path'])
        
        # 2. Find label column
        label_col = find_label_column(df)
        
        # 3. Handle missing values
        df = handle_missing_values(df)
        
        # 4. Separate features and labels
        X, y = separate_features_labels(df, label_col)
        
        # 5. Split data
        X_train, X_test, y_train, y_test = split_data(
            X, y,
            test_size=CONFIG['test_size'],
            random_state=CONFIG['random_state']
        )
        
        # 6. Scale features
        X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
        
        # 7. Train model
        model = train_model(X_train_scaled, y_train)
        
        # 8. Evaluate model
        metrics = evaluate_model(
            model, X_train_scaled, X_test_scaled,
            y_train, y_test,
            feature_names=X.columns.tolist()
        )
        
        # 9. Save model and scaler
        save_model(
            model, scaler,
            CONFIG['model_output'],
            CONFIG['scaler_output']
        )
        
        print(f"\n{'='*60}")
        print(f"✅ Training completed successfully!")
        print(f"{'='*60}")
        print(f"\nModel Information:")
        print(f"  Model: {CONFIG['model_output']}")
        print(f"  Scaler: {CONFIG['scaler_output']}")
        print(f"  Features: {len(X.columns)}")
        print(f"  Classes: {len(np.unique(y))}")
        print(f"  Test Accuracy: {metrics['test_accuracy']:.4f}")
        print(f"\nUsage:")
        print(f"  from train_model import load_model")
        print(f"  model, scaler = load_model('{CONFIG['model_output']}', '{CONFIG['scaler_output']}')")
        print(f"  predictions = model.predict(scaler.transform(X_new))")
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
