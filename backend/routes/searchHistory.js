const express = require('express');
const SearchHistory = require('../models/SearchHistory');
const auth = require('../middleware/auth');

const router = express.Router();

// @route   POST /api/search-history
// @desc    Save a new search to history
// @access  Private
router.post('/', auth, async (req, res) => {
  try {
    const { text, classification, confidence, insights, probabilities } = req.body;

    // Validation
    if (!text || !classification || confidence === undefined) {
      return res.status(400).json({ 
        message: 'Please provide text, classification, and confidence' 
      });
    }

    // Create new search history entry
    const searchHistory = new SearchHistory({
      userId: req.userId,
      text,
      classification,
      confidence,
      insights: insights || [],
      probabilities: probabilities || {}
    });

    await searchHistory.save();

    res.status(201).json({
      success: true,
      message: 'Search saved to history',
      data: searchHistory
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// @route   GET /api/search-history
// @desc    Get user's search history
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const { limit = 20, skip = 0 } = req.query;

    const totalCount = await SearchHistory.countDocuments({ userId: req.userId });

    const history = await SearchHistory.find({ userId: req.userId })
      .sort({ createdAt: -1 })
      .limit(parseInt(limit))
      .skip(parseInt(skip));

    res.status(200).json({
      success: true,
      data: history,
      pagination: {
        total: totalCount,
        limit: parseInt(limit),
        skip: parseInt(skip),
        hasMore: parseInt(skip) + parseInt(limit) < totalCount
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// @route   GET /api/search-history/:id
// @desc    Get a specific search from history
// @access  Private
router.get('/:id', auth, async (req, res) => {
  try {
    const search = await SearchHistory.findOne({
      _id: req.params.id,
      userId: req.userId
    });

    if (!search) {
      return res.status(404).json({
        success: false,
        message: 'Search not found'
      });
    }

    res.status(200).json({
      success: true,
      data: search
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// @route   DELETE /api/search-history/:id
// @desc    Delete a search from history
// @access  Private
router.delete('/:id', auth, async (req, res) => {
  try {
    const search = await SearchHistory.findOneAndDelete({
      _id: req.params.id,
      userId: req.userId
    });

    if (!search) {
      return res.status(404).json({
        success: false,
        message: 'Search not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Search deleted from history'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// @route   DELETE /api/search-history
// @desc    Clear all search history for user
// @access  Private
router.delete('/', auth, async (req, res) => {
  try {
    const result = await SearchHistory.deleteMany({ userId: req.userId });

    res.status(200).json({
      success: true,
      message: `Deleted ${result.deletedCount} searches from history`
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

module.exports = router;
