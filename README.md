# 🧬 Molecular Analyzer

A comprehensive web-based molecular analysis platform for computational chemistry research and education. Built with Python, RDKit, and Streamlit, providing professional-grade molecular visualization, conformational analysis, and advanced property calculations.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![RDKit](https://img.shields.io/badge/rdkit-2023.03+-green.svg)](https://www.rdkit.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

### Core Analysis Capabilities
- **Single Molecule Analysis** - Comprehensive property calculations and 2D/3D visualization
- **Batch Processing** - High-throughput analysis of molecular datasets
- **Molecule Comparison** - Side-by-side analysis with similarity metrics
- **Conformational Analysis** - Multi-conformer generation with energy optimization
- **Advanced Properties** - Drug-likeness assessment and optimization recommendations

### Advanced Visualization
- **3D Molecular Visualization** - Interactive 3D structures with CPK coloring
- **Conformational Change Labeling** - Visual identification of molecular flexibility hotspots
- **Bond Type Differentiation** - Color-coded single, double, triple, and aromatic bonds
- **Real-time Rendering** - Dynamic visualization with customizable parameters

### Professional Features
- **Workflow Automation** - Intelligent task management and knowledge capture
- **State Management** - Persistent analysis results across sessions
- **Export Capabilities** - JSON, CSV, and visualization exports
- **Modular Architecture** - Extensible component-based design

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shahjalal2313/molecular-analyzer.git
   cd molecular-analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the Streamlit server**
   ```bash
   streamlit run app/streamlit_app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Start analyzing molecules!**

## 📖 Documentation

The documentation is built using [MkDocs](https://www.mkdocs.org/) with the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.

To build the documentation locally, run the following commands:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

The documentation will be available at `http://127.0.0.1:8000`.

- **[User Guide](docs/user-guide/README.md)** - Complete usage instructions
- **[API Reference](docs/api-reference/README.md)** - Technical documentation
- **[Tutorials](docs/tutorials/README.md)** - Step-by-step examples
- **[Development Guide](docs/development/README.md)** - Contributing guidelines

## 💡 Usage Examples

### Single Molecule Analysis
```python
# Analyze caffeine
smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
# Enter SMILES in the web interface for instant analysis
```

### Conformational Analysis
```python
# Study molecular flexibility
smiles = "CCCCC"  # Pentane - flexible chain
# Use the Conformational Analysis section to:
# - Generate multiple conformers
# - Visualize energy differences
# - Identify conformational change hotspots
```

### Batch Processing
```python
# Process multiple molecules
molecules = ["CCO", "CC(C)O", "CCCC"]
# Upload CSV file or enter multiple SMILES for batch analysis
```

## 🧪 Scientific Applications

- **Drug Discovery** - ADMET property prediction and optimization
- **Chemical Education** - Interactive molecular visualization and learning
- **Research** - Conformational analysis and molecular flexibility studies
- **Pharmaceutical Development** - Compound screening and lead optimization

## 🏗️ Architecture

A high-level overview of the project architecture is available in the [Development Guide](docs/development/README.md).

## 🔧 Requirements

### System Requirements
- **Python 3.8+**
- **4GB RAM minimum** (8GB recommended)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### Key Dependencies
- **RDKit** (2023.03+) - Core cheminformatics
- **Streamlit** (1.28+) - Web interface
- **NumPy** (1.21+) - Numerical computations
- **Pandas** (1.3+) - Data handling
- **Plotly** (5.0+) - Interactive visualizations

## 🧑‍💻 Development

Please see the [Development Guide](docs/development/README.md) for instructions on how to set up the development environment, run tests, and contribute to the project.

## 📊 Performance

- **Analysis Speed**: ~100 molecules/minute (single molecule analysis)
- **Conformer Generation**: ~10 conformers/second (depends on molecular complexity)
- **Memory Usage**: ~500MB typical, ~2GB for large datasets
- **Browser Compatibility**: Tested on Chrome 90+, Firefox 88+, Safari 14+

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/development/CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **RDKit Community** - For the excellent cheminformatics toolkit
- **Streamlit Team** - For the amazing web app framework
- **Scientific Python Community** - For the robust ecosystem

## 📞 Contact

**Developer:** SHAH MD. JALAL UDDIN  
**Email:** shahjalal2313@gmail.com  
**GitHub:** [@shahjalal2313](https://github.com/shahjalal2313)

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/shahjalal2313/molecular-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/shahjalal2313/molecular-analyzer/discussions)

---

⭐ **Star this repository** if you find it useful!

🧬 **Built with passion for computational chemistry and open science** 🧬