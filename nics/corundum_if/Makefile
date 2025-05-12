# Copyright 2021 Max Planck Institute for Software Systems, and
# National University of Singapore
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# modified into Makefile by lemon-gith (date:20250509)
# with the help of GPT-4o (via GitHub Copilot)

# Note: Extra Verilator flags can be passed with EXTRA_VFLAGS env var

include mk/subdir_pre.mk
include mk/recipes.mk

dir_corundum := /corundum/
bin_corundum := $(dir_corundum)corundum_verilator
verilator_dir_corundum := ./obj_dir
verilator_src_corundum := $(verilator_dir_corundum)/Vinterface.cpp
verilator_bin_corundum := $(verilator_dir_corundum)/Vinterface

# find rtl/ dirs at all levels, most always nested in a lib/ dir
vsrcs_corundum := $(wildcard $(dir_corundum)rtl/*.v \
	$(dir_corundum)lib/*/rtl/*.v $(dir_corundum)lib/*/lib/*/rtl/*.v)
srcs_corundum := $(addprefix $(dir_corundum),\
	corundum_verilator.cc dma.cc mem.cc)
OBJS := $(srcs_corundum:.cc=.o)

# Makefile variables

base_dir := $(d)./

CPPLINT ?= cpplint
CLANG_TIDY ?= clang-tidy
CLANG_FORMAT ?= clang-format
CFLAGS += -Wall -Wextra -Wno-unused-parameter -O3 -fPIC -std=gnu11 $(EXTRA_CFLAGS)
CXXFLAGS += -Wall -Wextra -Wno-unused-parameter -O3 -fPIC -std=gnu++17 $(EXTRA_CXXFLAGS)
CPPFLAGS += -I$(base_dir)/lib -iquote$(base_dir) $(EXTRA_CPPFLAGS)


# use +1364-2001ext+v to compile `.v` files using Verilog 2001
VFLAGS = +1364-2001ext+v \
	-Wno-WIDTH -Wno-PINMISSING -Wno-LITENDIAN -Wno-IMPLICIT -Wno-SELRANGE \
    -Wno-CASEINCOMPLETE -Wno-UNSIGNED $(EXTRA_VFLAGS)
# EXTRA_VFLAGS allows env-set flags, too ^

# get it to call the rules.mk in lib/
$(eval $(call subdir,lib))

all: $(ALL_ALL)
.DEFAULT_GOAL := all

$(OBJS): CPPFLAGS := $(CPPFLAGS) -I$(dir_corundum)include/

$(verilator_src_corundum): $(vsrcs_corundum)
	verilator $(VFLAGS) --cc -O3 \
		-CFLAGS "-I$(abspath $(lib_dir)) -iquote $(abspath $(base_dir)) -O3 -g -Wall -Wno-maybe-uninitialized" \
		--Mdir $(verilator_dir_corundum) \
		-y $(dir_corundum)rtl \
		-y $(dir_corundum)lib/axi/rtl \
		-y $(dir_corundum)lib/eth/lib/axis/rtl/ \
		-y $(dir_corundum)lib/pcie/rtl \
		$(dir_corundum)rtl/interface.v --exe $(abspath $(srcs_corundum)) \
		  $(abspath $(lib_nicif) $(lib_netif) $(lib_pcie) $(lib_base))

$(verilator_bin_corundum): $(verilator_src_corundum) $(srcs_corundum) \
	$(lib_nicif) $(lib_netif) $(lib_pcie) $(lib_base)
	$(MAKE) -C $(verilator_dir_corundum) -f Vinterface.mk

# just makes a copy of the verilator compiled binary at the 'top level'
$(bin_corundum): $(verilator_bin_corundum)
	cp $< $@

clean:
	rm -rf $(CLEAN_ALL)
	rm -rf $(bin_corundum) $(verilator_dir_corundum) $(OBJS)

.PHONY: all clean

include mk/subdir_post.mk
-include $(DEPS_ALL)

# TODO: fix these Makefiles and get this running in the docker container