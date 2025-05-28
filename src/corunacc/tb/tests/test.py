import cocotb


@cocotb.test()
async def tell_me_the_truth(dut):
    assert True, "well, this was unexpected"


@cocotb.test()
async def tell_me_lies(dut):
    assert False, "well, this was expected"
