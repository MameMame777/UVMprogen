#!/usr/bin/env python3
"""
UVM Component Generator
Generates standard UVM verification components based on templates
"""

import argparse
from pathlib import Path
from datetime import datetime

class UVMComponentGenerator:
    def __init__(self, protocol, output_dir="."):
        self.protocol = protocol.lower()
        self.output_dir = Path(output_dir)
        self.class_prefix = self.protocol
        
    def generate_transaction(self):
        """Generate UVM transaction class"""
        content = f'''// {self.protocol.upper()} Transaction Class
// File: {self.protocol}_transaction.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_transaction extends uvm_sequence_item;
    `uvm_object_utils({self.class_prefix}_transaction)

    // Transaction fields - customize for your protocol
    rand bit [31:0] addr;
    rand bit [31:0] data;
    rand bit [3:0]  strb;
    bit [1:0]       resp;
    
    // Transaction type
    typedef enum bit [1:0] {{
        READ  = 2'b00,
        WRITE = 2'b01
    }} trans_type_e;
    
    rand trans_type_e trans_type;
    
    // Constraints
    constraint addr_align_c {{
        addr[1:0] == 2'b00; // Word aligned addresses
    }}
    
    constraint data_range_c {{
        data != 32'h0; // Avoid zero data for better coverage
    }}
    
    function new(string name = "{self.class_prefix}_transaction");
        super.new(name);
    endfunction
    
    // Standard UVM methods
    virtual function void do_copy(uvm_object rhs);
        {self.class_prefix}_transaction rhs_t;
        if (!$cast(rhs_t, rhs)) begin
            `uvm_fatal(get_type_name(), "Cast failed in do_copy")
        end
        super.do_copy(rhs);
        this.addr = rhs_t.addr;
        this.data = rhs_t.data;
        this.strb = rhs_t.strb;
        this.resp = rhs_t.resp;
        this.trans_type = rhs_t.trans_type;
    endfunction
    
    virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        {self.class_prefix}_transaction rhs_t;
        if (!$cast(rhs_t, rhs)) return 0;
        return (super.do_compare(rhs, comparer) &&
                (this.addr == rhs_t.addr) &&
                (this.data == rhs_t.data) &&
                (this.strb == rhs_t.strb) &&
                (this.resp == rhs_t.resp) &&
                (this.trans_type == rhs_t.trans_type));
    endfunction
    
    virtual function string convert2string();
        return $sformatf("addr=0x%0h, data=0x%0h, strb=0x%0h, resp=%0d, type=%s",
                        addr, data, strb, resp, trans_type.name());
    endfunction

endclass
'''
        return self._write_file("verification/common", f"{self.protocol}_transaction.sv", content)
    
    def generate_driver(self):
        """Generate UVM driver class"""
        content = f'''// {self.protocol.upper()} Driver Class
// File: {self.protocol}_driver.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_driver extends uvm_driver#({self.class_prefix}_transaction);
    `uvm_component_utils({self.class_prefix}_driver)
    
    // Virtual interface
    virtual {self.protocol}_if vif;
    
    function new(string name = "{self.class_prefix}_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get virtual interface from config database
        if (!uvm_config_db#(virtual {self.protocol}_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal(get_type_name(), "Virtual interface not found in config database")
        end
    endfunction
    
    virtual task run_phase(uvm_phase phase);
        {self.class_prefix}_transaction req;
        
        // Initialize interface
        initialize_interface();
        
        forever begin
            // Get next transaction from sequencer
            seq_item_port.get_next_item(req);
            
            `uvm_info(get_type_name(), $sformatf("Driving transaction: %s", req.convert2string()), UVM_HIGH)
            
            // Drive transaction to interface
            drive_transaction(req);
            
            // Indicate completion to sequencer
            seq_item_port.item_done();
        end
    endtask
    
    virtual task initialize_interface();
        // Initialize interface signals to default values
        // TODO: Customize for your protocol
        vif.valid <= 1'b0;
        vif.ready <= 1'b0;
        wait(!vif.reset);
        @(posedge vif.clk);
    endtask
    
    virtual task drive_transaction({self.class_prefix}_transaction trans);
        // TODO: Implement protocol-specific driving logic
        case (trans.trans_type)
            {self.class_prefix}_transaction::READ: begin
                drive_read(trans);
            end
            {self.class_prefix}_transaction::WRITE: begin
                drive_write(trans);
            end
        endcase
    endtask
    
    virtual task drive_read({self.class_prefix}_transaction trans);
        // TODO: Implement read transaction driving
        @(posedge vif.clk);
        vif.valid <= 1'b1;
        vif.addr <= trans.addr;
        // Add protocol-specific signals
        wait(vif.ready);
        @(posedge vif.clk);
        vif.valid <= 1'b0;
    endtask
    
    virtual task drive_write({self.class_prefix}_transaction trans);
        // TODO: Implement write transaction driving
        @(posedge vif.clk);
        vif.valid <= 1'b1;
        vif.addr <= trans.addr;
        vif.data <= trans.data;
        vif.strb <= trans.strb;
        // Add protocol-specific signals
        wait(vif.ready);
        @(posedge vif.clk);
        vif.valid <= 1'b0;
    endtask

endclass
'''
        return self._write_file(f"verification/uvm/agents/{self.protocol}_agent", f"{self.protocol}_driver.sv", content)
    
    def generate_monitor(self):
        """Generate UVM monitor class"""
        content = f'''// {self.protocol.upper()} Monitor Class
// File: {self.protocol}_monitor.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_monitor extends uvm_monitor;
    `uvm_component_utils({self.class_prefix}_monitor)
    
    // Virtual interface
    virtual {self.protocol}_if vif;
    
    // Analysis port for sending transactions to scoreboard
    uvm_analysis_port#({self.class_prefix}_transaction) ap;
    
    function new(string name = "{self.class_prefix}_monitor", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get virtual interface from config database
        if (!uvm_config_db#(virtual {self.protocol}_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal(get_type_name(), "Virtual interface not found in config database")
        end
        
        // Create analysis port
        ap = new("ap", this);
    endfunction
    
    virtual task run_phase(uvm_phase phase);
        {self.class_prefix}_transaction trans;
        
        forever begin
            // Wait for transaction on interface
            wait_for_transaction();
            
            // Collect transaction data
            trans = {self.class_prefix}_transaction::type_id::create("trans");
            collect_transaction(trans);
            
            `uvm_info(get_type_name(), $sformatf("Collected transaction: %s", trans.convert2string()), UVM_HIGH)
            
            // Send transaction to analysis port
            ap.write(trans);
        end
    endtask
    
    virtual task wait_for_transaction();
        // TODO: Implement protocol-specific transaction detection
        @(posedge vif.clk);
        while (!(vif.valid && vif.ready)) begin
            @(posedge vif.clk);
        end
    endtask
    
    virtual task collect_transaction({self.class_prefix}_transaction trans);
        // TODO: Implement protocol-specific data collection
        trans.addr = vif.addr;
        trans.data = vif.data;
        trans.strb = vif.strb;
        trans.resp = vif.resp;
        
        // Determine transaction type based on interface signals
        if (vif.write_enable) begin
            trans.trans_type = {self.class_prefix}_transaction::WRITE;
        end else begin
            trans.trans_type = {self.class_prefix}_transaction::READ;
        end
    endtask

endclass
'''
        return self._write_file(f"verification/uvm/agents/{self.protocol}_agent", f"{self.protocol}_monitor.sv", content)
    
    def generate_sequencer(self):
        """Generate UVM sequencer class"""
        content = f'''// {self.protocol.upper()} Sequencer Class
// File: {self.protocol}_sequencer.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_sequencer extends uvm_sequencer#({self.class_prefix}_transaction);
    `uvm_component_utils({self.class_prefix}_sequencer)
    
    function new(string name = "{self.class_prefix}_sequencer", uvm_component parent = null);
        super.new(name, parent);
    endfunction

endclass
'''
        return self._write_file(f"verification/uvm/agents/{self.protocol}_agent", f"{self.protocol}_sequencer.sv", content)
    
    def generate_sequences(self):
        """Generate UVM sequence classes"""
        
        # Base sequence
        base_seq_content = f'''// {self.protocol.upper()} Base Sequence Class
// File: {self.protocol}_base_seq.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_base_seq extends uvm_sequence#({self.class_prefix}_transaction);
    `uvm_object_utils({self.class_prefix}_base_seq)
    
    function new(string name = "{self.class_prefix}_base_seq");
        super.new(name);
    endfunction
    
    virtual task body();
        // Base sequence implementation
        `uvm_info(get_type_name(), "Starting base sequence", UVM_MEDIUM)
    endtask

endclass
'''
        
        # Read sequence
        read_seq_content = f'''// {self.protocol.upper()} Read Sequence Class
// File: {self.protocol}_read_seq.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_read_seq extends {self.class_prefix}_base_seq;
    `uvm_object_utils({self.class_prefix}_read_seq)
    
    rand int num_reads = 5;
    
    constraint num_reads_c {{
        num_reads inside {{[1:10]}};
    }}
    
    function new(string name = "{self.class_prefix}_read_seq");
        super.new(name);
    endfunction
    
    virtual task body();
        {self.class_prefix}_transaction req;
        
        `uvm_info(get_type_name(), $sformatf("Starting read sequence with %0d reads", num_reads), UVM_MEDIUM)
        
        for (int i = 0; i < num_reads; i++) begin
            req = {self.class_prefix}_transaction::type_id::create("req");
            
            start_item(req);
            if (!req.randomize() with {{
                trans_type == {self.class_prefix}_transaction::READ;
            }}) begin
                `uvm_fatal(get_type_name(), "Randomization failed")
            end
            finish_item(req);
            
            `uvm_info(get_type_name(), $sformatf("Read %0d: %s", i+1, req.convert2string()), UVM_HIGH)
        end
    endtask

endclass
'''
        
        # Write sequence
        write_seq_content = f'''// {self.protocol.upper()} Write Sequence Class
// File: {self.protocol}_write_seq.sv
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

`include "uvm_macros.svh"
import uvm_pkg::*;

class {self.class_prefix}_write_seq extends {self.class_prefix}_base_seq;
    `uvm_object_utils({self.class_prefix}_write_seq)
    
    rand int num_writes = 5;
    
    constraint num_writes_c {{
        num_writes inside {{[1:10]}};
    }}
    
    function new(string name = "{self.class_prefix}_write_seq");
        super.new(name);
    endfunction
    
    virtual task body();
        {self.class_prefix}_transaction req;
        
        `uvm_info(get_type_name(), $sformatf("Starting write sequence with %0d writes", num_writes), UVM_MEDIUM)
        
        for (int i = 0; i < num_writes; i++) begin
            req = {self.class_prefix}_transaction::type_id::create("req");
            
            start_item(req);
            if (!req.randomize() with {{
                trans_type == {self.class_prefix}_transaction::WRITE;
            }}) begin
                `uvm_fatal(get_type_name(), "Randomization failed")
            end
            finish_item(req);
            
            `uvm_info(get_type_name(), $sformatf("Write %0d: %s", i+1, req.convert2string()), UVM_HIGH)
        end
    endtask

endclass
'''
        
        # Write files
        files = [
            ("verification/uvm/sequences", f"{self.protocol}_base_seq.sv", base_seq_content),
            ("verification/uvm/sequences", f"{self.protocol}_read_seq.sv", read_seq_content),
            ("verification/uvm/sequences", f"{self.protocol}_write_seq.sv", write_seq_content)
        ]
        
        return [self._write_file(dir_path, filename, content) for dir_path, filename, content in files]
    
    def _write_file(self, directory, filename, content):
        """Helper method to write file content"""
        file_path = self.output_dir / directory / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Generated: {file_path}")
        return file_path
    
    def generate_all_components(self):
        """Generate all UVM components"""
        print(f"Generating UVM components for {self.protocol.upper()} protocol...")
        print("-" * 50)
        
        generated_files = []
        generated_files.append(self.generate_transaction())
        generated_files.append(self.generate_driver())
        generated_files.append(self.generate_monitor())
        generated_files.append(self.generate_sequencer())
        generated_files.extend(self.generate_sequences())
        
        print("-" * 50)
        print(f"✅ Generated {len(generated_files)} UVM component files")
        print("\nNext steps:")
        print("1. Customize interface signals for your protocol")
        print("2. Implement protocol-specific driving logic")
        print("3. Add transaction constraints")
        print("4. Implement scoreboard checking logic")
        
        return generated_files

def main():
    parser = argparse.ArgumentParser(description='Generate UVM verification components')
    parser.add_argument('protocol', help='Protocol name (e.g., AXI4, PCIe, UART)')
    parser.add_argument('--output-dir', default='.', help='Output directory (default: current)')
    
    args = parser.parse_args()
    
    generator = UVMComponentGenerator(args.protocol, args.output_dir)
    generator.generate_all_components()

if __name__ == "__main__":
    main()
