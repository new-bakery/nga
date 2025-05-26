import React, { useState, useEffect } from 'react';
import { X, ChevronUp, ChevronDown, Plus, Trash2, Check, AlertCircle } from 'react-feather';
import { motion, AnimatePresence } from 'framer-motion';
import './SOPForm.scss'; // You'll need to create this file

function SOPForm({ sop, onSave, onClose }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    steps: [],
    analysis_guidelines: [],
    is_disabled: false,
    domains: [],
    tags: ''
  });

  const [expandedSections, setExpandedSections] = useState({
    steps: !sop,
    guidelines: !sop
  });

  const [activeKeys, setActiveKeys] = useState(['0', '1']);

  useEffect(() => {
    if (sop) {
      const formattedSop = {
        ...sop,
        steps: Array.isArray(sop.steps) ? sop.steps : [],
        analysis_guidelines: Array.isArray(sop.analysis_guidelines) ? sop.analysis_guidelines : []
      };
      setFormData(formattedSop);
    }
  }, [sop]);

  // Animation variants
  const fadeIn = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.4 } }
  };

  const slideUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleStepChange = (index, field, value) => {
    const newSteps = [...formData.steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setFormData(prev => ({ ...prev, steps: newSteps }));
  };

  const handleStepExampleChange = (stepIndex, exampleIndex, value) => {
    const newSteps = [...formData.steps];
    if (!Array.isArray(newSteps[stepIndex].examples)) {
      newSteps[stepIndex].examples = [];
    }
    newSteps[stepIndex].examples[exampleIndex] = value;
    setFormData(prev => ({ ...prev, steps: newSteps }));
  };

  const addStepExample = (stepIndex) => {
    const newSteps = [...formData.steps];
    if (!Array.isArray(newSteps[stepIndex].examples)) {
      newSteps[stepIndex].examples = [];
    }
    newSteps[stepIndex].examples.push('');
    setFormData(prev => ({ ...prev, steps: newSteps }));
  };

  const removeStepExample = (stepIndex, exampleIndex) => {
    const newSteps = [...formData.steps];
    newSteps[stepIndex].examples.splice(exampleIndex, 1);
    setFormData(prev => ({ ...prev, steps: newSteps }));
  };

  const handleGuidelineChange = (index, field, value) => {
    const newGuidelines = [...formData.analysis_guidelines];
    newGuidelines[index] = { ...newGuidelines[index], [field]: value };
    setFormData(prev => ({ ...prev, analysis_guidelines: newGuidelines }));
  };

  const handleGuidelineReferenceChange = (guidelineIndex, refIndex, value) => {
    const newGuidelines = [...formData.analysis_guidelines];
    if (!Array.isArray(newGuidelines[guidelineIndex].reference_data)) {
      newGuidelines[guidelineIndex].reference_data = [];
    }
    newGuidelines[guidelineIndex].reference_data[refIndex] = value;
    setFormData(prev => ({ ...prev, analysis_guidelines: newGuidelines }));
  };

  const addGuidelineReference = (guidelineIndex) => {
    const newGuidelines = [...formData.analysis_guidelines];
    if (!Array.isArray(newGuidelines[guidelineIndex].reference_data)) {
      newGuidelines[guidelineIndex].reference_data = [];
    }
    newGuidelines[guidelineIndex].reference_data.push('');
    setFormData(prev => ({ ...prev, analysis_guidelines: newGuidelines }));
  };

  const removeGuidelineReference = (guidelineIndex, refIndex) => {
    const newGuidelines = [...formData.analysis_guidelines];
    newGuidelines[guidelineIndex].reference_data.splice(refIndex, 1);
    setFormData(prev => ({ ...prev, analysis_guidelines: newGuidelines }));
  };

  const addStep = () => {
    setExpandedSections(prev => ({ ...prev, steps: true }));
    setFormData(prev => ({
      ...prev,
      steps: [...prev.steps, {
        step_number: prev.steps.length + 1,
        title: '',
        description: '',
        action: '',
        examples: []
      }]
    }));
  };

  const addGuideline = () => {
    setExpandedSections(prev => ({ ...prev, guidelines: true }));
    setFormData(prev => ({
      ...prev,
      analysis_guidelines: [...prev.analysis_guidelines, {
        title: '',
        condition: '',
        action: '',
        reference_data: []
      }]
    }));
  };

  const removeStep = (index) => {
    setFormData(prev => ({
      ...prev,
      steps: prev.steps.filter((_, i) => i !== index)
    }));
  };

  const removeGuideline = (index) => {
    setFormData(prev => ({
      ...prev,
      analysis_guidelines: prev.analysis_guidelines.filter((_, i) => i !== index)
    }));
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <motion.div 
      className="sop-form"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="modal-overlay">
        <motion.div 
          className="modal-content"
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ 
            type: "spring", 
            stiffness: 400, 
            damping: 30 
          }}
        >
          <div className="modal-header">
            <motion.h2 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              {sop ? 'Edit SOP' : 'Create New SOP'}
            </motion.h2>
            <motion.button 
              className="close-button" 
              onClick={onClose}
              whileHover={{ rotate: 90, scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <X size={20} />
            </motion.button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-content">
              <motion.div 
                className="form-group"
                variants={slideUp}
                initial="hidden"
                animate="visible"
                custom={0}
              >
                <label>
                  Title
                  <span className="required">*</span>
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                  className="modern-input"
                />
              </motion.div>

              <motion.div 
                className="form-group"
                variants={slideUp}
                initial="hidden"
                animate="visible"
                custom={1}
              >
                <label>
                  Description
                  <span className="required">*</span>
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                  rows={4}
                  className="modern-textarea"
                />
              </motion.div>

              <div className="accordion">
                <motion.div 
                  className="accordion-section"
                  variants={slideUp}
                  initial="hidden"
                  animate="visible"
                  custom={2}
                >
                  <motion.div
                    className={`accordion-header ${expandedSections.steps ? 'active' : ''}`}
                    onClick={() => toggleSection('steps')}
                    whileHover={{ backgroundColor: "rgba(0, 0, 0, 0.05)" }}
                  >
                    <h3>Steps</h3>
                    <motion.span 
                      animate={{ rotate: expandedSections.steps ? 180 : 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      {expandedSections.steps ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </motion.span>
                  </motion.div>

                  <AnimatePresence>
                    {expandedSections.steps && (
                      <motion.div 
                        className="accordion-content expanded"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <AnimatePresence>
                          {formData.steps.map((step, index) => (
                            <motion.div 
                              key={index} 
                              className="step-item"
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, x: -100 }}
                              transition={{ delay: index * 0.05 }}
                              layout
                            >
                              <div className="item-header">
                                <span className="step-number">Step {index + 1}</span>
                                <motion.button
                                  type="button"
                                  className="remove-button"
                                  onClick={() => removeStep(index)}
                                  whileHover={{ scale: 1.05, backgroundColor: "#f44336" }}
                                  whileTap={{ scale: 0.95 }}
                                >
                                  <Trash2 size={16} />
                                  <span>Remove</span>
                                </motion.button>
                              </div>
                              <div className="form-row">
                                <label>Title</label>
                                <input
                                  type="text"
                                  value={step.title || ''}
                                  onChange={(e) => handleStepChange(index, 'title', e.target.value)}
                                  className="step-title modern-input"
                                />
                              </div>
                              <div className="form-row">
                                <label>Description</label>
                                <textarea
                                  value={step.description || ''}
                                  onChange={(e) => handleStepChange(index, 'description', e.target.value)}
                                  rows={3}
                                  className="modern-textarea"
                                />
                              </div>
                              <div className="form-row">
                                <label>Action</label>
                                <textarea
                                  value={step.action || ''}
                                  onChange={(e) => handleStepChange(index, 'action', e.target.value)}
                                  rows={2}
                                  className="modern-textarea"
                                />
                              </div>
                              <div className="form-row">
                                <div className="examples-header">
                                  <label>Examples</label>
                                  <motion.button
                                    type="button"
                                    className="add-button small"
                                    onClick={() => addStepExample(index)}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                  >
                                    <Plus size={16} />
                                    <span>Add Example</span>
                                  </motion.button>
                                </div>
                                <AnimatePresence>
                                  {step.examples?.map((example, exampleIndex) => (
                                    <motion.div 
                                      key={exampleIndex} 
                                      className="example-item"
                                      initial={{ opacity: 0, y: 10 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      exit={{ opacity: 0, height: 0 }}
                                      transition={{ delay: exampleIndex * 0.05 }}
                                    >
                                      <input
                                        type="text"
                                        value={example}
                                        onChange={(e) => handleStepExampleChange(index, exampleIndex, e.target.value)}
                                        placeholder="Enter example"
                                        className="modern-input"
                                      />
                                      <motion.button
                                        type="button"
                                        className="remove-button small"
                                        onClick={() => removeStepExample(index, exampleIndex)}
                                        whileHover={{ scale: 1.1, backgroundColor: "#f44336" }}
                                        whileTap={{ scale: 0.9 }}
                                      >
                                        <X size={16} />
                                      </motion.button>
                                    </motion.div>
                                  ))}
                                </AnimatePresence>
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                        <div className="add-button-container">
                          <motion.button
                            type="button"
                            className="add-button primary"
                            onClick={addStep}
                            whileHover={{ scale: 1.03, boxShadow: "0 5px 15px rgba(0, 0, 0, 0.1)" }}
                            whileTap={{ scale: 0.97 }}
                          >
                            <Plus size={18} />
                            <span>Add Step</span>
                          </motion.button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>

                <motion.div 
                  className="accordion-section"
                  variants={slideUp}
                  initial="hidden"
                  animate="visible"
                  custom={3}
                >
                  <motion.div
                    className={`accordion-header ${expandedSections.guidelines ? 'active' : ''}`}
                    onClick={() => toggleSection('guidelines')}
                    whileHover={{ backgroundColor: "rgba(0, 0, 0, 0.05)" }}
                  >
                    <h3>Analysis Guidelines</h3>
                    <motion.span 
                      animate={{ rotate: expandedSections.guidelines ? 180 : 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      {expandedSections.guidelines ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </motion.span>
                  </motion.div>

                  <AnimatePresence>
                    {expandedSections.guidelines && (
                      <motion.div 
                        className="accordion-content expanded"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <AnimatePresence>
                          {formData.analysis_guidelines.map((guideline, index) => (
                            <motion.div 
                              key={index} 
                              className="guideline-item"
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, x: -100 }}
                              transition={{ delay: index * 0.05 }}
                              layout
                            >
                              <div className="item-header">
                                <span className="guideline-number">Guideline {index + 1}</span>
                                <motion.button
                                  type="button"
                                  className="remove-button"
                                  onClick={() => removeGuideline(index)}
                                  whileHover={{ scale: 1.05, backgroundColor: "#f44336" }}
                                  whileTap={{ scale: 0.95 }}
                                >
                                  <Trash2 size={16} />
                                  <span>Remove</span>
                                </motion.button>
                              </div>
                              <div className="form-row">
                                <label>Condition</label>
                                <input
                                  type="text"
                                  value={guideline.condition || ''}
                                  onChange={(e) => handleGuidelineChange(index, 'condition', e.target.value)}
                                  className="modern-input"
                                />
                              </div>
                              <div className="form-row">
                                <label>Action</label>
                                <textarea
                                  value={guideline.action || ''}
                                  onChange={(e) => handleGuidelineChange(index, 'action', e.target.value)}
                                  rows={3}
                                  className="modern-textarea"
                                />
                              </div>
                              <div className="form-row">
                                <div className="references-header">
                                  <label>Reference Data</label>
                                  <motion.button
                                    type="button"
                                    className="add-button small"
                                    onClick={() => addGuidelineReference(index)}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                  >
                                    <Plus size={16} />
                                    <span>Add Reference</span>
                                  </motion.button>
                                </div>
                                <AnimatePresence>
                                  {guideline.reference_data?.map((ref, refIndex) => (
                                    <motion.div 
                                      key={refIndex} 
                                      className="reference-item"
                                      initial={{ opacity: 0, y: 10 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      exit={{ opacity: 0, height: 0 }}
                                      transition={{ delay: refIndex * 0.05 }}
                                    >
                                      <input
                                        type="text"
                                        value={ref}
                                        onChange={(e) => handleGuidelineReferenceChange(index, refIndex, e.target.value)}
                                        placeholder="Enter reference"
                                        className="modern-input"
                                      />
                                      <motion.button
                                        type="button"
                                        className="remove-button small"
                                        onClick={() => removeGuidelineReference(index, refIndex)}
                                        whileHover={{ scale: 1.1, backgroundColor: "#f44336" }}
                                        whileTap={{ scale: 0.9 }}
                                      >
                                        <X size={16} />
                                      </motion.button>
                                    </motion.div>
                                  ))}
                                </AnimatePresence>
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                        <div className="add-button-container">
                          <motion.button
                            type="button"
                            className="add-button primary"
                            onClick={addGuideline}
                            whileHover={{ scale: 1.03, boxShadow: "0 5px 15px rgba(0, 0, 0, 0.1)" }}
                            whileTap={{ scale: 0.97 }}
                          >
                            <Plus size={18} />
                            <span>Add Guideline</span>
                          </motion.button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </div>
            </div>

            <motion.div 
              className="form-actions"
              variants={fadeIn}
              initial="hidden"
              animate="visible"
            >
              <motion.button 
                type="submit"
                className="primary-button"
                whileHover={{ scale: 1.05, boxShadow: "0 5px 15px rgba(0, 0, 0, 0.1)" }}
                whileTap={{ scale: 0.95 }}
              >
                <Check size={18} />
                <span>Save</span>
              </motion.button>
              <motion.button 
                type="button" 
                className="secondary-button"
                onClick={onClose}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <X size={18} />
                <span>Cancel</span>
              </motion.button>
            </motion.div>
          </form>
        </motion.div>
      </div>
    </motion.div>
  );
}

export default SOPForm;