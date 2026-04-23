# -*- coding: utf-8 -*-
import os
import sys
import io

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import torch
import numpy as np
import pickle
import re
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from flask_cors import CORS

# SHAP explainability
try:
    import shap
    SHAP_AVAILABLE = True
    print("✅ SHAP library imported successfully")
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️ SHAP not installed. Install with: pip install shap")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Model loading
model = None
tokenizer = None
explainer = None  # SHAP explainer (cached)

# Phishing URL model
rf_model = None
rf_scaler = None

def load_rf_model():
    """Load the trained RandomForest phishing URL model"""
    global rf_model, rf_scaler
    
    try:
        # Get absolute path to model files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'phishing_model.pkl')
        scaler_path = os.path.join(script_dir, 'scaler.pkl')
        
        # Load model and scaler
        with open(model_path, 'rb') as f:
            rf_model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            rf_scaler = pickle.load(f)
        
        print("✅ RandomForest phishing URL model loaded")
        return True
    except FileNotFoundError as e:
        print(f"⚠️ Phishing URL model not found: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error loading phishing model: {e}")
        return False

def load_model():
    """Load the trained scam detection model"""
    global model, tokenizer
    
    try:
        model_path = os.path.join(os.path.dirname(__file__), 'pbl', 'scam_model')
        
        print(f"📁 Looking for trained model at: {model_path}")
        
        if os.path.exists(model_path):
            try:
                # Load trained BERT model and tokenizer
                from transformers import BertTokenizer, BertForSequenceClassification
                
                print(f"🤖 Loading trained model from {model_path}...")
                model = BertForSequenceClassification.from_pretrained(model_path)
                tokenizer = BertTokenizer.from_pretrained(model_path)
                
                # Set to eval mode
                model.eval()
                
                print(f"✅ Successfully loaded trained model from {model_path}")
                print(f"✅ Model device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
                
            except Exception as e:
                print(f"⚠️ Error loading trained model: {e}")
                print("⚠️ Loading pre-trained model from Hugging Face...")
                _load_pretrained_model()
        else:
            print(f"ℹ️ Trained model not found at: {model_path}")
            print("📦 Loading pre-trained BERT model from Hugging Face...")
            _load_pretrained_model()
            
    except Exception as e:
        print(f"❌ Error in load_model: {e}")
        _load_pretrained_model()

def _load_pretrained_model():
    """Load pre-trained BERT model from Hugging Face"""
    global model, tokenizer
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        model_name = 'bert-base-uncased'
        print(f"🌐 Loading {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)
        model.eval()
        print(f"✅ Successfully loaded pre-trained {model_name}")
    except Exception as e2:
        print(f"❌ Failed to load pre-trained model: {e2}")
        print("⚠️ Will use pattern-based detection instead")

def create_prediction_function():
    """Create a wrapper function for SHAP explainer"""
    def predict_fn(texts):
        """Prediction function that takes list of texts and returns probabilities"""
        try:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            predictions_list = []
            
            for text in texts:
                if isinstance(text, np.ndarray):
                    text = str(text)
                
                # Tokenize
                inputs = tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True
                ).to(device)
                
                # Get predictions
                with torch.no_grad():
                    outputs = model(**inputs)
                    logits = outputs.logits
                    probs = torch.nn.functional.softmax(logits, dim=1)
                    predictions_list.append(probs[0].cpu().numpy())
            
            return np.array(predictions_list)
        except Exception as e:
            print(f"Error in predict_fn: {e}")
            return np.array([[0.33, 0.33, 0.33]] * len(texts))
    
    return predict_fn

def explain_prediction(text, top_k=10):
    """
    Explain prediction using SHAP values
    Returns JSON with word importance scores
    """
    global explainer
    
    if not SHAP_AVAILABLE or model is None or tokenizer is None:
        print("⚠️ SHAP not available or model not loaded")
        return {
            'word_importance': [],
            'message': 'SHAP explainability not available'
        }
    
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Get base prediction
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)
            pred_class = probs.argmax().item()
        
        # Get tokens for this text
        tokens = tokenizer.tokenize(text)
        
        # Simple word importance based on model attention
        # Using attention weights instead of SHAP for faster, more reliable results
        print("🔄 Computing word importance from model...")
        
        # Get model outputs with attention
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs, output_attentions=True)
            logits = outputs.logits
            
            # Get attention weights from last layer
            attention_weights = outputs.attentions[-1]  # Shape: (batch_size, num_heads, seq_len, seq_len)
            
            # Average over batch and heads, focus on prediction token
            attention = attention_weights[0].mean(dim=0)  # Average over heads
            
            # Get importance scores from attention
            prediction_attention = attention[-1]  # Attention to last token (prediction)
            
            # Map to tokens
            word_importance = []
            
            for idx, token in enumerate(tokens):
                if token not in ['[CLS]', '[SEP]', '[PAD]'] and idx < len(prediction_attention):
                    # Convert attention weight to impact score
                    attention_score = float(prediction_attention[idx].cpu().numpy())
                    
                    # Scale to -1 to 1 range based on prediction class
                    if pred_class == 0:  # not_a_scam
                        impact = -attention_score
                    elif pred_class == 2:  # scam
                        impact = attention_score
                    else:  # suspicious
                        impact = attention_score * 0.5
                    
                    word_importance.append({
                        'word': token.replace('##', ''),  # Remove BERT subword markers
                        'impact': impact
                    })
        
        # Sort by absolute impact and get top K
        if word_importance:
            word_importance.sort(key=lambda x: abs(x['impact']), reverse=True)
            top_words = word_importance[:min(top_k, len(word_importance))]
        else:
            top_words = []
        
        return {
            'word_importance': top_words,
            'total_words_analyzed': len(tokens),
            'method': 'attention_based'
        }
        
    except Exception as e:
        print(f"❌ Error in explain_prediction: {e}")
        import traceback
        traceback.print_exc()
        return {
            'word_importance': [],
            'message': f'Explainability error: {str(e)}'
        }

