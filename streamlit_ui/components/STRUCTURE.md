# Streamlit UI Components - Standard Structure

This directory contains the restructured, standardized component system for the Molecular Analyzer Streamlit UI.

## 📁 Directory Structure

```
components/
├── __init__.py                 # Main package imports
├── base.py                     # BaseComponent class
├── charts/                     # Chart visualization components
│   ├── __init__.py
│   ├── bar_chart.py           # BarChartComponent
│   ├── scatter_plot.py        # ScatterPlotComponent
│   └── line_plot.py           # LinePlotComponent
├── input/                      # Molecule input components
│   ├── __init__.py
│   └── molecule_input.py      # MoleculeInputComponent
├── display/                    # Message display components
│   ├── __init__.py
│   └── message_display.py     # MessageDisplayComponent
└── tests/                      # Test files
    ├── test_final_structure.py
    └── simple_import_test.py
```

## 🏗️ Architecture

### BaseComponent (`base.py`)
- Abstract base class for all UI components
- Provides common functionality:
  - Error handling and validation
  - State management integration
  - Logging and analytics
  - Consistent widget key generation
  - Message display utilities

### Chart Components (`charts/`)
All chart components inherit from `BaseComponent` and provide:

#### BarChartComponent
- Configurable bar charts (vertical/horizontal)
- Grouping, stacking, and overlay modes
- Interactive hover information
- Export capabilities

#### ScatterPlotComponent  
- Advanced scatter plots with correlation analysis
- Trend line fitting (linear, polynomial, exponential)
- Color mapping and size mapping
- Statistical annotations

#### LinePlotComponent
- Multi-series line plots
- Smoothing options (moving average, exponential, polynomial)
- Area fill and marker customization
- Statistical summaries

### Input Components (`input/`)

#### MoleculeInputComponent
- Manual SMILES entry with validation
- Predefined molecule selection
- CSV file upload and validation
- Batch processing capabilities
- Multiple input methods (dropdown, grid, categorized)

### Display Components (`display/`)

#### MessageDisplayComponent
- Success, error, warning, and info messages
- Message queuing and prioritization
- Auto-dismiss functionality
- Collapsible detailed information
- Consistent styling

## 🚀 Usage Examples

### Basic Import
```python
from components import (
    BarChartComponent,
    ScatterPlotComponent, 
    LinePlotComponent,
    MoleculeInputComponent,
    MessageDisplayComponent
)
```

### Chart Components
```python
# Create bar chart
bar_chart = BarChartComponent("Molecular Weights")
bar_chart.configure_chart(
    title="Molecular Weight Comparison",
    x_label="Molecules", 
    y_label="Weight (g/mol)"
)

# Render chart (in Streamlit context)
fig = bar_chart.render(
    data=molecular_data,
    x_column='molecule',
    y_column='molecular_weight',
    show_config=True
)
```

### Input Components
```python
# Create molecule input
molecule_input = MoleculeInputComponent("Molecule Input")

# Single molecule input
smiles = molecule_input.render(
    input_type="single",
    methods=["manual", "examples"]
)

# Batch input
smiles_list, df = molecule_input.render(
    input_type="batch", 
    methods=["text_area", "file"]
)
```

### Message Display
```python
# Create message display
messages = MessageDisplayComponent("Messages")

# Show different message types
messages.show_success("Analysis completed successfully!")
messages.show_error("Invalid SMILES structure", show_details=True)
messages.show_warning("Low data quality", suggested_action="Add more data points")
messages.show_info("Processing may take a few minutes", collapsible=True)
```

## 🧪 Testing

Run the test suite to verify the structure:

```bash
cd components/
python test_final_structure.py
```

This validates:
- All components can be imported correctly
- Inheritance from BaseComponent works
- Core functionality operates as expected
- Package structure is properly organized

## 🔧 Key Features

### Consistent API
- All components inherit from `BaseComponent`
- Standardized `render()` method
- Common error handling patterns
- Uniform validation approach

### Error Handling
- Graceful error handling with user feedback
- Detailed error logging for debugging
- Validation with clear error messages
- Safe fallbacks for missing dependencies

### Extensibility
- Easy to add new component types
- Plugin-style architecture
- Clear separation of concerns
- Reusable base functionality

### Performance
- Efficient component rendering
- Minimal dependencies
- Optimized for Streamlit
- Memory-conscious design

## 📋 Component Standards

All components follow these standards:

1. **Inherit from BaseComponent**
2. **Implement abstract `render()` method**
3. **Use `get_key()` for widget keys**
4. **Handle errors with `add_error()` and `add_warning()`**
5. **Log interactions with `log_interaction()`**
6. **Validate inputs before processing**
7. **Provide clear documentation**
8. **Include type hints**

## 🔄 Migration from Old Structure

The old phase-based structure has been replaced with this standard organization:

- `phase_1_foundation/` → `base.py`
- `phase_2_components/` → `input/` and `display/`
- `phase_3_services/charts/` → `charts/`

All functionality has been preserved while improving:
- Import clarity
- Code organization
- Maintainability
- Testing coverage
- Documentation

---

**Version**: 1.0.0  
**Last Updated**: 2025-07-18  
**Status**: ✅ Fully Functional