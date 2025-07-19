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
            
            # Implementation directories (配置配線用)
            "impl",
            "impl/constraints",
            "impl/scripts",
            "impl/reports",
            "impl/bitstream",
            "impl/projects",
            "impl/ip",
            "impl/bd",  # Block Design
            
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
    
    def generate_implementation_templates(self):
        """Generate implementation (配置配線) template files"""
        
        # Constraints file template
        constraints_content = f"""# {self.project_name} - Implementation Constraints
# File: {self.project_name.lower()}_constraints.xdc
# Generated: {datetime.now().strftime('%Y-%m-%d')}

# ================================================================================
# Clock Constraints
# ================================================================================

# Primary clock constraint
create_clock -period 10.000 -name sys_clk -waveform {{0.000 5.000}} [get_ports clk]

# Generated clocks (if any)
# create_generated_clock -name clk_div2 -source [get_ports clk] -divide_by 2 [get_pins clk_div_inst/Q]

# ================================================================================
# Input/Output Constraints
# ================================================================================

# Input delay constraints
set_input_delay -clock [get_clocks sys_clk] -min 2.000 [get_ports {{reset}}]
set_input_delay -clock [get_clocks sys_clk] -max 8.000 [get_ports {{reset}}]

# Output delay constraints
# set_output_delay -clock [get_clocks sys_clk] -min 1.000 [get_ports {{output_port}}]
# set_output_delay -clock [get_clocks sys_clk] -max 6.000 [get_ports {{output_port}}]

# ================================================================================
# Physical Constraints (Board-specific)
# ================================================================================

# Pin assignments (customize for your board)
# set_property PACKAGE_PIN E3 [get_ports clk]
# set_property IOSTANDARD LVCMOS33 [get_ports clk]

# set_property PACKAGE_PIN C12 [get_ports reset]
# set_property IOSTANDARD LVCMOS33 [get_ports reset]

# ================================================================================
# Timing Exceptions
# ================================================================================

# False paths
# set_false_path -from [get_clocks clk1] -to [get_clocks clk2]

# Maximum delay constraints
# set_max_delay 8.000 -from [get_ports input_port] -to [get_ports output_port]

# ================================================================================
# Implementation Directives
# ================================================================================

# Synthesis directives
# set_property KEEP_HIERARCHY SOFT [get_cells instance_name]

# Place and Route directives
# set_property LOC SLICE_X0Y0 [get_cells instance_name]

# TODO: Add board-specific constraints
# TODO: Add {self.protocol.upper()} protocol-specific timing constraints
"""
        self._write_file("impl/constraints", f"{self.project_name.lower()}_constraints.xdc", constraints_content)
        
        # Vivado TCL script template
        vivado_script_content = f"""# {self.project_name} - Vivado Implementation Script
# File: build_project.tcl
# Generated: {datetime.now().strftime('%Y-%m-%d')}

# ================================================================================
# Project Configuration
# ================================================================================

set project_name "{self.project_name.lower()}"
set project_dir "./projects"
set part_name "xc7a35tcpg236-1"  # Default part - customize for your board
set board_part ""  # Set board part if using a development board

# Create project directory
file mkdir $project_dir

# ================================================================================
# Create Vivado Project
# ================================================================================

# Create project
create_project $project_name $project_dir/$project_name -part $part_name -force

# Set board part if specified
if {{$board_part != ""}} {{
    set_property board_part $board_part [current_project]
}}

# ================================================================================
# Add Source Files
# ================================================================================

# Add RTL files
add_files -fileset sources_1 [glob ../rtl/*.sv]
add_files -fileset sources_1 [glob ../rtl/interfaces/*.sv]

# Add constraint files
add_files -fileset constrs_1 [glob ../constraints/*.xdc]

# Set top module
set_property top {self.project_name.title()}_Core [current_fileset]

# ================================================================================
# IP Management
# ================================================================================

# Add IP files (if any)
# add_files -fileset sources_1 [glob ../ip/*.xci]

# Upgrade IP (if needed)
# upgrade_ip [get_ips]

# ================================================================================
# Synthesis
# ================================================================================

proc run_synthesis {{}} {{
    global project_name
    
    puts "Starting synthesis for $project_name..."
    
    # Reset synthesis run
    reset_run synth_1
    
    # Launch synthesis
    launch_runs synth_1 -jobs 4
    wait_on_run synth_1
    
    # Check synthesis results
    if {{[get_property PROGRESS [get_runs synth_1]] != "100%"}} {{
        error "Synthesis failed!"
    }}
    
    puts "Synthesis completed successfully"
    
    # Open synthesized design for analysis
    open_run synth_1 -name synth_1
    
    # Generate synthesis reports
    report_timing_summary -file ../reports/synthesis_timing.rpt
    report_utilization -file ../reports/synthesis_utilization.rpt
    report_power -file ../reports/synthesis_power.rpt
}}

# ================================================================================
# Implementation
# ================================================================================

proc run_implementation {{}} {{
    global project_name
    
    puts "Starting implementation for $project_name..."
    
    # Reset implementation runs
    reset_run impl_1
    
    # Launch implementation
    launch_runs impl_1 -jobs 4
    wait_on_run impl_1
    
    # Check implementation results
    if {{[get_property PROGRESS [get_runs impl_1]] != "100%"}} {{
        error "Implementation failed!"
    }}
    
    puts "Implementation completed successfully"
    
    # Open implemented design
    open_run impl_1
    
    # Generate implementation reports
    report_timing_summary -file ../reports/implementation_timing.rpt
    report_utilization -file ../reports/implementation_utilization.rpt
    report_route_status -file ../reports/route_status.rpt
    report_drc -file ../reports/drc.rpt
    report_power -file ../reports/implementation_power.rpt
}}

# ================================================================================
# Bitstream Generation
# ================================================================================

proc generate_bitstream {{}} {{
    global project_name
    
    puts "Generating bitstream for $project_name..."
    
    # Launch bitstream generation
    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1
    
    # Check bitstream generation results
    if {{[get_property PROGRESS [get_runs impl_1]] != "100%"}} {{
        error "Bitstream generation failed!"
    }}
    
    puts "Bitstream generation completed successfully"
    
    # Copy bitstream to output directory
    file copy -force ./projects/$project_name/$project_name.runs/impl_1/$project_name.bit ../bitstream/
    
    puts "Bitstream saved to ../bitstream/$project_name.bit"
}}

# ================================================================================
# Complete Build Flow
# ================================================================================

proc build_all {{}} {{
    run_synthesis
    run_implementation
    generate_bitstream
    
    puts "Complete build flow finished successfully!"
}}

# ================================================================================
# Usage Instructions
# ================================================================================

puts "Vivado build script loaded for {self.project_name}"
puts ""
puts "Available commands:"
puts "  run_synthesis        - Run synthesis only"
puts "  run_implementation   - Run implementation only"
puts "  generate_bitstream   - Generate bitstream only"
puts "  build_all           - Run complete flow"
puts ""
puts "Example usage:"
puts "  vivado -mode tcl -source build_project.tcl -tclargs build_all"
"""
        self._write_file("impl/scripts", "build_project.tcl", vivado_script_content)
        
        # Implementation makefile
        makefile_content = f"""# {self.project_name} - Implementation Makefile
# Generated: {datetime.now().strftime('%Y-%m-%d')}

PROJECT_NAME = {self.project_name.lower()}
VIVADO = vivado
TCL_SCRIPT = scripts/build_project.tcl

# Default target
.PHONY: all
all: bitstream

# Create directories
.PHONY: setup
setup:
	@mkdir -p projects reports bitstream ip bd
	@echo "Implementation directories created"

# Synthesis only
.PHONY: synth
synth: setup
	@echo "Running synthesis..."
	@cd scripts && $(VIVADO) -mode batch -source build_project.tcl -tclargs run_synthesis
	@echo "Synthesis completed"

# Implementation only
.PHONY: impl
impl: setup
	@echo "Running implementation..."
	@cd scripts && $(VIVADO) -mode batch -source build_project.tcl -tclargs run_implementation
	@echo "Implementation completed"

# Bitstream generation
.PHONY: bitstream
bitstream: setup
	@echo "Running complete build flow..."
	@cd scripts && $(VIVADO) -mode batch -source build_project.tcl -tclargs build_all
	@echo "Bitstream generation completed"

# Interactive mode
.PHONY: gui
gui: setup
	@echo "Opening Vivado GUI..."
	@cd scripts && $(VIVADO) -mode gui -source build_project.tcl

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf projects/* reports/* bitstream/*
	@echo "Clean completed"

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  setup     - Create implementation directories"
	@echo "  synth     - Run synthesis only"
	@echo "  impl      - Run implementation only"
	@echo "  bitstream - Run complete flow and generate bitstream"
	@echo "  gui       - Open Vivado GUI"
	@echo "  clean     - Clean build artifacts"
	@echo "  help      - Show this help"

# Board-specific targets (examples)
.PHONY: arty
arty: BOARD_PART = digilentinc.com:arty-a7-35:part0:1.0
arty: bitstream

.PHONY: basys3
basys3: BOARD_PART = digilentinc.com:basys3:part0:1.1
basys3: bitstream
"""
        self._write_file("impl", "Makefile", makefile_content)
        
        # IP catalog template
        ip_readme_content = f"""# {self.project_name} - IP Catalog

## Overview

This directory contains IP cores used in the {self.project_name} project.

## IP Core Management

### Adding New IP Cores

1. **Using Vivado IP Catalog:**
   ```tcl
   # In Vivado TCL console
   create_ip -name clk_wiz -vendor xilinx.com -library ip -module_name clk_gen
   ```

2. **From Third-Party Sources:**
   - Place IP files (.xci, .xcix) in this directory
   - Update the build script to include new IP cores

### IP Core Examples

- **Clock Management:** Clock wizard, MMCM, PLL cores
- **Memory Controllers:** MIG (Memory Interface Generator)
- **Communication:** AXI interconnect, protocol converters
- **DSP:** FIR filters, FFT cores
- **Custom IP:** Project-specific IP blocks

### IP Upgrade Process

When migrating to newer Vivado versions:

```tcl
# Upgrade all IP cores
upgrade_ip [get_ips]
```

## TODO

- [ ] Add clock generation IP for {self.protocol.upper()} protocol
- [ ] Configure memory interface if needed
- [ ] Add protocol-specific IP cores
- [ ] Create custom IP for {self.project_name}
"""
        self._write_file("impl/ip", "README.md", ip_readme_content)
        
        # Block Design template
        bd_readme_content = f"""# {self.project_name} - Block Design

## Overview

This directory contains Vivado Block Design (.bd) files for the {self.project_name} project.

## Block Design Usage

### Creating Block Designs

1. **In Vivado GUI:**
   - File → Create Block Design
   - Add IP cores and interconnects
   - Export to TCL for version control

2. **TCL Script Generation:**
   ```tcl
   # Export block design to TCL
   write_bd_tcl -force ../bd/system_bd.tcl
   ```

### Block Design Examples

- **System Integration:** Top-level system with processors
- **Protocol Bridges:** {self.protocol.upper()} to other protocols
- **Memory Subsystems:** DDR controllers with caches
- **Processing Pipelines:** DSP chains and data flows

### Integration with RTL

Block designs can be integrated with custom RTL:

```systemverilog
// Instantiate block design in RTL
system_wrapper system_i (
    .clk(clk),
    .reset(reset),
    // Other ports...
);
```

## Best Practices

- Keep block designs modular
- Use hierarchical designs for complex systems
- Export TCL scripts for version control
- Document interface specifications
- Use consistent naming conventions

## TODO

- [ ] Create system block design for {self.project_name}
- [ ] Add {self.protocol.upper()} interconnect
- [ ] Integrate with RTL modules
- [ ] Add debugging interfaces (ILA, VIO)
"""
        self._write_file("impl/bd", "README.md", bd_readme_content)
    
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
├─ impl/                  # Implementation (配置配線)
│  ├─ constraints/       # Timing and physical constraints
│  ├─ scripts/           # Build scripts (TCL)
│  ├─ reports/           # Implementation reports
│  ├─ bitstream/         # Generated bitstreams
│  ├─ projects/          # Vivado project files
│  ├─ ip/                # IP cores
│  └─ bd/                # Block designs
├─ tools/                # Utility scripts
├─ docs/                 # Documentation
└─ .github/workflows/    # CI/CD pipeline
```

## Quick Start

### Verification Flow

Navigate to the `sim/run` directory and use the unified test execution system:

```bash
cd sim/run

