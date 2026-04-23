const mongoose = require('mongoose');

const searchHistorySchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  text: {
    type: String,
    required: true,
    maxlength: 10000
  },
  classification: {
    type: String,
    enum: ['not_a_scam', 'suspicious', 'scam'],
    required: true
  },
  confidence: {
    type: Number,
    required: true
  },
  insights: [{
    type: String
  }],
  probabilities: {
    safe: Number,
    suspicious: Number,
    scam: Number
  },
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  }
});

// Index for efficient querying by userId and sorting by date
searchHistorySchema.index({ userId: 1, createdAt: -1 });

module.exports = mongoose.model('SearchHistory', searchHistorySchema);