def extract_urls_from_text(text):
    """
    Extract URLs from text using regex
    Returns list of URLs
    """
    # URL regex pattern
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates

def calculate_url_features(url):
    """
    Extract URL features for phishing detection
    Returns dict with features needed by the RF model
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
        
        # Count secure/verify keywords (too many together is suspicious)
        secure_keywords_found = sum(1 for kw in secure_keywords if kw in domain or kw in path)
        
        # Calculate URLSimilarityIndex (100 = legit-looking, lower = more suspicious)
        # If domain has multiple hyphens or seems to be impersonating, reduce similarity
        url_similarity = 100
        
        # Reduce similarity if mixing real keywords with secure keywords
        if impersonation_score > 0 and secure_keywords_found > 0:
            url_similarity = max(20, 100 - (impersonation_score * 15) - (secure_keywords_found * 10))
        elif secure_keywords_found > 2:  # Too many secure keywords
            url_similarity = max(30, 100 - (secure_keywords_found * 15))
        elif domain.count('-') > 2:  # Too many hyphens
            url_similarity = max(40, 100 - (domain.count('-') * 10))
        elif has_ip:  # IP address
            url_similarity = 20
        elif not has_https:  # No HTTPS
            url_similarity = max(60, url_similarity - 20)
        
        # Detect form submission and suspicious parameters
        has_form_params = 1 if any(p in full_url_lower for p in ['email', 'password', 'user', 'login', 'account', 'card', 'ssn', 'token']) else 0
        
        # Entropy
        entropy = 0
        if url:
            from collections import Counter
            freq = Counter(url)
            entropy = -sum((count / len(url)) * np.log2(count / len(url)) for count in freq.values())
        
        # Features for the model
        features = {
            'URLLength': url_length,
            'DomainLength': domain_length,
            'IsDomainIP': has_ip,
            'URLSimilarityIndex': url_similarity,  # Now dynamically calculated
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
            'DomainTitleMatchScore': 50 if impersonation_score > 0 else 100,  # Lower if impersonating
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
            'Bank': bank_in_domain,  # Now detecting "bank" keyword
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
        print(f"Error extracting URL features: {e}")
        return None

def predict_phishing_url(url):
    """
    Predict if a URL is phishing using the RandomForest model
    Returns prediction result
    """
    # Whitelist of known legitimate domains
    whitelist_domains = [
        'chatgpt.com', 'openai.com', 'gmail.com', 'google.com', 'facebook.com',
        'twitter.com', 'linkedin.com', 'github.com', 'stackoverflow.com', 'youtube.com',
        'amazon.com', 'ebay.com', 'paypal.com', 'apple.com', 'microsoft.com',
        'netflix.com', 'instagram.com', 'telegram.org', 'whatsapp.com', 'discord.com',
        'reddit.com', 'wikipedia.org', 'quora.com', 'medium.com', 'dev.to',
        'cloudflare.com', 'aws.amazon.com', 'azure.microsoft.com', 'heroku.com',
        'digitalocean.com', 'vercel.com', 'netlify.com', 'stripe.com', 'twilio.com',
        'auth0.com', 'okta.com', 'slack.com', 'zoom.us', 'teams.microsoft.com'
    ]
    
    try:
        # Extract domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        
        # Check if domain is in whitelist
        if domain in whitelist_domains:
            return {
                'url': url,
                'classification': 'legitimate',
                'confidence': 0.99,
                'probabilities': {
                    'phishing': 0.01,
                    'legitimate': 0.99
                },
                'available': True,
                'reason': 'Verified legitimate domain'
            }
    except:
        pass
    
    # If model not available, use heuristic approach
    if rf_model is None or rf_scaler is None:
        return {
            'error': 'Model not loaded',
            'classification': 'unknown',
            'available': False
        }
    
    try:
        # Extract features
        features = calculate_url_features(url)
        if features is None:
            return {'error': 'Could not extract features', 'classification': 'unknown'}
        
        # Convert to DataFrame with correct feature order
        import pandas as pd
        feature_names = ['URLLength', 'DomainLength', 'IsDomainIP', 'URLSimilarityIndex', 
                        'CharContinuationRate', 'TLDLegitimateProb', 'URLCharProb', 'TLDLength', 
                        'NoOfSubDomain', 'HasObfuscation', 'NoOfObfuscatedChar', 'ObfuscationRatio', 
                        'NoOfLettersInURL', 'LetterRatioInURL', 'NoOfDegitsInURL', 'DegitRatioInURL', 
                        'NoOfEqualsInURL', 'NoOfQMarkInURL', 'NoOfAmpersandInURL', 
                        'NoOfOtherSpecialCharsInURL', 'SpacialCharRatioInURL', 'IsHTTPS', 'LineOfCode', 
                        'LargestLineLength', 'HasTitle', 'DomainTitleMatchScore', 'URLTitleMatchScore', 
                        'HasFavicon', 'Robots', 'IsResponsive', 'NoOfURLRedirect', 'NoOfSelfRedirect', 
                        'HasDescription', 'NoOfPopup', 'NoOfiFrame', 'HasExternalFormSubmit', 
                        'HasSocialNet', 'HasSubmitButton', 'HasHiddenFields', 'HasPasswordField', 
                        'Bank', 'Pay', 'Crypto', 'HasCopyrightInfo', 'NoOfImage', 'NoOfCSS', 'NoOfJS', 
                        'NoOfSelfRef', 'NoOfEmptyRef', 'NoOfExternalRef']
        
        # Only use features that exist in the trained model
        feature_data = {name: [features.get(name, 0)] for name in feature_names}
        df = pd.DataFrame(feature_data)
        
        # Scale features
        scaled = rf_scaler.transform(df)
        
        # Make prediction
        pred = rf_model.predict(scaled)[0]
        probs = rf_model.predict_proba(scaled)[0]
        
        # Label mapping: 0 = PHISHING, 1 = LEGITIMATE
        return {
            'url': url,
            'prediction': int(pred),
            'classification': 'phishing' if pred == 0 else 'legitimate',
            'confidence': float(max(probs)),
            'probabilities': {
                'phishing': float(probs[0]),      # prob of class 0
                'legitimate': float(probs[1])     # prob of class 1
            },
            'available': True,
            'features': features  # Include features for explanation
        }
    except Exception as e:
        print(f"Error predicting phishing: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'classification': 'unknown'}

def get_url_explanation(url):
    """
    Generate human-readable explanation for URL phishing classification
    Shows which features triggered the phishing alert
    """
    try:
        prediction = predict_phishing_url(url)
        if 'error' in prediction:
            return {'error': prediction['error']}
        
        features = prediction.get('features', {})
        features_copy = dict(features)
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Identify red flags
        red_flags = []
        green_flags = []
        
        # Security flags
        if not url.startswith('https'):
            red_flags.append({
                'flag': '🚨 Not HTTPS',
                'reason': 'URL uses HTTP instead of secure HTTPS'
            })
        else:
            green_flags.append({
                'flag': '✓ HTTPS Used',
                'reason': 'URL uses secure HTTPS connection'
            })
        
        # Domain analysis
        if features_copy.get('URLSimilarityIndex', 100) < 60:
            red_flags.append({
                'flag': f'🚨 Low Domain Similarity ({features_copy.get("URLSimilarityIndex", 100):.0f}/100)',
                'reason': 'Domain name looks suspicious or impersonates legitimate brand'
            })
        elif features_copy.get('URLSimilarityIndex', 100) >= 100:
            green_flags.append({
                'flag': '✓ Legitimate Domain',
                'reason': 'Domain name pattern looks legitimate'
            })
        
        # Bank/Financial keywords
        if features_copy.get('Bank') == 1:
            red_flags.append({
                'flag': '🚨 Bank Keyword Detected',
                'reason': f'Domain contains "bank" keyword: {domain}'
            })
        
        if features_copy.get('Pay') == 1:
            red_flags.append({
                'flag': '🚨 Payment Keyword Detected',
                'reason': f'Domain mimics payment service: {domain}'
            })
        
        # Suspicious parameters
        if features_copy.get('NoOfEqualsInURL', 0) > 0 or features_copy.get('NoOfQMarkInURL', 0) > 0:
            params = parsed.query.lower()
            if any(kw in params for kw in ['user', 'account', 'id', 'email', 'login']):
                red_flags.append({
                    'flag': '🚨 Suspicious Query Parameters',
                    'reason': 'URL contains parameters requesting user/account info'
                })
        
        # Obfuscation
        if features_copy.get('NoOfObfuscatedChar', 0) > 2:
            red_flags.append({
                'flag': f'🚨 Multiple Hyphens ({features_copy.get("NoOfObfuscatedChar", 0)} found)',
                'reason': 'Excessive hyphens in domain often indicate phishing'
            })
        
        # Special character indicators
        if features_copy.get('HasPasswordField') == 1:
            red_flags.append({
                'flag': '🚨 Password Field Detected',
                'reason': 'URL suggests password change/update request'
            })
        
        # IP address
        if features_copy.get('IsDomainIP') == 1:
            red_flags.append({
                'flag': '🚨 IP Address Used',
                'reason': 'URL uses IP address instead of domain name'
            })
        
        # Legitimate indicators
        if features_copy.get('TLDLegitimateProb', 0) > 0.8:
            green_flags.append({
                'flag': '✓ Standard TLD',
                'reason': f'Uses standard TLD: {domain.split(".")[-1]}'
            })
        
        if features_copy.get('NoOfSubDomain', 0) >= 1:
            green_flags.append({
                'flag': f'✓ Subdomain Structure',
                'reason': f'Uses proper subdomain structure: {domain}'
            })
        
        return {
            'url': url,
            'classification': prediction['classification'],
            'confidence': prediction['confidence'],
            'red_flags': red_flags,
            'green_flags': green_flags,
            'feature_details': {
                'URLSimilarityIndex': features_copy.get('URLSimilarityIndex', 0),
                'ContainsBankKeyword': bool(features_copy.get('Bank')),
                'IsHTTPS': bool(features_copy.get('IsHTTPS')),
                'HasObfuscation': bool(features_copy.get('HasObfuscation')),
                'DomainLength': features_copy.get('DomainLength', 0),
                'URLLength': features_copy.get('URLLength', 0)
            }
        }
    except Exception as e:
        print(f"Error getting URL explanation: {e}")
        import traceback
        traceback.print_exc()

def extract_insights_from_text(text):
    """Extract specific indicators that suggest scam/suspicious behavior"""
    text_lower = text.lower()
    insights = []
    
    # Urgency indicators
    urgency_keywords = ['urgent', 'immediately', 'act now', 'asap', 'limited time', 'expire', 'don\'t wait', 'hurry', 'right away']
    urgency_found = [kw for kw in urgency_keywords if kw in text_lower]
    if urgency_found:
        insights.append(f"🚨 High urgency language detected: {', '.join(urgency_found)}")
    
    # Money-related keywords
    money_keywords = ['wire', 'transfer', 'payment', 'bitcoin', 'crypto', 'refund', 'claim', 'won', 'prize', 'reward', 'cashback', 'credit']
    money_found = [kw for kw in money_keywords if kw in text_lower]
    if money_found:
        insights.append(f"💰 Financial keywords detected: {', '.join(set(money_found))}")
    
    # Personal info requests
    personal_keywords = ['verify', 'confirm', 'password', 'ssn', 'credit card', 'bank details', 'otp', 'pin', 'account number']
    personal_found = [kw for kw in personal_keywords if kw in text_lower]
    if personal_found:
        insights.append(f"🔐 Personal info request detected: {', '.join(set(personal_found))}")
    
    # Impersonation indicators
    impersonation_keywords = ['paypal', 'amazon', 'apple', 'microsoft', 'bank', 'irs', 'government', 'police']
    impersonation_found = [kw for kw in impersonation_keywords if kw in text_lower]
    if impersonation_found:
        insights.append(f"👤 Potential impersonation: {', '.join(set(impersonation_found))}")
    
    # Shortened URLs
    url_patterns = ['bit.ly', 'tinyurl', 'goo.gl', 'short.link', 'ow.ly']
    urls_found = [pattern for pattern in url_patterns if pattern in text_lower]
    if urls_found:
        insights.append(f"🔗 Suspicious shortened URLs detected: {', '.join(urls_found)}")
    
    # Spelling errors (common in phishing)
    common_misspellings = ['recieve', 'occured', 'untill', 'sincerely', 'adminstration']
    spelling_found = [word for word in common_misspellings if word in text_lower]
    if spelling_found:
        insights.append(f"✏️ Suspicious spelling errors: {', '.join(spelling_found)}")
    
    # Action-oriented suspicious phrases
    action_phrases = ['click here', 'download', 'install', 'enable location', 'allow access']
    actions_found = [phrase for phrase in action_phrases if phrase in text_lower]
    if actions_found:
        insights.append(f"⚡ Suspicious action requests: {', '.join(actions_found)}")
    
    return insights

def analyze_text_with_model(text):
    """Analyze text using the trained model with detailed insights"""
    if model is not None and tokenizer is not None:
        try:
            # Tokenize input
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
            model.to(device)
            
            # Get predictions
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = outputs.logits.softmax(dim=1)
            
            # Get the predicted class and all probabilities
            predicted_class = predictions.argmax().item()
            confidence = predictions[0][predicted_class].item()
            
            class_names = ['not_a_scam', 'suspicious', 'scam']
            classification = class_names[predicted_class]
            
            # Extract pattern-based indicators
            pattern_insights = extract_insights_from_text(text)
            
            # Build insights list
            insights = [
                f"🤖 Model Confidence: {confidence*100:.1f}%"
            ]
            
            # Add pattern insights
            if pattern_insights:
                insights.extend(pattern_insights)
            else:
                insights.append("✓ No suspicious patterns detected")
            
            return {
                'classification': classification,
                'confidence': float(confidence),
                'scam_score': float(confidence) if classification == 'scam' else 1 - float(confidence),
                'insights': insights,
                'probabilities': {
                    'safe': float(predictions[0][0].item()),
                    'suspicious': float(predictions[0][1].item()),
                    'scam': float(predictions[0][2].item())
                }
            }
        except Exception as e:
            print(f"Model inference error: {e}")
            return analyze_text_with_patterns(text)
    else:
        print("⚠️ No model loaded, using pattern-based detection")
        return analyze_text_with_patterns(text)

def analyze_text_with_patterns(text):
    """Fallback: Analyze text using pattern matching"""
    text_lower = text.lower()
    
    scam_keywords = {
        'urgent': ['urgent', 'immediately', 'act now', 'limited time', 'expire'],
        'money': ['wire', 'transfer', 'payment', 'bitcoin', 'crypto', 'refund'],
        'personal_info': ['verify', 'confirm', 'password', 'ssn', 'credit card'],
        'pressure': ['urgent', 'immediate', 'asap', 'don\'t wait', 'hurry'],
        'impersonation': ['paypal', 'amazon', 'apple', 'microsoft', 'bank', 'irs'],
        'promises': ['guarantee', 'prize', 'won', 'claim', 'free money', 'rich quick']
    }
    
    insights = []
    scam_score = 0
    max_score = 0
    
    for category, keywords in scam_keywords.items():
        max_score += len(keywords)
        for keyword in keywords:
            if keyword in text_lower:
                scam_score += 1
                insights.append(f"Contains '{keyword}' - common in {category.replace('_', ' ')}")
    
    # Check for shortened URLs
    for link_pattern in ['bit.ly', 'tinyurl', 'goo.gl', 'short.link']:
        if link_pattern in text_lower:
            scam_score += 1
            insights.append(f"Contains suspicious shortened URL: {link_pattern}")
    
    # Check for spelling errors
    common_misspellings = ['recieve', 'occured', 'untill', 'sincerely']
    for misspelling in common_misspellings:
        if misspelling in text_lower:
            scam_score += 0.5
            insights.append(f"Contains common misspelling: '{misspelling}'")
    
    if len(text) > 0:
        text_length_factor = min(len(text) / 500, 1)
        probability = (scam_score / max(max_score, 1)) if max_score > 0 else 0
        probability = max(0, min(probability - (text_length_factor * 0.2), 1))
    else:
        probability = 0
    
    if probability >= 0.7:
        classification = "scam"
        confidence = min(probability * 1.3, 1.0)
        probs = {'safe': 0.0, 'suspicious': 0.1, 'scam': confidence}
    elif probability >= 0.4:
        classification = "suspicious"
        confidence = probability
        probs = {'safe': 0.2, 'suspicious': confidence, 'scam': 0.1}
    else:
        classification = "not_a_scam"
        confidence = 1 - probability
        probs = {'safe': confidence, 'suspicious': 0.0, 'scam': 0.0}
    
    # Normalize probabilities to sum to 1
    total = sum(probs.values())
    probs = {k: v/total for k, v in probs.items()}
    
    return {
        'classification': classification,
        'confidence': float(confidence),
        'scam_score': float(probability),
        'insights': insights[:5],
        'probabilities': {
            'safe': float(probs['safe']),
            'suspicious': float(probs['suspicious']),
            'scam': float(probs['scam'])
        }
    }

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    model_status = "loaded" if model is not None else "not_loaded (using patterns)"
    return jsonify({
        'status': 'healthy',
        'message': 'Backend ML API is running',
        'model': model_status
    }), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict if text is a scam"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing text field',
                'message': 'Please provide text to analyze'
            }), 400
        
        text = data['text'].strip()
        
        if len(text) == 0:
            return jsonify({
                'error': 'Empty text',
                'message': 'Please enter some text to analyze'
            }), 400
        
        if len(text) > 10000:
            return jsonify({
                'error': 'Text too long',
                'message': 'Text must be less than 10000 characters'
            }), 400
        
        # Analyze the text
        result = analyze_text_with_model(text)
        
        return jsonify({
            'success': True,
            'prediction': result,
            'text': text[:200] + '...' if len(text) > 200 else text
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e)
        }), 500

@app.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    """Predict multiple texts"""
    try:
        data = request.get_json()
        
        if not data or 'texts' not in data:
            return jsonify({
                'error': 'Missing texts field',
                'message': 'Please provide texts to analyze'
            }), 400
        
        texts = data['texts']
        
        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({
                'error': 'Invalid texts format',
                'message': 'Please provide a non-empty list of texts'
            }), 400
        
        results = []
        for text in texts[:10]:
            if text.strip():
                result = analyze_text_with_model(text)
                results.append({
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'prediction': result
                })
        
        return jsonify({
            'success': True,
            'predictions': results,
            'count': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Batch prediction failed',
            'message': str(e)
        }), 500

@app.route('/api/explain', methods=['POST'])
def explain():
    """Explain prediction using SHAP values"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing text field',
                'message': 'Please provide text to explain'
            }), 400
        
        text = data['text'].strip()
        top_k = data.get('top_k', 10)
        
        if len(text) == 0:
            return jsonify({
                'error': 'Empty text',
                'message': 'Please enter some text to analyze'
            }), 400
        
        if len(text) > 1000:
            return jsonify({
                'error': 'Text too long',
                'message': 'For explainability, text must be less than 1000 characters'
            }), 400
        
        if not SHAP_AVAILABLE:
            return jsonify({
                'error': 'SHAP not available',
                'message': 'Please install SHAP: pip install shap',
                'fallback': 'Use pattern-based insights instead'
            }), 503
        
        # Get prediction first
        prediction_result = analyze_text_with_model(text)
        
        # Get SHAP explanation
        print(f"🔍 Generating SHAP explanation for: {text[:50]}...")
        shap_explanation = explain_prediction(text, top_k=top_k)
        
        return jsonify({
            'success': True,
            'text': text,
            'prediction': prediction_result,
            'explanation': shap_explanation
        }), 200
    
    except Exception as e:
        print(f"❌ Explain endpoint error: {e}")
        return jsonify({
            'error': 'Explanation failed',
            'message': str(e)
        }), 500

