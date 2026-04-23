# Backend ML - Scam Detection Model Server

Flask API server for the trained scam detection model using BERT and transformers.

## 📁 Folder Structure

```
backend_ml/
├── app.py                          # Flask API server
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── pbl/
    ├── scam_model/                # Pre-trained model files
    │   ├── model.pkl              # Trained model
    │   └── tokenizer.pkl          # Tokenizer
    ├── scam_dataset_3class_1000.csv   # Training dataset
    ├── scam_detection_bert.py      # Model training script
    └── test_model.py               # Testing script
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend_ml
pip install -r requirements.txt
```

**Note:** First time installation may take 5-10 minutes due to torch and transformers size.

### 2. Start the Server

```bash
python app.py
```

Server will run on: `http://localhost:5001`

### 3. Verify It's Working

```bash
curl http://localhost:5001/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Backend ML API is running",
  "model": "loaded"
}
```

---

## 🔌 API Endpoints

### 1. Single Text Prediction

**Endpoint:** `POST /api/predict`

**Request:**
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Click here urgently to verify your account!"}'
```

**Response:**
```json
{
  "success": true,
  "prediction": {
    "classification": "scam",
    "confidence": 0.92,
    "scam_score": 0.85,
    "insights": [
      "Contains 'click' - common in phishing",
      "Contains 'urgently' - pressure tactic",
      "Model prediction: scam (92%)"
    ]
  },
  "text": "Click here urgently to verify your account!"
}
```

---

### 2. Batch Predictions

**Endpoint:** `POST /api/batch-predict`

Analyze multiple texts at once.

```bash
curl -X POST http://localhost:5001/api/batch-predict \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Text 1",
      "Text 2",
      "Text 3"
    ]
  }'
```

---

### 3. Health Check

**Endpoint:** `GET /api/health`

```bash
curl http://localhost:5001/api/health
```

---

## 📊 Classification Labels

The model classifies text into 3 categories:

| Classification | Meaning | Confidence |
|---|---|---|
| `scam` | Clear scam indicators detected | ≥ 70% |
| `suspicious` | Some suspicious indicators | 40-69% |
| `not_a_scam` | Appears legitimate | < 40% |

---

## 🤖 Model Information

### Architecture
- **Base Model:** BERT (Bidirectional Encoder Representations from Transformers)
- **Task:** Text Classification (3 classes)
- **Framework:** Transformers (Hugging Face)

### Training Data
- **Dataset:** `scam_dataset_3class_1000.csv`
- **Classes:** 3 (scam, suspicious, legitimate)
- **Sample Size:** 1000 examples

### Model Files Location
```
pbl/scam_model/
├── model.pkl           # Trained BERT model
└── tokenizer.pkl       # Tokenizer for preprocessing
```

---

## 🔄 Model Loading

The app tries to load models in this order:

1. **Pre-trained model** from `pbl/scam_model/`
   - Looks for `model.pkl` and `tokenizer.pkl`
2. **BERT from Hugging Face** as fallback
   - Uses `bert-base-uncased` for demonstration
3. **Pattern-based detection** as final fallback
   - Uses keyword matching if no ML model loaded

---

## 🛠️ Training Your Own Model

To train a new model with your dataset:

```bash
cd pbl
python scam_detection_bert.py --dataset scam_dataset_3class_1000.csv
```

This will:
- Load the dataset
- Train the BERT model
- Save model and tokenizer to `scam_model/`
- Generate performance metrics

---

## 🧪 Testing the Model

Run the test script:

```bash
cd pbl
python test_model.py
```

This will:
- Load the trained model
- Test with sample texts
- Display predictions and confidence scores
- Show performance metrics

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (optional):

```
FLASK_ENV=development
FLASK_DEBUG=True
MODEL_PATH=./pbl/scam_model
```

### Port Configuration

To change the port (default: 5001):

Edit `app.py` last line:
```python
app.run(debug=True, host='0.0.0.0', port=5002)  # Change 5001 to 5002
```

---

## 📈 Performance

- **Response Time:** 200-500ms per prediction
- **Batch Processing:** 1-2 seconds for 10 texts
- **Memory Usage:** ~2-3 GB (BERT model)
- **GPU Support:** Yes, if CUDA available

---

## 🔍 Debugging

### Check if server is running:
```bash
curl http://localhost:5001/api/health
```

### View server logs:
```
Check terminal output for real-time logs
```

### Test API with Postman:
1. Import collection from frontend docs
2. Set URL to: `http://localhost:5001/api/predict`
3. Body: `{"text": "your text here"}`

---

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## 📋 Requirements Details

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 2.3.0 | Web framework |
| Flask-CORS | 4.0.0 | Cross-origin requests |
| torch | 2.0.0 | Deep learning |
| transformers | 4.30.0 | BERT models |
| numpy | 1.24.0 | Numerical computing |
| pandas | 2.0.0 | Data manipulation |
| scikit-learn | 1.2.0 | Machine learning |

---

## 🐛 Troubleshooting

### Port 5001 already in use
```bash
# Find and kill process
lsof -i :5001
kill -9 <PID>

# Or change port in app.py
```

### Module not found errors
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

### CUDA/GPU errors
- GPU support is optional
- Model will run on CPU if GPU not available
- Install `torch[cuda]` separately if needed

### Memory issues
- BERT model uses ~2-3 GB RAM
- Use CPU mode for low-memory systems
- Consider using smaller models (DistilBERT)

---

## 📚 Learn More

- **BERT Paper:** https://arxiv.org/abs/1810.04805
- **Hugging Face:** https://huggingface.co/
- **Transformers Library:** https://github.com/huggingface/transformers
- **Flask Docs:** https://flask.palletsprojects.com/

---

## 📊 API Response Examples

### Scam Example
```json
{
  "success": true,
  "prediction": {
    "classification": "scam",
    "confidence": 0.95,
    "scam_score": 0.85,
    "insights": [
      "Contains 'wire' - money transfer request",
      "Contains 'urgently' - pressure tactic",
      "Contains 'verify' - phishing pattern",
      "Model prediction: scam (95%)"
    ]
  }
}
```

### Suspicious Example
```json
{
  "success": true,
  "prediction": {
    "classification": "suspicious",
    "confidence": 0.65,
    "scam_score": 0.55,
    "insights": [
      "Contains 'verify' - verification request",
      "Model prediction: suspicious (65%)"
    ]
  }
}
```

### Legitimate Example
```json
{
  "success": true,
  "prediction": {
    "classification": "not_a_scam",
    "confidence": 0.95,
    "scam_score": 0.05,
    "insights": []
  }
}
```

---

## 🔐 Security Notes

1. **Rate limiting:** Implement in production
2. **Input validation:** Currently limited to 10,000 characters
3. **CORS:** Currently allows all origins (restrict in production)
4. **Logging:** Add request logging for audit trail

---

## 📞 Support

If you encounter issues:

1. Check `pbl/results/` folder for training logs
2. Review `test_model.py` output for model diagnostics
3. Check Flask app logs in terminal
4. Verify `scam_model/` files exist and are readable

---

**Backend ML API v1.0 - Ready for Production**

Last Updated: April 16, 2026
