`mqnic_core_axi` is the lowest level with available testbench

`mqnic_core_pcie_us` apparently looks a bit easier, a bit higher-level, which is nice, and should be easier to understand

> What does corundum use its interfaces for?

1. figure out what the TB does/is/uses/etc.
2. modify the existing tb, test it out a bit, have some fun
3. see if you can get arbitrary packets sending/receiving for a single DUT
4. see if you can set up a test that uses multiple interconnected TB instances
  - idk if docker containers would be necessary, since it feels like that might just be adding more complexity for no reason
    - instead instantiate multiple TB instances?
    - put them in a list
    - iterate through, or create permutations, etc.
    - that way, I can keep it all in one testbench, in one cocotb instance
    - and can make multiple tests in this one file, too
  - get them to send packets back and forth based on some arbitrary program, idk
5. see if you can automate the scaling nonsense to scale things arbitrarily
  - i.e. auto-scaling test programs/procedures
  - or maybe a better use of your time would be refactoring the system to make writing new tests easier
    - since I imagine some of these things will be quite repetitive, and since I can't write all of the tests that my successor will need, just guide them in the write direction, it might be nice to help them get into it all easier
6. If you have a _lot_ of free time, you could set up a Tonic DUT
   - Tonic at the centre, surrounded by the Corundum infrastructure doing all the bits that Tonic can't
   - I think this could amount to slotting Tonic in [here](https://github.com/corundum/corundum/wiki/Future-of-Corundum#application-logic)

That's it, if you can do up to 4 or 5 by the deadline, that would be pretty good, if you manage to finish 6, that would be amazing
