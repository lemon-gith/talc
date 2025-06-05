#include <iostream>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <linux/if_tun.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <netinet/ip.h>
#include <netinet/ether.h>
#include <stdlib.h>


class TapInterface {
public:
    TapInterface(const std::string& dev_name = "tap0") : fd_(-1), if_name_(dev_name) {
        createTap();
        tapUp();
    }

    ~TapInterface() {
        if (fd_ != -1) {
            close(fd_);
        }
    }

    int readPacket(char* buffer, int size) {
        return read(fd_, buffer, size);
    }

    int writePacket(const char* buffer, int size) {
        return write(fd_, buffer, size);
    }

    std::string getInterfaceName() const {
        return if_name_;
    }

private:
    int fd_;
    std::string if_name_;

    void createTap() {
        struct ifreq ifr;
        int err;

        // Open the clone device
        if ((fd_ = open("/dev/net/tun", O_RDWR)) < 0) {
            perror("Opening /dev/net/tun");
            exit(1);
        }

        // Clear the structure
        memset(&ifr, 0, sizeof(ifr));

        // Flags: IFF_TAP means TAP device, no packet information (no IFF_NO_PI means packet info)
        ifr.ifr_flags = IFF_TAP | IFF_NO_PI;

        // Interface name
        strncpy(ifr.ifr_name, if_name_.c_str(), IFNAMSIZ);

        // Create the device
        if ((err = ioctl(fd_, TUNSETIFF, (void *)&ifr)) < 0) {
            perror("ioctl(TUNSETIFF)");
            close(fd_);
            exit(1);
        }

        // Save the interface name in case it was changed
        if_name_ = ifr.ifr_name;
        std::cout << "Created TAP device: " << if_name_ << std::endl;
    }

    void tapUp() {
        system(("../py/scripts/tap-config.sh " + if_name_).c_str());
    }
};

void printIpAddress(uint32_t ip) {
    uint8_t bytes[4];
    bytes[0] = ip & 0xFF;
    bytes[1] = (ip >> 8) & 0xFF;
    bytes[2] = (ip >> 16) & 0xFF;
    bytes[3] = (ip >> 24) & 0xFF;
    std::cout << (int)bytes[3] << "."
              << (int)bytes[2] << "."
              << (int)bytes[1] << "."
              << (int)bytes[0];
}

int main() {
    TapInterface tap;

    char buffer[1500];

    while (true) {
        int nread = tap.readPacket(buffer, sizeof(buffer));
        if (nread < 0) {
            perror("Reading from TAP interface");
            break;
        }

        std::cout << "Read " << nread << " bytes from "
            << tap.getInterfaceName() << std::endl;

	    if (nread >= sizeof(struct ether_header)) {
            struct ether_header* eth = (struct ether_header*)buffer;
            // Check if the packet is an IP packet
            if (ntohs(eth->ether_type) == ETHERTYPE_IP) {
                struct iphdr* ip = (struct iphdr*)(
                    buffer + sizeof(struct ether_header)
                );

                std::cout << "IP Header:" << std::endl;
                std::cout << "  Src IP: ";
                printIpAddress(ntohl(ip->saddr));
                std::cout << std::endl;

                std::cout << "  Dst IP: ";
                printIpAddress(ntohl(ip->daddr));
                std::cout << std::endl;
            }
        }

        // (Optional) echo it back
        if (tap.writePacket(buffer, nread) < 0) {
            perror("Writing to TAP interface");
            break;
        }
    }

    return 0;
}