# Show all available test configurations
.\\run.bat

# Execute a specific test
.\\run.bat {self.protocol}_base
```

### Implementation Flow

Navigate to the `impl` directory and use the build system:

```bash
cd impl

# Run complete implementation flow
make bitstream

# Run synthesis only
make synth

# Run implementation only
make impl

# Open Vivado GUI
make gui

# Clean build artifacts
make clean
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

### RTL Design
- [ ] Implement {self.protocol.upper()} protocol signals
- [ ] Add comprehensive test scenarios
- [ ] Implement driver and monitor logic
- [ ] Add scoreboard verification
- [ ] Create advanced test sequences

### Implementation
- [ ] Add board-specific pin constraints
- [ ] Optimize timing constraints for {self.protocol.upper()}
- [ ] Add clock management IP cores
- [ ] Create system block design
- [ ] Implement power optimization
- [ ] Add debugging interfaces (ILA, VIO)

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

# Implementation outputs
impl/projects/*/
impl/reports/*.rpt
impl/reports/*.log
impl/bitstream/*.bit
impl/bitstream/*.bin
impl/bitstream/*.mcs

# Vivado files
*.jou
*.log
*.str
*.xpr
*.cache/
*.hw/
*.ip_user_files/
*.runs/
*.sim/
*.srcs/

# IP cores
*.xci
*.xcix

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
        self.generate_implementation_templates()
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
        print("7. Add board-specific constraints in impl/constraints/")
        print("8. Run implementation: cd impl && make bitstream")
        print("9. Set up CI/CD pipeline")

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
