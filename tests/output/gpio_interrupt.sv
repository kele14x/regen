//*****************************************************************************
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//*****************************************************************************
`timescale 1 ns / 1 ps `default_nettype none

module gpio_interrupt_regs #(
    parameter C_ADDR_WIDTH = 9,
    parameter C_DATA_WIDTH = 32
) (
    // AXI4-Lite Slave
    input var                       aclk,
    input var                       aresetn,
    //
    input var  [  C_ADDR_WIDTH-1:0] s_axi_awaddr,
    input var  [               2:0] s_axi_awprot,
    input var                       s_axi_awvalid,
    output var                      s_axi_awready,
    //
    input var  [  C_DATA_WIDTH-1:0] s_axi_wdata,
    input var  [C_DATA_WIDTH/8-1:0] s_axi_wstrb,
    input var                       s_axi_wvalid,
    output var                      s_axi_wready,
    //
    output var [               1:0] s_axi_bresp,
    output var                      s_axi_bvalid,
    input var                       s_axi_bready,
    //
    input var  [  C_ADDR_WIDTH-1:0] s_axi_araddr,
    input var  [               2:0] s_axi_arprot,
    input var                       s_axi_arvalid,
    output var                      s_axi_arready,
    //
    output var [  C_DATA_WIDTH-1:0] s_axi_rdata,
    output var [               1:0] s_axi_rresp,
    output var                      s_axi_rvalid,
    input var                       s_axi_rready,
    // IRQ Ports
    // Register GPIO_STAT
    output var gpio_stat_irq,
    // Register Ports
    // Field GPIO_DATA.GPIO_DATA_VAL
    input var [31:0] gpio_data_val_in,
    output var [31:0] gpio_data_val_out,
    // Field GPIO_TRI.GPIO_TRI_VAL
    output var [31:0] gpio_tri_val,
    // Field GPIO2_DATA.GPIO2_DATA_VAL
    input var [31:0] gpio2_data_val_in,
    output var [31:0] gpio2_data_val_out,
    // Field GPIO2_TRI.GPIO2_TRI_VAL
    output var [31:0] gpio2_tri_val,
    // Field GPIO_STAT.GPIO_STAT_CH0
    input var gpio_stat_ch0,
    // Field GPIO_STAT.GPIO_STAT_CH1
    input var gpio_stat_ch1
);

  // synthesis translate_off
  initial begin
    assert ((C_DATA_WIDTH == 32) || (C_DATA_WIDTH == 64))
      else $error("AXI-4 Lite interface only support C_DATA_WIDTH=32 or 64");
  end
  // synthesis translate_on

  // RRESP/BRESP
  localparam logic [1:0] RespOkey   = 2'b00;  //   OKAY, normal access success
  localparam logic [1:0] RespExokay = 2'b01;  // EXOKAY, exclusive access success
  localparam logic [1:0] RespSlverr = 2'b10;  // SLVERR, slave error
  localparam logic [1:0] RespDecerr = 2'b11;  // DECERR, decoder error


  // Write State Machine
  //====================

  // Write Iteration Interval = 3+ (back-to-back write transaction)
  // Write Latency = 3+ (from AWADDR/WDATA transaction to data appear on port)

  typedef enum int {
    S_WRRST , // in reset
    S_WRIDLE, // idle, waiting for both write address and write data
    S_WRADDR, // write data is provided, waiting for write address
    S_WRDATA, // write address is provided, waiting for write data
    S_WRREQ,  // set wr_req,
    S_WRDEC,  // writer decoding
    S_WRRESP  // `wr_ack` is assert, response to axi master
  } wr_state_t;

  wr_state_t wr_state, wr_state_next;

  logic wr_valid, wr_addr_valid, wr_data_valid;

  logic [C_DATA_WIDTH/8-1:0] wr_be;
  logic [  C_ADDR_WIDTH-3:0] wr_addr;
  logic [  C_DATA_WIDTH-1:0] wr_data;

  logic                      wr_req;
  logic                      wr_ack;


  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      wr_state <= S_WRRST;
    end else begin
      wr_state <= wr_state_next;
    end
  end

  always_comb begin
    case (wr_state)
      S_WRRST:  wr_state_next = S_WRIDLE;
      S_WRIDLE: wr_state_next = (s_axi_awvalid && s_axi_wvalid) ? S_WRREQ :
                                                   s_axi_awvalid ? S_WRADDR :
                                                   s_axi_wvalid  ? S_WRDATA :
                                                   S_WRIDLE;
      S_WRADDR: wr_state_next = !s_axi_wvalid  ? S_WRADDR : S_WRREQ;
      S_WRDATA: wr_state_next = !s_axi_awvalid ? S_WRDATA : S_WRREQ;
      S_WRREQ:  wr_state_next = S_WRDEC;
      S_WRDEC:  wr_state_next = S_WRRESP;
      S_WRRESP: wr_state_next = !s_axi_bready  ? S_WRRESP : S_WRIDLE;
      default:  wr_state_next = S_WRRST;
    endcase
  end

  assign wr_valid = ((wr_state == S_WRIDLE) && s_axi_awvalid && s_axi_wvalid) ||
      ((wr_state == S_WRADDR) && s_axi_wvalid) ||
      ((wr_state == S_WRDATA) && s_axi_awvalid);

  assign wr_addr_valid = ((wr_state == S_WRIDLE) && s_axi_awvalid) ||
      ((wr_state == S_WRDATA) && s_axi_awvalid);

  assign wr_data_valid = ((wr_state == S_WRIDLE) && s_axi_wvalid) ||
      ((wr_state == S_WRADDR) && s_axi_wvalid);


  // Write Address Channel
  //----------------------

  // We are waiting for both write address and write data, but only write
  // address is provided. Register it for later use.
  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      wr_addr <= 'd0;
    end else if (wr_addr_valid) begin
      wr_addr <= s_axi_awaddr[C_ADDR_WIDTH-1:2];
    end
  end

  // Slave can accept write address if idle, or if only write data is
  // provided.
  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_awready <= 1'b0;
    end else begin
      s_axi_awready <= (wr_state_next == S_WRIDLE || wr_state_next == S_WRDATA);
    end
  end


  // Write Data Channel
  //-------------------

  // We are waiting for both write address and write data, but only write
  // data is provided. Register it for later use.
  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      wr_data <= 'd0;
      wr_be   <= 'd0;
    end else if (wr_data_valid) begin
      wr_data <= s_axi_wdata;
      wr_be   <= s_axi_wstrb;
    end
  end

  // Slave can accpet write data if idle, or if only write address is
  // provided.
  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_wready <= 1'b0;
    end else begin
      s_axi_wready <= (wr_state_next == S_WRIDLE || wr_state_next == S_WRADDR);
    end
  end


  // Write Response Channel
  //-----------------------

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      wr_req <= 1'b0;
    end else begin
      wr_req <= wr_valid;
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_bvalid <= 1'b0;
    end else begin
      s_axi_bvalid <= (wr_state_next == S_WRRESP);
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_bresp <= 0;
    end else if (wr_state == S_WRDEC) begin
      s_axi_bresp <= wr_ack ? RespOkey : RespSlverr;
    end
  end


  // Read State Machine
  //===================

  // Read Iteration Interval = 3 (back-to-back read transaction)
  // Read Latency = 3 (from ARADDR transaction to RDATA transaction)

  typedef enum int {
    S_RDRST ,
    S_RDIDLE,
    S_RDREQ,
    S_RDDEC,
    S_RDRESP
  } rd_state_t;

  rd_state_t rd_state, rd_state_next;

  logic                    rd_valid;

  logic [C_ADDR_WIDTH-3:0] rd_addr;
  logic [C_DATA_WIDTH-1:0] rd_data;

  logic                    rd_req;
  logic                    rd_ack;


  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      rd_state <= S_RDRST;
    end else begin
      rd_state <= rd_state_next;
    end
  end

  always_comb begin
    case(rd_state)
      S_RDRST:  rd_state_next = S_RDIDLE;
      S_RDIDLE: rd_state_next = !s_axi_arvalid ? S_RDIDLE : S_RDREQ;
      S_RDREQ:  rd_state_next = S_RDDEC;
      S_RDDEC:  rd_state_next = S_RDRESP;
      S_RDRESP: rd_state_next = !s_axi_rready  ? S_RDRESP : S_RDIDLE;
      default:  rd_state_next = S_RDRST;
    endcase
  end

  assign rd_valid = (rd_state == S_RDIDLE) && s_axi_arvalid;


  // Read Address Channel
  //---------------------

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      rd_addr <= 'd0;
    end else if (rd_valid) begin
      rd_addr <= s_axi_araddr[C_ADDR_WIDTH-1:2];
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_arready <= 1'b0;
    end else begin
      s_axi_arready <= (rd_state_next == S_RDIDLE);
    end
  end


  // Read Data/Response Channel
  //---------------------------

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      rd_req <= 1'b0;
    end else begin
      rd_req <= rd_valid;
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_rvalid <= 1'b0;
   end else begin
      s_axi_rvalid <= (rd_state_next == S_RDRESP);
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_rdata <= 0;
    end else if (rd_state == S_RDDEC) begin
      s_axi_rdata <= rd_data;
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      s_axi_rresp <= 0;
    end else if (rd_state == S_RDDEC) begin
      s_axi_rresp <= rd_ack ? RespOkey : RespSlverr;
    end
  end


  // Register Model
  //===============

  // GPIO_DATA_VAL @0#0

  logic [31:0] gpio_data_val_ireg;
  logic [31:0] gpio_data_val_oreg;

  always_ff @(posedge aclk) begin
    gpio_data_val_ireg <= gpio_data_val_in;
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_data_val_oreg <= 0;
    end else if (wr_req && wr_addr == 0) begin
      gpio_data_val_oreg <= wr_data[31:0];
    end
  end

  assign gpio_data_val_out = gpio_data_val_oreg;

  // GPIO_DATA @0

  
  // GPIO_TRI_VAL @1#0

  logic [31:0] gpio_tri_val_oreg;

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_tri_val_oreg <= 0;
    end else if (wr_req && wr_addr == 1) begin
      gpio_tri_val_oreg <= wr_data[31:0];
    end
  end

  assign gpio_tri_val = gpio_tri_val_oreg;

  // GPIO_TRI @1

  
  // GPIO2_DATA_VAL @2#0

  logic [31:0] gpio2_data_val_ireg;
  logic [31:0] gpio2_data_val_oreg;

  always_ff @(posedge aclk) begin
    gpio2_data_val_ireg <= gpio2_data_val_in;
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio2_data_val_oreg <= 0;
    end else if (wr_req && wr_addr == 2) begin
      gpio2_data_val_oreg <= wr_data[31:0];
    end
  end

  assign gpio2_data_val_out = gpio2_data_val_oreg;

  // GPIO2_DATA @2

  
  // GPIO2_TRI_VAL @3#0

  logic [31:0] gpio2_tri_val_oreg;

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio2_tri_val_oreg <= 0;
    end else if (wr_req && wr_addr == 3) begin
      gpio2_tri_val_oreg <= wr_data[31:0];
    end
  end

  assign gpio2_tri_val = gpio2_tri_val_oreg;

  // GPIO2_TRI @3

  
  // GPIO_STAT_CH0 @71#0

  logic gpio_stat_ch0_ireg;
  logic gpio_stat_ch0_d;
  logic gpio_stat_ch0_int;
  logic gpio_stat_ch0_trap;
  logic gpio_stat_ch0_mask;
  logic gpio_stat_ch0_force;
  logic gpio_stat_ch0_dbg;
  logic gpio_stat_ch0_trig;

  always_ff @(posedge aclk) begin
    gpio_stat_ch0_ireg <= gpio_stat_ch0;
    gpio_stat_ch0_d    <= gpio_stat_ch0_ireg;
  end

  always_ff @(posedge aclk) begin
    gpio_stat_ch0_int <= gpio_stat_ch0_trap & gpio_stat_ch0_mask;
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch0_trap <= '0;
    end else if (wr_req && wr_addr == 72) begin
      gpio_stat_ch0_trap <= gpio_stat_ch0_trap & ~wr_data[0:0];
    end else begin
      gpio_stat_ch0_trap <= gpio_stat_ch0_trap | gpio_stat_ch0_force |
        (gpio_stat_ch0_ireg & (~gpio_stat_ch0_d | ~gpio_stat_ch0_trig));
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch0_mask <= '0;
    end else if (wr_req && wr_addr == 73) begin
      gpio_stat_ch0_mask <= wr_data[0:0];
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch0_force <= '0;
    end else if (wr_req && wr_addr == 74) begin
      gpio_stat_ch0_force <= wr_data[0:0];
    end else begin
      gpio_stat_ch0_force <= '0;
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch0_trig <= '0;
    end else if (wr_req && wr_addr == 76) begin
      gpio_stat_ch0_trig <= wr_data[0:0];
    end
  end

  // GPIO_STAT_CH1 @71#1

  logic gpio_stat_ch1_ireg;
  logic gpio_stat_ch1_d;
  logic gpio_stat_ch1_int;
  logic gpio_stat_ch1_trap;
  logic gpio_stat_ch1_mask;
  logic gpio_stat_ch1_force;
  logic gpio_stat_ch1_dbg;
  logic gpio_stat_ch1_trig;

  always_ff @(posedge aclk) begin
    gpio_stat_ch1_ireg <= gpio_stat_ch1;
    gpio_stat_ch1_d    <= gpio_stat_ch1_ireg;
  end

  always_ff @(posedge aclk) begin
    gpio_stat_ch1_int <= gpio_stat_ch1_trap & gpio_stat_ch1_mask;
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch1_trap <= '0;
    end else if (wr_req && wr_addr == 72) begin
      gpio_stat_ch1_trap <= gpio_stat_ch1_trap & ~wr_data[1:1];
    end else begin
      gpio_stat_ch1_trap <= gpio_stat_ch1_trap | gpio_stat_ch1_force |
        (gpio_stat_ch1_ireg & (~gpio_stat_ch1_d | ~gpio_stat_ch1_trig));
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch1_mask <= '0;
    end else if (wr_req && wr_addr == 73) begin
      gpio_stat_ch1_mask <= wr_data[1:1];
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch1_force <= '0;
    end else if (wr_req && wr_addr == 74) begin
      gpio_stat_ch1_force <= wr_data[1:1];
    end else begin
      gpio_stat_ch1_force <= '0;
    end
  end

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      gpio_stat_ch1_trig <= '0;
    end else if (wr_req && wr_addr == 76) begin
      gpio_stat_ch1_trig <= wr_data[1:1];
    end
  end

  // GPIO_STAT @71

  always_ff @(posedge aclk) begin
    gpio_stat_irq <= |{gpio_stat_ch0_int, gpio_stat_ch1_int};
  end


  // Write ACK
  //==========

  always_comb begin
    wr_ack = 1'b0;
    if (0 == wr_addr) begin
      wr_ack = 1'b1;
    end
    if (1 == wr_addr) begin
      wr_ack = 1'b1;
    end
    if (2 == wr_addr) begin
      wr_ack = 1'b1;
    end
    if (3 == wr_addr) begin
      wr_ack = 1'b1;
    end
    if (71 <= wr_addr && wr_addr <= 76) begin
      wr_ack = 1'b1;
    end
  end


  // Read Register
  //==============

  always_ff @(posedge aclk) begin
    if (!aresetn) begin
      rd_data <= '0;
    end else if (rd_req) begin
      rd_data <= '0;
      case (rd_addr)
        0: begin
          rd_data[31:0] <= gpio_data_val_ireg;
        end
        1: begin
          rd_data[31:0] <= gpio_tri_val_oreg;
        end
        2: begin
          rd_data[31:0] <= gpio2_data_val_ireg;
        end
        3: begin
          rd_data[31:0] <= gpio2_tri_val_oreg;
        end
        71: begin
          rd_data[0:0] <= gpio_stat_ch0_int;
          rd_data[1:1] <= gpio_stat_ch1_int;
        end
        72: begin
          rd_data[0:0] <= gpio_stat_ch0_trap;
          rd_data[1:1] <= gpio_stat_ch1_trap;
        end
        73: begin
          rd_data[0:0] <= gpio_stat_ch0_mask;
          rd_data[1:1] <= gpio_stat_ch1_mask;
        end
        74: begin
          rd_data[0:0] <= gpio_stat_ch0_force;
          rd_data[1:1] <= gpio_stat_ch1_force;
        end
        75: begin
          rd_data[0:0] <= gpio_stat_ch0_dbg;
          rd_data[1:1] <= gpio_stat_ch1_dbg;
        end
        76: begin
          rd_data[0:0] <= gpio_stat_ch0_trig;
          rd_data[1:1] <= gpio_stat_ch1_trig;
        end
        default: rd_data <= 'hDEADBEEF;
      endcase
    end
  end


  // Read ACK
  //=========

  always_comb begin
    rd_ack = 1'b0;
    if (0 == wr_addr) begin
      rd_ack = 1'b1;
    end
    if (1 == wr_addr) begin
      rd_ack = 1'b1;
    end
    if (2 == wr_addr) begin
      rd_ack = 1'b1;
    end
    if (3 == wr_addr) begin
      rd_ack = 1'b1;
    end
    if (71 <= wr_addr && wr_addr <= 76) begin
      rd_ack = 1'b1;
    end
  end

endmodule

`default_nettype wire
