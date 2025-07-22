# 📖 Molecular Analyzer User Guide

Welcome to the comprehensive user guide for Molecular Analyzer! This guide will help you get the most out of the platform's molecular analysis and visualization capabilities.

## 🎯 Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Analysis Types](#analysis-types)
4. [Advanced Features](#advanced-features)
5. [Tips & Best Practices](#tips--best-practices)
6. [Troubleshooting](#troubleshooting)

## 🚀 Getting Started

### First Steps
1. **Launch the application** using `streamlit run app/streamlit_app.py`
2. **Open your browser** to the provided local URL (usually `http://localhost:8501`)
3. **Choose your analysis type** from the sidebar navigation menu

### Supported Input Formats
- **SMILES strings** (e.g., `CCO` for ethanol)
- **CSV files** with SMILES column for batch processing
- **Direct text input** for multiple molecules

## 🖥️ Interface Overview

### Navigation Menu
The sidebar contains the main navigation options:

- **Single Molecule Analysis** - Analyze one molecule at a time
- **Batch Analysis** - Process multiple molecules simultaneously
- **Molecule Comparison** - Compare two or more molecules
- **Conformational Analysis** - Study molecular flexibility
- **Advanced Analysis** - Drug-likeness and property optimization
- **System Info** - Technical information and system status

### Main Content Area
The main area displays:
- Input controls for molecular data
- Analysis results and visualizations
- Interactive charts and 3D models
- Export options for data and visualizations

## 🔬 Analysis Types

### Single Molecule Analysis

**Purpose**: Comprehensive analysis of individual molecules

**How to Use**:
1. Enter a SMILES string in the input field
2. Click "Analyze Molecule"
3. Review the calculated properties
4. Explore 2D and 3D visualizations

**Key Features**:
- Molecular properties (MW, LogP, TPSA, etc.)
- 2D molecular structure
- Interactive 3D visualization
- Drug-likeness assessment

### Batch Analysis

**Purpose**: High-throughput processing of molecular datasets

**How to Use**:
1. Upload a CSV file with SMILES column
2. Or enter multiple SMILES (one per line)
3. Click "Process Batch"
4. Download results as CSV

**Key Features**:
- Process up to 1000 molecules
- Statistical summaries
- Property distributions
- Batch export capabilities

### Molecule Comparison

**Purpose**: Side-by-side analysis of multiple molecules

**How to Use**:
1. Enter 2-4 SMILES strings
2. Assign names to each molecule
3. Click "Compare Molecules"
4. Analyze differences and similarities

**Key Features**:
- Property comparison tables
- Similarity calculations
- Overlay visualizations
- Radar charts for property profiles

### Conformational Analysis

**Purpose**: Study molecular flexibility and conformational changes

**How to Use**:
1. Enter a SMILES string
2. Set number of conformers (1-50)
3. Choose optimization level
4. Enable "Show Conformational Changes" for advanced visualization

**Key Features**:
- Multiple conformer generation
- Energy analysis and plots
- 3D conformer visualization
- **Conformational change labeling** with color-coded highlights
- Flexibility hotspot identification

### Advanced Analysis

**Purpose**: Drug-likeness assessment and molecular optimization

**How to Use**:
1. Enter a SMILES string
2. Click "Perform Advanced Analysis"
3. Review drug-likeness metrics
4. Explore optimization suggestions

**Key Features**:
- Lipinski's Rule of Five
- Veber's Rule compliance
- ADMET predictions
- Optimization recommendations

## ⭐ Advanced Features

### 3D Visualization Options

**Visualization Styles**:
- **Ball and Stick** - Standard molecular representation
- **Space-filling** - Van der Waals surface representation
- **Wireframe** - Simplified bond-only view

**Bond Type Visualization**:
- 🔵 **Blue bonds** - Triple bonds (C≡C, C≡N)
- 🟢 **Green bonds** - Double bonds (C=C, C=O)
- 🟣 **Purple bonds** - Aromatic bonds (benzene rings)
- **Dark gray bonds** - Single bonds (C-C, C-H)

**Conformational Change Features**:
- **Shortened hydrogen bonds** for better visual proportion
- **Color-coded change highlighting**:
  - 🔴 **Red**: Major changes (>2.0 Å displacement)
  - 🟠 **Orange**: Minor changes (1.0-2.0 Å displacement)
- **Interactive conformer comparison**
- **Real-time change analysis**

### Export Options

**Available Formats**:
- **JSON** - Complete analysis data
- **CSV** - Tabular property data
- **HTML** - Interactive visualizations
- **PNG** - Static images

**What You Can Export**:
- Molecular properties
- Analysis results
- 3D visualizations
- Comparison data

### State Management

The application automatically saves:
- Analysis results across sessions
- Visualization settings
- Input history
- Cached calculations

## 💡 Tips & Best Practices

### Input Preparation
- **Validate SMILES** before analysis using online checkers
- **Use canonical SMILES** for consistency
- **Clean your data** before batch processing

### Performance Optimization
- **Limit conformers** to 20-30 for complex molecules
- **Use batch processing** for multiple molecules
- **Clear cache** if memory usage becomes high

### Visualization Best Practices
- **Enable conformational changes** for flexibility studies
- **Use appropriate visualization styles** for your analysis purpose
- **Save visualizations** before clearing results

### Conformational Analysis Tips
- **Start with 10-20 conformers** for initial exploration
- **Use higher energy thresholds** (5-10 kcal/mol) for diverse conformers
- **Enable change labeling** to identify flexible regions
- **Compare low-energy conformers** for meaningful analysis

## 🔧 Troubleshooting

### Common Issues

**"Invalid SMILES" Error**:
- Check for typos in the SMILES string
- Ensure proper syntax (no spaces, correct parentheses)
- Try using a different SMILES representation

**Slow Performance**:
- Reduce number of conformers
- Clear browser cache
- Check system memory usage
- Restart the application

**Visualization Not Loading**:
- Refresh the browser page
- Check browser compatibility (Chrome, Firefox, Safari, Edge)
- Disable browser extensions that might interfere

**3D Visualization Issues**:
- Update your browser to the latest version
- Enable hardware acceleration
- Try a different visualization style

### Getting Help

If you encounter issues:

1. **Check the error message** for specific guidance
2. **Restart the application** to clear temporary issues
3. **Review the troubleshooting section** above
4. **Contact support** with detailed error descriptions

## 📞 Support

**Developer**: SHAH MD. JALAL UDDIN  
**Email**: shahjalal2313@gmail.com  
**GitHub Issues**: [Report Bug](https://github.com/shahjalal2313/molecular-analyzer/issues)

---

🧬 **Happy analyzing!** We hope this guide helps you make the most of Molecular Analyzer's powerful features.