@app.route('/api/combined-analysis', methods=['POST'])
def combined_analysis():
    """
    Combined analysis: Text scam detection + URL phishing detection
    
    Request JSON:
    {
        "text": "Check this link: https://example.com"
    }
    
    Returns:
    {
        "text_analysis": { ... },
        "url_analysis": { ... },
        "risk_level": "HIGH|MEDIUM|LOW",
        "summary": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing text field',
                'message': 'Please provide text to analyze'
            }), 400
        
        text = data['text'].strip()
        
        if len(text) == 0:
            return jsonify({
                'error': 'Empty text',
                'message': 'Please enter some text to analyze'
            }), 400
        
        if len(text) > 10000:
            return jsonify({
                'error': 'Text too long',
                'message': 'Text must be less than 10000 characters'
            }), 400
        
        # 1. Always analyze text for scams
        print(f"🔍 Analyzing text...")
        text_result = analyze_text_with_model(text)
        
        # 2. Extract URLs from text
        print(f"🔗 Extracting URLs...")
        urls = extract_urls_from_text(text)
        
        # 3. Analyze URLs if any found
        url_results = []
        if urls:
            print(f"🚨 Found {len(urls)} URL(s)")
            for url in urls:
                url_pred = predict_phishing_url(url)
                # Add explanation to URL result
                url_explanation = get_url_explanation(url)
                url_pred['explanation'] = {
                    'red_flags': url_explanation.get('red_flags', []),
                    'green_flags': url_explanation.get('green_flags', []),
                    'features': url_explanation.get('feature_details', {})
                }
                url_results.append(url_pred)
        else:
            print(f"ℹ️ No URLs found in text")
        
        # 4. Determine risk level based on both models
        text_is_scam = text_result['classification'] in ['scam', 'suspicious']
        url_is_phishing = any(u.get('classification') == 'phishing' for u in url_results)
        
        if text_is_scam and url_is_phishing:
            risk_level = "HIGH"
            risk_description = "🚨 HIGH RISK: Both text and URL are suspicious"
        elif text_is_scam or url_is_phishing:
            risk_level = "MEDIUM"
            risk_description = "⚠️ MEDIUM RISK: Either text or URL is suspicious"
        else:
            risk_level = "LOW"
            risk_description = "✓ LOW RISK: Both text and URLs appear safe"
        
        # Build comprehensive response
        response = {
            'success': True,
            'text_analysis': {
                'classification': text_result['classification'],
                'confidence': text_result['confidence'],
                'insights': text_result['insights'][:3],  # Top 3 insights
                'probabilities': text_result['probabilities']
            },
            'url_analysis': {
                'urls_found': len(urls),
                'urls': url_results
            },
            'risk_assessment': {
                'risk_level': risk_level,
                'description': risk_description,
                'factors': {
                    'text_suspicious': text_is_scam,
                    'any_url_phishing': url_is_phishing
                }
            },
            'summary': {
                'text_classification': text_result['classification'],
                'url_count': len(urls),
                'phishing_urls': len([u for u in url_results if u.get('classification') == 'phishing']),
                'overall_risk': risk_level
            }
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"❌ Combined analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    load_model()
    load_rf_model()
    print("\n" + "="*60)
    print("🤖 Backend ML API Starting")
    print("="*60)
    print("📍 Running on: http://0.0.0.0:5001")
    print("🔗 Health check: http://localhost:5001/api/health")
    print("🔗 Combined analysis: http://localhost:5001/api/combined-analysis")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
