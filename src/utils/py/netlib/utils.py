from scapy.packet import Packet


def get_packet_layers(packet: Packet):
    """Unwraps packet at all layers, returning all layers (including payloads)

    https://stackoverflow.com/a/13550975
    """
    counter = 0
    while True:
        layer = packet.getlayer(counter)
        if layer is None:
            break

        yield layer
        counter += 1

