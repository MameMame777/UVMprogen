#!/usr/bin/env python3
"""
FPGA Verification Project Template Generator
Author: DSIMtuto Team
Date: July 19, 2025

This script generates a standardized FPGA verification project structure
based on the successful DSIMtuto project template.
"""

import os
import sys
import argparse
from pathlib import Path
import json
from datetime import datetime
from uvm_component_generator import UVMComponentGenerator

class ProjectTemplateGenerator:
    def __init__(self, project_name, protocol="AXI4", simulator="dsim"):
        self.project_name = project_name
        self.protocol = protocol.lower()
        self.simulator = simulator.lower()
        self.base_path = Path(project_name)
        
    def create_directory_structure(self):
        """Create the standard directory structure"""
        directories = [
            # RTL directories
            "rtl",
            "rtl/interfaces",
            
            # Verification directories
            "verification",
            "verification/common",
            "verification/testbench",
            "verification/uvm",
            "verification/uvm/agents",
            f"verification/uvm/agents/{self.protocol}_agent",
            "verification/uvm/env",
            "verification/uvm/sequences",
            "verification/uvm/tests",
            
            # Simulation directories
            "sim",
            "sim/run",
            "sim/config",
            "sim/config/filelists",
            "sim/output",
            
            # Documentation and tools
            "docs",
            "tools",
            "diary",
            
            # GitHub Actions
            ".github",
            ".github/workflows"
        ]
        
        for directory in directories:
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
    
    def generate_rtl_templates(self):
        """Generate RTL template files"""
        # Interface template
        interface_content = f"""// {self.protocol.upper()} Interface
// File: {self.protocol}_if.sv
// Generated: {datetime.now().strftime('%Y-%m-%d')}

interface {self.protocol}_if;
    // Clock and reset
    logic clk;
    logic reset;
    
    // Add protocol-specific signals here
    // TODO: Define {self.protocol.upper()} interface signals
    
    // Modports for different perspectives
    modport master (
        input  clk, reset,
        // TODO: Add master signals
    );
    
    modport slave (
        input  clk, reset,
        // TODO: Add slave signals
    );
    
endinterface
"""
        self._write_file("rtl/interfaces", f"{self.protocol}_if.sv", interface_content)
        
        # Main module template
        module_content = f"""// {self.project_name} Main Module
// File: {self.project_name.lower()}_core.sv
// Generated: {datetime.now().strftime('%Y-%m-%d')}

module {self.project_name.title()}_Core (
    {self.protocol}_if.slave bus_if
);

    // TODO: Implement module functionality
    
endmodule
"""
        self._write_file("rtl", f"{self.project_name.lower()}_core.sv", module_content)
    
    def generate_uvm_templates(self):
        """Generate UVM verification templates using UVMComponentGenerator"""
        print(f"Generating UVM components for {self.protocol.upper()} protocol...")
        
        # Create UVM component generator instance
        uvm_generator = UVMComponentGenerator(
            protocol=self.protocol,
            output_dir=self.base_path
        )
        
        # Generate all UVM components
        generated_files = uvm_generator.generate_all_components()
        
        # Generate environment class (not included in component generator)
        self._generate_environment()
        
        # Generate testbench top module
        self._generate_testbench_top()
        
        return generated_files
    
    def _generate_environment(self):
        """Generate UVM environment class"""
        env_content = f"""// {self.protocol.upper()} Environment Class
// File: {self.protocol}_env.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.protocol}_env extends uvm_env;
    `uvm_component_utils({self.protocol}_env)
    
    // UVM components
    {self.protocol}_agent master_agent;
    {self.protocol}_agent slave_agent;
    {self.protocol}_scoreboard sb;
    
    function new(string name = "{self.protocol}_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Create agents
        master_agent = {self.protocol}_agent::type_id::create("master_agent", this);
        slave_agent = {self.protocol}_agent::type_id::create("slave_agent", this);
        
        // Set agent configurations
        uvm_config_db#(uvm_active_passive_enum)::set(this, "master_agent", "is_active", UVM_ACTIVE);
        uvm_config_db#(uvm_active_passive_enum)::set(this, "slave_agent", "is_active", UVM_PASSIVE);
        
        // Create scoreboard
        sb = {self.protocol}_scoreboard::type_id::create("sb", this);
    endfunction
    
    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        // Connect monitors to scoreboard
        master_agent.monitor.ap.connect(sb.master_port);
        slave_agent.monitor.ap.connect(sb.slave_port);
    endfunction

endclass
"""
        self._write_file("verification/uvm/env", f"{self.protocol}_env.sv", env_content)
        
        # Generate scoreboard
        scoreboard_content = f"""// {self.protocol.upper()} Scoreboard Class
// File: {self.protocol}_scoreboard.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.protocol}_scoreboard extends uvm_scoreboard;
    `uvm_component_utils({self.protocol}_scoreboard)
    
    // Analysis imports for receiving transactions
    uvm_analysis_imp_master#({self.protocol}_transaction, {self.protocol}_scoreboard) master_port;
    uvm_analysis_imp_slave#({self.protocol}_transaction, {self.protocol}_scoreboard) slave_port;
    
    // Transaction queues
    {self.protocol}_transaction master_queue[$];
    {self.protocol}_transaction slave_queue[$];
    
    // Statistics
    int transactions_compared = 0;
    int transactions_passed = 0;
    int transactions_failed = 0;
    
    function new(string name = "{self.protocol}_scoreboard", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        master_port = new("master_port", this);
        slave_port = new("slave_port", this);
    endfunction
    
    virtual function void write_master({self.protocol}_transaction trans);
        {self.protocol}_transaction trans_clone;
        $cast(trans_clone, trans.clone());
        master_queue.push_back(trans_clone);
        
        `uvm_info(get_type_name(), $sformatf("Master transaction received: %s", trans.convert2string()), UVM_HIGH)
        
        // Try to find matching slave transaction
        check_transactions();
    endfunction
    
    virtual function void write_slave({self.protocol}_transaction trans);
        {self.protocol}_transaction trans_clone;
        $cast(trans_clone, trans.clone());
        slave_queue.push_back(trans_clone);
        
        `uvm_info(get_type_name(), $sformatf("Slave transaction received: %s", trans.convert2string()), UVM_HIGH)
        
        // Try to find matching master transaction
        check_transactions();
    endfunction
    
    virtual function void check_transactions();
        {self.protocol}_transaction master_trans, slave_trans;
        
        // Simple FIFO comparison - customize based on your protocol
        if (master_queue.size() > 0 && slave_queue.size() > 0) begin
            master_trans = master_queue.pop_front();
            slave_trans = slave_queue.pop_front();
            
            transactions_compared++;
            
            if (master_trans.compare(slave_trans)) begin
                transactions_passed++;
                `uvm_info(get_type_name(), 
                         $sformatf("PASS: Transactions match\\nMaster: %s\\nSlave:  %s", 
                                  master_trans.convert2string(), slave_trans.convert2string()), 
                         UVM_MEDIUM)
            end else begin
                transactions_failed++;
                `uvm_error(get_type_name(), 
                          $sformatf("FAIL: Transactions do not match\\nMaster: %s\\nSlave:  %s", 
                                   master_trans.convert2string(), slave_trans.convert2string()))
            end
        end
    endfunction
    
    virtual function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        
        `uvm_info(get_type_name(), "=== SCOREBOARD SUMMARY ===", UVM_NONE)
        `uvm_info(get_type_name(), $sformatf("Transactions compared: %0d", transactions_compared), UVM_NONE)
        `uvm_info(get_type_name(), $sformatf("Transactions passed:   %0d", transactions_passed), UVM_NONE)
        `uvm_info(get_type_name(), $sformatf("Transactions failed:   %0d", transactions_failed), UVM_NONE)
        
        if (transactions_failed > 0) begin
            `uvm_error(get_type_name(), "TEST FAILED: One or more transactions failed comparison")
        end else if (transactions_compared == 0) begin
            `uvm_warning(get_type_name(), "TEST WARNING: No transactions were compared")
        end else begin
            `uvm_info(get_type_name(), "TEST PASSED: All transactions passed comparison", UVM_NONE)
        end
    endfunction

endclass
"""
        self._write_file("verification/uvm/env", f"{self.protocol}_scoreboard.sv", scoreboard_content)
    
    def _generate_testbench_top(self):
        """Generate testbench top module"""
        tb_top_content = f"""// {self.project_name} Testbench Top Module
// File: tb_top.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

// Include all verification files
`include "{self.protocol}_transaction.sv"
`include "{self.protocol}_sequencer.sv"
`include "{self.protocol}_driver.sv"
`include "{self.protocol}_monitor.sv"
`include "{self.protocol}_agent.sv"
`include "{self.protocol}_scoreboard.sv"
`include "{self.protocol}_env.sv"

// Include sequences
`include "{self.protocol}_base_seq.sv"
`include "{self.protocol}_read_seq.sv"
`include "{self.protocol}_write_seq.sv"

// Include tests
`include "{self.protocol}_base_test.sv"

module tb_top;
    
    // Clock and reset generation
    logic clk = 0;
    logic reset = 1;
    
    // Clock generation (100MHz)
    always #5 clk = ~clk;
    
    // Reset generation
    initial begin
        reset = 1;
        repeat(10) @(posedge clk);
        reset = 0;
    end
    
    // Interface instantiation
    {self.protocol}_if bus_if();
    
    // Connect clock and reset to interface
    assign bus_if.clk = clk;
    assign bus_if.reset = reset;
    
    // DUT instantiation
    {self.project_name.title()}_Core dut (
        .bus_if(bus_if.slave)
    );
    
    // UVM configuration and test execution
    initial begin
        // Set virtual interface in config database
        uvm_config_db#(virtual {self.protocol}_if)::set(null, "*", "vif", bus_if);
        
        // Enable UVM verbosity
        uvm_config_db#(int)::set(null, "*", "recording_detail", UVM_FULL);
        
        // Run the test
        run_test();
    end
    
    // Optional: Dump waves for debugging
    initial begin
        $dumpfile("{self.protocol}_waves.vcd");
        $dumpvars(0, tb_top);
    end
    
    // Timeout watchdog
    initial begin
        #1000000; // 1ms timeout
        `uvm_fatal("TIMEOUT", "Test timed out!")
    end

endmodule
"""
        self._write_file("verification/testbench", "tb_top.sv", tb_top_content)
        
        # Generate additional test classes
        self._generate_additional_tests()
    
    def _generate_additional_tests(self):
        """Generate additional test classes using the UVM components"""
        
        # Read test
        read_test_content = f"""// {self.protocol.upper()} Read Test Class
// File: {self.protocol}_read_test.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.protocol}_read_test extends {self.protocol}_base_test;
    `uvm_component_utils({self.protocol}_read_test)

    function new(string name = "{self.protocol}_read_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task run_phase(uvm_phase phase);
        {self.protocol}_read_seq read_seq;
        
        phase.raise_objection(this);
        
        `uvm_info(get_type_name(), "Starting {self.protocol.upper()} read test", UVM_MEDIUM)
        
        // Wait for reset deassertion
        wait(!vif.reset);
        repeat(10) @(posedge vif.clk);
        
        // Execute read sequence
        read_seq = {self.protocol}_read_seq::type_id::create("read_seq");
        read_seq.start(env.master_agent.sequencer);
        
        // Wait for sequence completion
        repeat(50) @(posedge vif.clk);
        
        `uvm_info(get_type_name(), "Read test completed successfully", UVM_MEDIUM)
        
        phase.drop_objection(this);
    endtask

endclass
"""
        self._write_file("verification/uvm/tests", f"{self.protocol}_read_test.sv", read_test_content)
        
        # Write test
        write_test_content = f"""// {self.protocol.upper()} Write Test Class
// File: {self.protocol}_write_test.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.protocol}_write_test extends {self.protocol}_base_test;
    `uvm_component_utils({self.protocol}_write_test)

    function new(string name = "{self.protocol}_write_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task run_phase(uvm_phase phase);
        {self.protocol}_write_seq write_seq;
        
        phase.raise_objection(this);
        
        `uvm_info(get_type_name(), "Starting {self.protocol.upper()} write test", UVM_MEDIUM)
        
        // Wait for reset deassertion
        wait(!vif.reset);
        repeat(10) @(posedge vif.clk);
        
        // Execute write sequence
        write_seq = {self.protocol}_write_seq::type_id::create("write_seq");
        write_seq.start(env.master_agent.sequencer);
        
        // Wait for sequence completion
        repeat(50) @(posedge vif.clk);
        
        `uvm_info(get_type_name(), "Write test completed successfully", UVM_MEDIUM)
        
        phase.drop_objection(this);
    endtask

endclass
"""
        self._write_file("verification/uvm/tests", f"{self.protocol}_write_test.sv", write_test_content)
        
        # Mixed test
        mixed_test_content = f"""// {self.protocol.upper()} Mixed Test Class
// File: {self.protocol}_mixed_test.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.protocol}_mixed_test extends {self.protocol}_base_test;
    `uvm_component_utils({self.protocol}_mixed_test)

    function new(string name = "{self.protocol}_mixed_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task run_phase(uvm_phase phase);
        {self.protocol}_read_seq read_seq;
        {self.protocol}_write_seq write_seq;
        
        phase.raise_objection(this);
        
        `uvm_info(get_type_name(), "Starting {self.protocol.upper()} mixed test", UVM_MEDIUM)
        
        // Wait for reset deassertion
        wait(!vif.reset);
        repeat(10) @(posedge vif.clk);
        
        // Execute mixed sequences
        fork
            begin
                write_seq = {self.protocol}_write_seq::type_id::create("write_seq");
                write_seq.start(env.master_agent.sequencer);
            end
            begin
                #100; // Slight delay
                read_seq = {self.protocol}_read_seq::type_id::create("read_seq");
                read_seq.start(env.master_agent.sequencer);
            end
        join
        
        // Wait for completion
        repeat(100) @(posedge vif.clk);
        
        `uvm_info(get_type_name(), "Mixed test completed successfully", UVM_MEDIUM)
        
        phase.drop_objection(this);
    endtask

endclass
"""
        self._write_file("verification/uvm/tests", f"{self.protocol}_mixed_test.sv", mixed_test_content)
    
    def generate_simulation_config(self):
        """Generate simulation configuration files"""
        
        # Test configuration
        test_config_content = f"""# {self.project_name} Test Configuration
# Format: test_name|description|filelist|uvm_test|waves_file|verbosity
#
# Generated: {datetime.now().strftime('%Y-%m-%d')}

# Basic tests
{self.protocol}_base|{self.protocol.upper()} Base Framework Test|filelists/{self.protocol}_base.f|{self.protocol}_base_test|{self.protocol}_base_waves.vcd|UVM_MEDIUM
{self.protocol}_read|{self.protocol.upper()} Read Operations Test|filelists/{self.protocol}_full.f|{self.protocol}_read_test|{self.protocol}_read_waves.vcd|UVM_MEDIUM
{self.protocol}_write|{self.protocol.upper()} Write Operations Test|filelists/{self.protocol}_full.f|{self.protocol}_write_test|{self.protocol}_write_waves.vcd|UVM_MEDIUM
{self.protocol}_mixed|{self.protocol.upper()} Mixed Operations Test|filelists/{self.protocol}_full.f|{self.protocol}_mixed_test|{self.protocol}_mixed_waves.vcd|UVM_MEDIUM
simple_tb|Simple Testbench|filelists/simple.f||simple_waves.vcd|

# Advanced tests (templates)
{self.protocol}_regression|{self.protocol.upper()} Regression Test Suite|filelists/{self.protocol}_regression.f|{self.protocol}_regression_test|{self.protocol}_regression_waves.vcd|UVM_HIGH
"""
        self._write_file("sim/config", "test_config.cfg", test_config_content)
        
        # Base filelist
        filelist_content = f"""# {self.protocol.upper()} Base Framework Test Filelist
# Generated: {datetime.now().strftime('%Y-%m-%d')}

# RTL Interface Files
..\\..\\rtl\\interfaces\\{self.protocol}_if.sv

# RTL Design Files
..\\..\\rtl\\{self.project_name.lower()}_core.sv

# UVM Test Files
..\\..\\verification\\common\\{self.protocol}_transaction.sv
..\\..\\verification\\uvm\\tests\\{self.protocol}_base_test.sv

# UVM Testbench Top
..\\..\\verification\\testbench\\tb_top.sv
"""
        self._write_file("sim/config/filelists", f"{self.protocol}_base.f", filelist_content)
        
        # Full filelist for complete UVM tests
        full_filelist_content = f"""# {self.protocol.upper()} Full Test Suite Filelist
# Generated: {datetime.now().strftime('%Y-%m-%d')}

# RTL Interface Files
..\\..\\rtl\\interfaces\\{self.protocol}_if.sv

# RTL Design Files
..\\..\\rtl\\{self.project_name.lower()}_core.sv

# UVM Common Files
..\\..\\verification\\common\\{self.protocol}_transaction.sv

# UVM Agent Components
..\\..\\verification\\uvm\\agents\\{self.protocol}_agent\\{self.protocol}_sequencer.sv
..\\..\\verification\\uvm\\agents\\{self.protocol}_agent\\{self.protocol}_driver.sv
..\\..\\verification\\uvm\\agents\\{self.protocol}_agent\\{self.protocol}_monitor.sv
..\\..\\verification\\uvm\\agents\\{self.protocol}_agent\\{self.protocol}_agent.sv

# UVM Environment
..\\..\\verification\\uvm\\env\\{self.protocol}_scoreboard.sv
..\\..\\verification\\uvm\\env\\{self.protocol}_env.sv

# UVM Sequences
..\\..\\verification\\uvm\\sequences\\{self.protocol}_base_seq.sv
..\\..\\verification\\uvm\\sequences\\{self.protocol}_read_seq.sv
..\\..\\verification\\uvm\\sequences\\{self.protocol}_write_seq.sv

# UVM Tests
..\\..\\verification\\uvm\\tests\\{self.protocol}_base_test.sv
..\\..\\verification\\uvm\\tests\\{self.protocol}_read_test.sv
..\\..\\verification\\uvm\\tests\\{self.protocol}_write_test.sv
..\\..\\verification\\uvm\\tests\\{self.protocol}_mixed_test.sv

# UVM Testbench Top
..\\..\\verification\\testbench\\tb_top.sv
"""
        self._write_file("sim/config/filelists", f"{self.protocol}_full.f", full_filelist_content)
        
        # Run script template
        run_script_content = f"""@echo off
setlocal enabledelayedexpansion

REM ================================================================================
REM {self.project_name} Unified Test Execution Script
REM Generated: {datetime.now().strftime('%Y-%m-%d')}
REM ================================================================================

REM DSIM Environment Setup
set "DSIM_LICENSE=%USERPROFILE%\\AppData\\Local\\metrics-ca\\dsim-license.json"
call "%USERPROFILE%\\AppData\\Local\\metrics-ca\\dsim\\20240422.0.0\\shell_activate.bat"

REM Configuration file path
set "CONFIG_FILE=..\\config\\test_config.cfg"

REM Check if configuration file exists
if not exist "%CONFIG_FILE%" (
    echo ERROR: Configuration file %CONFIG_FILE% not found!
    exit /b 1
)

REM Parse command line arguments
set "TEST_NAME=%1"

REM If no test name provided, show available tests
if "%TEST_NAME%"=="" (
    echo Available test configurations:
    echo ================================================================================
    for /f "tokens=1,2 delims=|" %%a in ('type "%CONFIG_FILE%" ^| findstr /v "^#" ^| findstr /v "^$"') do (
        echo   %%a - %%b
    )
    echo ================================================================================
    echo Usage: run.bat [TEST_NAME]
    exit /b 0
)

REM TODO: Add full test execution logic (copy from DSIMtuto project)

echo Test execution completed!
exit /b 0
"""
        self._write_file("sim/run", "run.bat", run_script_content)
    
    def generate_documentation(self):
        """Generate documentation templates"""
        
        readme_content = f"""# {self.project_name} - {self.protocol.upper()} Verification Project

## Overview

This project implements a comprehensive verification environment for {self.protocol.upper()} protocol 
using UVM (Universal Verification Methodology) and the DSIM simulator.

**Generated from DSIMtuto template on {datetime.now().strftime('%Y-%m-%d')}**

## Key Features

- ✅ **Unified Test Execution System**: Configuration-driven test management
- ✅ **Comprehensive UVM Verification**: Multiple test scenarios with full coverage
- ✅ **{self.protocol.upper()} Protocol Implementation**: Complete interface and module verification
- ✅ **Automated Environment Setup**: DSIM simulator with UVM-1.2 integration
- ✅ **Scalable Test Framework**: Easy addition of new test configurations

## Project Structure

```
{self.project_name}/
├─ rtl/                    # RTL design files
│  ├─ interfaces/         # Protocol interfaces
│  └─ {self.project_name.lower()}_core.sv    # Main module
├─ verification/           # Verification environment
│  ├─ common/             # Common test files
│  ├─ testbench/          # Testbench files
│  └─ uvm/                # UVM components
├─ sim/                   # Simulation management
│  ├─ run/               # Execution scripts
│  ├─ config/            # Configuration files
│  └─ output/            # Output files
├─ tools/                # Utility scripts
├─ docs/                 # Documentation
└─ .github/workflows/    # CI/CD pipeline
```

## Quick Start

Navigate to the `sim/run` directory and use the unified test execution system:

```bash
cd sim/run

# Show all available test configurations
.\\run.bat

# Execute a specific test
.\\run.bat {self.protocol}_base
```

## Available Tests

| Test Name | Type | Description |
|-----------|------|-------------|
| `{self.protocol}_base` | UVM | {self.protocol.upper()} Base Framework Test |
| `{self.protocol}_read` | UVM | {self.protocol.upper()} Read Operations Test |
| `{self.protocol}_write` | UVM | {self.protocol.upper()} Write Operations Test |
| `{self.protocol}_mixed` | UVM | {self.protocol.upper()} Mixed Operations Test |
| `simple_tb` | Non-UVM | Simple Testbench |

## Generated UVM Components

This project includes a complete UVM verification environment with:

- **Transaction Class**: `{self.protocol}_transaction` with randomization constraints
- **Driver**: `{self.protocol}_driver` for stimulus generation
- **Monitor**: `{self.protocol}_monitor` for protocol observation
- **Sequencer**: `{self.protocol}_sequencer` for sequence management
- **Agent**: `{self.protocol}_agent` combining driver, monitor, and sequencer
- **Environment**: `{self.protocol}_env` with master/slave agents and scoreboard
- **Scoreboard**: `{self.protocol}_scoreboard` for transaction checking
- **Sequences**: Base, read, and write sequences
- **Tests**: Multiple test scenarios for comprehensive verification

## TODO

- [ ] Implement {self.protocol.upper()} protocol signals
- [ ] Add comprehensive test scenarios
- [ ] Implement driver and monitor logic
- [ ] Add scoreboard verification
- [ ] Create advanced test sequences

## References

- [UVM 1.2 User Guide](https://www.accellera.org/images/downloads/standards/uvm/uvm_users_guide_1.2.pdf)
- [DSIMtuto Reference Project](https://github.com/MameMame777/DSIMtuto)
"""
        self._write_file("", "README.md", readme_content)
        
        # UVM guide template
        uvm_guide_content = f"""# {self.protocol.upper()} UVM Verification Environment Guide

## Overview

This document explains the UVM verification environment for the {self.project_name} project.

## Architecture Overview

### Class Hierarchy

```text
uvm_test
└── {self.protocol}_base_test

uvm_env
└── {self.protocol}_env
    ├── {self.protocol}_agent
    └── {self.protocol}_scoreboard

uvm_agent
└── {self.protocol}_agent
    ├── {self.protocol}_driver
    ├── {self.protocol}_monitor
    └── {self.protocol}_sequencer

uvm_sequence_item
└── {self.protocol}_transaction
```

## TODO

- [ ] Define test scenarios
- [ ] Implement verification components
- [ ] Add coverage analysis
- [ ] Document best practices

## Generated from DSIMtuto template

This guide is based on the successful DSIMtuto project structure.
Customize it according to your specific verification requirements.
"""
        self._write_file("docs", f"{self.protocol}_verification_guide.md", uvm_guide_content)
    
    def generate_github_actions(self):
        """Generate GitHub Actions CI/CD template"""
        
        ci_workflow_content = f"""name: {self.project_name} CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  lint:
    runs-on: ubuntu-latest
    name: Lint and Style Check
    
    steps:
    - uses: actions/checkout@v3
    
    - name: SystemVerilog Lint
      run: |
        echo "TODO: Add SystemVerilog linting"
        # Add verilator, sv-parser, or other linting tools
    
    - name: Markdown Lint
      uses: articulate/actions-markdownlint@v1
      with:
        config: .markdownlint.json
        files: '**/*.md'

  test:
    runs-on: ubuntu-latest
    name: Verification Tests
    needs: lint
    
    strategy:
      matrix:
        test: ['{self.protocol}_base', 'simple_tb']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Test Environment
      run: |
        echo "TODO: Setup DSIM simulator"
        echo "TODO: Setup UVM environment"
    
    - name: Run Test - ${{{{ matrix.test }}}}
      run: |
        echo "TODO: Execute test ${{{{ matrix.test }}}}"
        # cd sim/run && ./run.bat ${{{{ matrix.test }}}}
    
    - name: Upload Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: test-results-${{{{ matrix.test }}}}
        path: sim/output/
"""
        self._write_file(".github/workflows", "ci.yml", ci_workflow_content)
    
    def generate_gitignore(self):
        """Generate .gitignore file"""
        
        gitignore_content = f"""# {self.project_name} - Generated .gitignore

# Simulation outputs
sim/output/*.vcd
sim/output/*.mxd
sim/output/*.log
sim/output/*.db
sim/output/dsim_work/
sim/output/exec/

# Temporary files
*.tmp
*.temp
*~
.DS_Store

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS generated files
Thumbs.db
ehthumbs.db

# Build artifacts
build/
obj/
*.o
*.so

# Logs
*.log
log/

# Coverage reports
coverage/
*.ucdb
"""
        self._write_file("", ".gitignore", gitignore_content)
    
    def _write_file(self, directory, filename, content):
        """Helper method to write file content"""
        file_path = self.base_path / directory / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Generated: {file_path}")
    
    def generate_project(self):
        """Generate complete project template"""
        print(f"Generating {self.project_name} project template...")
        print(f"Protocol: {self.protocol.upper()}")
        print(f"Simulator: {self.simulator.upper()}")
        print("-" * 50)
        
        # Track generated files
        self.generated_files = []
        
        self.create_directory_structure()
        self.generate_rtl_templates()
        uvm_files = self.generate_uvm_templates()
        self.generate_simulation_config()
        self.generate_documentation()
        self.generate_github_actions()
        self.generate_gitignore()
        
        print("-" * 50)
        print(f"✅ Project template '{self.project_name}' generated successfully!")
        print(f"📁 Location: {self.base_path.absolute()}")
        print(f"🔧 Generated comprehensive UVM verification environment for {self.protocol.upper()}")
        print("\nGenerated Components:")
        print("- Transaction class with constraints and utility methods")
        print("- Driver for stimulus generation")
        print("- Monitor for protocol observation") 
        print("- Sequencer for sequence management")
        print("- Agent combining all components")
        print("- Environment with scoreboard")
        print("- Multiple test sequences (base, read, write, mixed)")
        print("- Complete testbench infrastructure")
        print("\nNext steps:")
        print("1. Customize RTL modules for your specific design")
        print("2. Update interface signals to match your protocol")
        print("3. Implement protocol-specific driving logic in driver")
        print("4. Add transaction constraints for your use case")
        print("5. Configure simulation environment")
        print("6. Run tests: cd sim/run && .\\run.bat [test_name]")
        print("7. Set up CI/CD pipeline")

def main():
    parser = argparse.ArgumentParser(description='Generate FPGA verification project template')
    parser.add_argument('project_name', help='Name of the project')
    parser.add_argument('--protocol', default='AXI4', help='Protocol type (default: AXI4)')
    parser.add_argument('--simulator', default='dsim', help='Simulator type (default: dsim)')
    
    args = parser.parse_args()
    
    generator = ProjectTemplateGenerator(
        project_name=args.project_name,
        protocol=args.protocol,
        simulator=args.simulator
    )
    
    generator.generate_project()

if __name__ == "__main__":
    main()
