`mqnic_core_axi` is the lowest level with available testbench

`mqnic_core_pcie_us` apparently looks a bit easier, a bit higher-level, which is nice, and should be easier to understand

> What does corundum use its interfaces for?

1. figure out what the TB does/is/uses/etc.
2. modify the existing tb, test it out a bit, have some fun
3. see if you can get arbitrary packets sending/receiving for a single DUT
4. see if you can set up a docker compose and interconnect between tb instances
  - should I use RabbitMQ? ([pika](https://www.rabbitmq.com/tutorials/tutorial-one-python) in python)
  - get them to send packets back and forth based on some arbitrary program, idk
5. see if you can write a docker compose or kubernetes nonsense to scale that arbitrarily
6. If you have a _lot_ of free time, you could set up a Tonic DUT
   - Tonic at the centre, surrounded by the Corundum infrastructure doing all the bits that Tonic can't

That's it, if you can do up to 4 or 5 by the deadline, that would be pretty amazing
