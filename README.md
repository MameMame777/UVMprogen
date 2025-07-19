# Project Template Generator Usage Guide

## Overview

This toolset provides templates for creating new FPGA verification projects based on the successful DSIMtuto project structure.

## Available Tools

### 1. Python Template Generator (Recommended)

**File**: `project_template_generator.py`

**Features**:
- Complete project structure generation
- Configurable protocol support
- UVM component templates
- CI/CD pipeline setup
- Documentation generation

**Usage**:
```bash
# Basic usage
python project_template_generator.py MyNewProject

# With custom protocol
python project_template_generator.py MyNewProject --protocol PCIe --simulator questa

# Available protocols: AXI4, PCIe, UART, SPI, I2C, custom
# Available simulators: dsim, questa, vivado, modelsim
```

**Generated Structure**:
```
MyNewProject/
├─ rtl/                    # RTL design files
├─ verification/           # Verification environment
├─ sim/                   # Simulation management
├─ docs/                  # Documentation
├─ tools/                 # Utility scripts
└─ .github/workflows/     # CI/CD pipeline
```

### 2. Windows Batch Generator

**File**: `create_project_template.bat`

**Features**:
- Windows-native implementation
- Interactive prompts
- Basic directory structure
- Simple configuration files

**Usage**:
```cmd
# Interactive mode
create_project_template.bat

# Command line mode
create_project_template.bat MyProject AXI4 dsim
```

### 3. UVM Component Generator

**File**: `uvm_component_generator.py`

**Features**:
- Generate individual UVM components
- Protocol-specific templates
- Standard UVM patterns
- Customizable constraints

**Usage**:
```bash
# Generate UVM components for AXI4 protocol
python uvm_component_generator.py AXI4

# Generate in specific directory
python uvm_component_generator.py PCIe --output-dir ../MyProject
```

**Generated Components**:
- Transaction class
- Driver class
- Monitor class
- Sequencer class
- Base sequences (read/write)

### 4. Configuration System

**File**: `template_config.json`

**Features**:
- Predefined project templates
- Simulator configurations
- Naming conventions
- Feature selections

**Templates**:
- `axi4_verification`: Full AXI4 UVM environment
- `simple_rtl_verification`: Basic RTL testbench
- `pcie_verification`: PCIe protocol verification

## Quick Start Examples

### Example 1: AXI4 Verification Project

```bash
# Generate complete AXI4 verification project
python project_template_generator.py MyAXI4Project --protocol AXI4

cd MyAXI4Project

# Generate additional UVM components
python ../DSIMtuto/tools/uvm_component_generator.py AXI4

# Initialize git repository
git init
git add .
git commit -m "Initial project setup from DSIMtuto template"
```

### Example 2: Custom Protocol Project

```bash
# Create custom protocol project
python project_template_generator.py MyCustomProject --protocol CUSTOM

# Customize the generated templates
# - Edit rtl/interfaces/custom_if.sv
# - Modify verification components
# - Update test scenarios
```

### Example 3: Simple RTL Verification

```bash
# Windows batch version for simple projects
create_project_template.bat SimpleRTL Custom dsim

cd SimpleRTL

# Add your RTL modules to rtl/ directory
# Customize testbench in verification/testbench/
```

## Customization Guidelines

### 1. RTL Interface Customization

After generation, customize the interface file:

```systemverilog
// Edit rtl/interfaces/your_protocol_if.sv
interface your_protocol_if;
    // Add your specific signals
    logic [31:0] custom_signal;
    logic        custom_enable;
    
    // Define modports
    modport master (
        output custom_signal,
        output custom_enable
    );
endinterface
```

### 2. UVM Component Customization

Customize generated UVM components:

```systemverilog
// In verification/uvm/agents/your_protocol_driver.sv
virtual task drive_write(your_protocol_transaction trans);
    // Implement your protocol-specific timing
    @(posedge vif.clk);
    vif.custom_signal <= trans.data;
    vif.custom_enable <= 1'b1;
    // Add protocol handshaking
endtask
```

### 3. Test Scenario Addition

Add new test scenarios:

```systemverilog
// Create new test in verification/uvm/tests/
class your_protocol_stress_test extends your_protocol_base_test;
    // Implement stress testing scenarios
endclass
```

## Best Practices

### 1. Naming Conventions

Follow established naming conventions:
- **Modules**: `Snake_Case` (e.g., `AXI4_Master`)
- **Signals**: `snake_case` (e.g., `data_valid`)
- **Classes**: `snake_case` (e.g., `axi4_driver`)
- **Files**: `snake_case.sv` (e.g., `axi4_driver.sv`)

### 2. Directory Organization

Maintain clean directory structure:
- Keep RTL separate from verification
- Group related UVM components
- Separate configuration from execution
- Organize documentation logically

### 3. Version Control

Initialize version control properly:

```bash
# Use provided .gitignore
cp DSIMtuto/.gitignore .

# Add simulation output exclusions
echo "sim/output/*" >> .gitignore

# Initial commit
git add .
git commit -m "Initial project from DSIMtuto template"
```

### 4. CI/CD Integration

The generated GitHub Actions workflow includes:
- Automatic linting
- Multi-test execution
- Artifact collection
- Daily regression testing

Customize `.github/workflows/ci.yml` for your specific needs.

## Template Maintenance

### Adding New Protocol Templates

1. **Update Configuration**: Add new protocol to `template_config.json`
2. **Create Interface Template**: Define protocol-specific interface
3. **Add UVM Components**: Create protocol-specific UVM classes
4. **Test Generation**: Verify template generates correctly

### Updating Tool Features

1. **Feature Addition**: Implement in Python generator
2. **Batch Support**: Add equivalent batch functionality
3. **Documentation**: Update this guide
4. **Testing**: Verify with sample projects

## Troubleshooting

### Common Issues

**Problem**: "Template directory already exists"
**Solution**: Remove existing directory or use different name

**Problem**: "Missing UVM components"
**Solution**: Run UVM component generator separately

**Problem**: "Simulation fails to compile"
**Solution**: Customize interface signals for your protocol

**Problem**: "CI/CD pipeline fails"
**Solution**: Update simulator paths in workflow file

### Getting Help

1. Check the DSIMtuto reference implementation
2. Review generated README.md files
3. Examine working examples in DSIMtuto project
4. Consult UVM and SystemVerilog documentation

## Contributing

To improve the template system:

1. **Test New Protocols**: Verify templates work for different protocols
2. **Add Features**: Implement missing functionality
3. **Documentation**: Update guides and examples
4. **Feedback**: Report issues and suggestions

The template system is designed to evolve based on user needs and industry best practices.
